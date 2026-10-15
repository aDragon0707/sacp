"""No model calls: Pi contract fixtures plus separate acceptance subprocesses."""
from __future__ import annotations

import contextlib
import copy
import io
import json
import tempfile
import unittest
import os
import sys
from pathlib import Path

from sacp_eval.__main__ import main
from sacp_eval.acceptance import snapshot_digest, verify_source
from sacp_eval.capture import capture_pi_json, pi_json_command
from sacp_eval.evaluate import evaluate_trace as raw_evaluate_trace
from sacp_eval.pi import digest, parse_trace


FIXTURES = Path(__file__).resolve().parent.parent / "examples" / "pi_eval"
RAW = (FIXTURES / "scripted-events.jsonl").read_bytes()


def encode(events):
    return b"".join(json.dumps(event, ensure_ascii=False).encode("utf-8") + b"\n" for event in events)


def events():
    return [json.loads(line) for line in RAW.split(b"\n") if line]


def evaluate_trace(raw, acceptance, **kwargs):
    kwargs.setdefault("delivery_digest", acceptance["snapshot_digest"])
    return raw_evaluate_trace(raw, acceptance, **kwargs)


class PiTraceTests(unittest.TestCase):
    def test_valid_lifecycle_does_not_claim_task_success(self):
        trace = parse_trace(RAW)
        self.assertEqual(trace["status"], "complete")
        self.assertEqual(trace["final_text"], "All tests passed.")
        self.assertEqual(trace["tool_calls"], 1)
        self.assertNotIn("allowed", trace)

    def test_unicode_separators_are_not_record_boundaries(self):
        for text in ("完成了", "a\u2028b", "c\u2029d", "line\nline", "🚀", 'quote"\\'):
            with self.subTest(text=text):
                stream = events()
                stream[4]["message"]["content"][0]["text"] = text
                parsed = parse_trace(encode(stream))
                self.assertEqual(parsed["status"], "complete")
                self.assertEqual(parsed["final_text"], text)

    def test_crlf_and_chunk_content_preserve_final_text(self):
        self.assertEqual(parse_trace(RAW.replace(b"\n", b"\r\n"))["final_text"], "All tests passed.")

    def test_truncation_never_reports_complete(self):
        for length in range(0, len(RAW), max(1, len(RAW) // 30)):
            self.assertEqual(parse_trace(RAW[:length])["status"], "incomplete")
        self.assertEqual(parse_trace(RAW[:-1])["status"], "incomplete")

    def test_low_level_end_and_tool_success_are_not_settled(self):
        parsed = parse_trace(encode(events()[:-1]))
        self.assertIn("agent_not_settled", parsed["errors"])

    def test_duplicate_or_wrong_tool_identity_is_rejected(self):
        for index, key, value in ((3, "toolCallId", "another"), (3, "toolName", "write"), (3, "isError", 0)):
            stream = events()
            stream[index][key] = value
            self.assertEqual(parse_trace(encode(stream))["status"], "incomplete")
        stream = events()
        stream.insert(4, stream[3])
        self.assertEqual(parse_trace(encode(stream))["status"], "incomplete")

    def test_failed_tool_can_be_recovered_without_forging_test_proof(self):
        stream = events()
        stream[3]["isError"] = True
        trace = parse_trace(encode(stream))
        self.assertEqual(trace["status"], "complete")
        self.assertEqual(trace["tool_errors"], ["tool-1"])

    def test_invalid_roots_keys_numbers_utf8_and_types_fail_closed(self):
        for invalid in (b"[]", b'{"type":"x","type":"y"}', b'{"type":NaN}', b"\xff", b'{"type":[]}'):
            self.assertEqual(parse_trace(invalid + b"\n")["status"], "incomplete")

    def test_aborted_or_error_final_cannot_be_complete(self):
        for stop in ("error", "aborted", "length", "toolUse"):
            stream = events()
            stream[4]["message"]["stopReason"] = stop
            self.assertEqual(parse_trace(encode(stream))["status"], "incomplete")
        stream = events()
        stream[-1]["aborted"] = True
        self.assertIn("agent_aborted", parse_trace(encode(stream))["errors"])

    def test_activity_after_settled_and_unknown_events_are_rejected(self):
        self.assertEqual(parse_trace(RAW + b'{"type":"agent_start"}\n')["status"], "incomplete")
        stream = events()
        stream.insert(2, {"type": "new_version_event"})
        self.assertEqual(parse_trace(encode(stream))["status"], "incomplete")

    def test_retry_needs_its_own_final_message(self):
        stream = events()
        stream.insert(-1, {"type": "agent_start"})
        stream.insert(-1, {"type": "agent_end"})
        self.assertEqual(parse_trace(encode(stream))["status"], "incomplete")

    def test_tool_end_after_agent_end_cannot_complete(self):
        stream = events()
        tool_end = stream.pop(3)
        stream.insert(-1, tool_end)
        self.assertIn("agent_ended_with_active_tools", parse_trace(encode(stream))["errors"])

    def test_retry_promise_cannot_be_closed_without_retry(self):
        stream = events()
        stream[-2]["willRetry"] = True
        self.assertIn("settled_with_retry_pending", parse_trace(encode(stream))["errors"])

    def test_snapshot_digest_is_order_independent_and_path_sensitive(self):
        first = {"a.py": b"ab", "b.py": b"c"}
        self.assertEqual(snapshot_digest(first), snapshot_digest(dict(reversed(list(first.items())))))
        self.assertNotEqual(snapshot_digest(first), snapshot_digest({"a.py": b"a", "b.py": b"bc"}))
        self.assertNotEqual(snapshot_digest(first), snapshot_digest({"other.py": b"ab", "b.py": b"c"}))


class PiAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.good = verify_source(FIXTURES / "task.json", FIXTURES / "candidate_good", allow_local_execution=True, trace_digest=digest(RAW))
        cls.bad = verify_source(FIXTURES / "task.json", FIXTURES / "candidate_bad", allow_local_execution=True, trace_digest=digest(RAW))

    def test_independent_acceptance_distinguishes_known_good_and_bad(self):
        self.assertEqual(self.good["status"], "passed")
        self.assertEqual(self.bad["status"], "failed")
        self.assertEqual(self.good["results"]["total"], 2)
        self.assertNotEqual(self.good["snapshot_digest"], self.bad["snapshot_digest"])

    def test_tool_ok_and_done_text_cannot_override_bad_delivery(self):
        result = evaluate_trace(RAW, self.bad, process_exit_code=0, claim_text="All tests passed.")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["derived_receipt"]["overall_status"], "unverified")

    def test_supported_selected_claim_gets_host_completed_not_release_approval(self):
        result = evaluate_trace(RAW, self.good, process_exit_code=0, claim_text="All tests passed.")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["derived_receipt"]["overall_status"], "host_completed")
        self.assertEqual(result["derived_receipt"]["authority_status"], "not_required")
        self.assertTrue(result["human_decision_required"])

    def test_unselected_or_missing_claim_stays_unverified(self):
        for selection in (None, "Something not in the final message"):
            result = evaluate_trace(RAW, self.good, process_exit_code=0, claim_text=selection)
            self.assertFalse(result["allowed"])
            self.assertEqual(result["claim_type"], "unclassified")

    def test_wrong_trace_or_bad_exit_blocks_fresh_successful_acceptance(self):
        altered = RAW.replace(b"All tests passed.", b"Everything is done.")
        result = evaluate_trace(altered, self.good, process_exit_code=0, claim_text="Everything is done.")
        self.assertIn("acceptance_trace_mismatch", result["errors"])
        for code in (1, None, False):
            self.assertFalse(evaluate_trace(RAW, self.good, process_exit_code=code, claim_text="All tests passed.")["allowed"])

    def test_previous_success_does_not_verify_another_delivery(self):
        result = evaluate_trace(RAW, self.good, process_exit_code=0, delivery_digest=self.bad["snapshot_digest"], claim_text="All tests passed.")
        self.assertIn("acceptance_delivery_mismatch", result["errors"])
        self.assertFalse(result["allowed"])

    def test_missing_zero_skipped_or_inconsistent_results_do_not_pass(self):
        for changes in ({"total": 0}, {"skipped": 1}, {"errors": 1}, {"failures": 1}, {"total": True}):
            altered = copy.deepcopy(self.good)
            altered["results"].update(changes)
            self.assertFalse(evaluate_trace(RAW, altered, process_exit_code=0, claim_text="All tests passed.")["allowed"])

    def test_local_code_execution_requires_opt_in(self):
        with self.assertRaisesRegex(ValueError, "explicit opt-in"):
            verify_source(FIXTURES / "task.json", FIXTURES / "candidate_good")

    def test_contract_must_live_outside_candidate(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            verify_source(FIXTURES / "task.json", FIXTURES, allow_local_execution=True)

    def test_missing_required_tests_is_indeterminate_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "task.json"
            (contract.parent / "oracle").mkdir()
            (contract.parent / "oracle" / "test_acceptance.py").write_text("import unittest\n", encoding="utf-8")
            contract.write_bytes((FIXTURES / "task.json").read_bytes())
            result = verify_source(contract, FIXTURES / "candidate_good", allow_local_execution=True)
            self.assertEqual(result["status"], "indeterminate")

    def test_paths_cannot_escape_the_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "task.json"
            for invalid in ("../calculator.py", "/calculator.py", "C:/calculator.py", "calculator.py/../calculator.py"):
                spec = json.loads((FIXTURES / "task.json").read_bytes())
                spec["source_files"] = [invalid]
                contract.write_text(json.dumps(spec), encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_source(contract, FIXTURES / "candidate_good", allow_local_execution=True)

    def test_actual_skipped_test_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "task.json"
            tests = contract.parent / "oracle"
            tests.mkdir()
            text = (FIXTURES / "oracle" / "test_acceptance.py").read_text(encoding="utf-8")
            text = text.replace("    def test_positive", "    @unittest.skip('deliberate acceptance control')\n    def test_positive")
            (tests / "test_acceptance.py").write_text(text, encoding="utf-8")
            contract.write_bytes((FIXTURES / "task.json").read_bytes())
            result = verify_source(contract, FIXTURES / "candidate_good", allow_local_execution=True)
            self.assertNotEqual(result["status"], "passed")
            self.assertEqual(result["results"]["skipped"], 1)

    def test_acceptance_timeout_is_indeterminate(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "task.json"
            (contract.parent / "oracle").mkdir()
            (contract.parent / "oracle" / "test_acceptance.py").write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
            contract.write_bytes((FIXTURES / "task.json").read_bytes())
            result = verify_source(contract, FIXTURES / "candidate_good", allow_local_execution=True, timeout=0.1)
            self.assertEqual(result["status"], "indeterminate")
            self.assertTrue(result["timed_out"])

    def test_expected_failure_is_not_successful_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            contract = Path(directory) / "task.json"
            tests = contract.parent / "oracle"
            tests.mkdir()
            text = (FIXTURES / "oracle" / "test_acceptance.py").read_text(encoding="utf-8")
            text = text.replace("    def test_positive", "    @unittest.expectedFailure\n    def test_positive")
            (tests / "test_acceptance.py").write_text(text, encoding="utf-8")
            contract.write_bytes((FIXTURES / "task.json").read_bytes())
            result = verify_source(contract, FIXTURES / "candidate_bad", allow_local_execution=True)
            self.assertEqual(result["results"]["expected_failures"], 1)
            self.assertFalse(evaluate_trace(RAW, result, process_exit_code=0, claim_text="All tests passed.")["allowed"])

    def test_verify_cli_produces_report_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            output = Path(directory) / "result.json"
            args = ["verify-local", "--trace", str(FIXTURES / "scripted-events.jsonl"), "--process-exit-code", "0", "--contract", str(FIXTURES / "task.json"), "--source", str(FIXTURES / "candidate_good"), "--delivery-digest", self.good["snapshot_digest"], "--claim-text", "All tests passed.", "--allow-local-execution", "--output", str(output)]
            self.assertEqual(main(args), 0)
            self.assertTrue(json.loads(output.read_text(encoding="utf-8"))["allowed"])
            self.assertEqual(main(args), 2)

    def test_inspect_cli_does_not_run_code_or_claim_task_success(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["inspect", "--trace", str(FIXTURES / "scripted-events.jsonl"), "--process-exit-code", "0"])
        self.assertEqual(code, 0)
        self.assertNotIn("allowed", json.loads(output.getvalue()))


class PiCaptureTests(unittest.TestCase):
    def test_capture_defaults_to_no_model_permission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, "disabled"):
                capture_pi_json(["never-execute"], launcher=["never-execute"], cwd=root, output_dir=root / "out", env={})
            self.assertFalse((root / "out").exists())

    def test_explicit_provider_model_and_prompt_cannot_be_options(self):
        command = pi_json_command("node", "cli.js", provider="example", model="exact-model", prompt="--extension hostile.js")
        self.assertEqual(command[-2:], ["--", "--extension hostile.js"])
        self.assertIn("--no-extensions", command)
        self.assertIn("--no-approve", command)
        self.assertIn("--offline", command)

    def test_scripted_process_capture_is_not_a_real_pi_benchmark(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            # Python is a launcher test double here, not a security boundary or Pi.
            code = "import sys;sys.stdout.buffer.write(bytes.fromhex(sys.argv[1]))"
            report = capture_pi_json(["-c", code, RAW.hex()], launcher=[sys.executable], cwd=root, output_dir=root / "out", env={key: value for key, value in os.environ.items() if key.upper() in {"SYSTEMROOT", "PATH", "WINDIR"}}, permit_model_calls=True)
            self.assertTrue(report["trace_complete"])
            self.assertEqual(report["events_digest"], digest(RAW))
            self.assertEqual((root / "out" / "events.jsonl").read_bytes(), RAW)

    def test_capture_times_out_instead_of_waiting_forever(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = capture_pi_json(["-c", "import time;time.sleep(30)"], launcher=[sys.executable], cwd=root, output_dir=root / "out", env=dict(os.environ), timeout=0.1, permit_model_calls=True)
            self.assertEqual(report["status"], "timeout")
            self.assertFalse(report["trace_complete"])

    def test_oversized_or_failed_process_cannot_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = capture_pi_json(["-c", "print('x'*10000)"], launcher=[sys.executable], cwd=root, output_dir=root / "out", env=dict(os.environ), max_output_bytes=100, permit_model_calls=True)
            self.assertEqual(report["status"], "output_limit")
            self.assertFalse(report["trace_complete"])
            report = capture_pi_json(["-c", "import sys;sys.exit(3)"], launcher=[sys.executable], cwd=root, output_dir=root / "failed", env=dict(os.environ), permit_model_calls=True)
            self.assertEqual(report["process_exit_code"], 3)
            self.assertFalse(report["trace_complete"])


if __name__ == "__main__":
    unittest.main()
