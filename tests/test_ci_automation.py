from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import yaml
from unittest.mock import patch

from scripts.build_ci_receipt import PR_REQUIRED_JOBS, build_receipt
from scripts.check_pr_gate import REQUIRED_JOBS, evaluate_gate
from scripts.check_pr_policy import evaluate_policy
from scripts.extract_ci_refs import extract_refs
from validator import validate_document

BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40
MERGE_SHA = "3" * 40
FINGERPRINT = "sha256:" + "a" * 64


def evidence(job: str, *, status: str = "passed", skipped: int = 0, head_sha: str = HEAD_SHA) -> dict:
    return {
        "schema": "sacp-ci-evidence/1",
        "job": job,
        "suite": "pr-policy" if job == "pr-policy" else "core",
        "status": status,
        "exit_code": 0 if status == "passed" else 1,
        "command": f"python scripts/run_tests.py --job {job}",
        "source_fingerprint": FINGERPRINT,
        "base_sha": BASE_SHA,
        "head_sha": head_sha,
        "merge_sha": MERGE_SHA,
        "environment": {
            "platform": "Linux-6.0",
            "python": "3.12.7",
            "runner_os": "Linux",
        },
        "generated_at": "2026-10-14T12:00:00+00:00",
        "results": {
            "total": 1,
            "failures": 0 if status == "passed" else 1,
            "errors": 0,
            "skipped": skipped,
            "successful": status == "passed",
            "change_classes": ["automation"] if job == "pr-policy" else [],
        },
    }


def workflow_event(
    *, head_sha: str = HEAD_SHA, conclusion: str = "success", fork: bool = False
) -> dict:
    return {
        "workflow_run": {
            "id": 1234,
            "head_sha": MERGE_SHA,
            "conclusion": conclusion,
            "updated_at": "2026-10-14T12:00:00+00:00",
            "pull_requests": [
                {
                    "number": 42,
                    "base": {"sha": BASE_SHA},
                    "head": {
                        "sha": head_sha,
                        "repo": {
                            "full_name": "contributor/sacp" if fork else "aDragon0707/sacp"
                        },
                    },
                }
            ],
        }
    }


class PrPolicyTests(unittest.TestCase):
    def test_readme_languages_must_change_together(self) -> None:
        result = evaluate_policy(["README.md"], {})
        self.assertFalse(result["passed"])
        self.assertIn("README.md and README.zh-CN.md", result["errors"][0])

    def test_workflow_actions_must_be_pinned_and_permissions_read_only(self) -> None:
        result = evaluate_policy(
            [".github/workflows/unsafe.yml"],
            {
                ".github/workflows/unsafe.yml": """
pull_request_target:
permissions:
  contents: write
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
"""
            },
        )
        self.assertFalse(result["passed"])
        self.assertGreaterEqual(len(result["errors"]), 3)

    def test_protocol_change_without_companions_is_a_review_warning(self) -> None:
        result = evaluate_policy(["SPEC.md"], {})
        self.assertTrue(result["passed"])
        self.assertIn("dirty case", result["warnings"][0])
        self.assertEqual(result["change_classes"], ["docs", "protocol"])

    def test_workflow_changes_are_automation_critical(self) -> None:
        pinned = "11d5960a326750d5838078e36cf38b85af677262"
        result = evaluate_policy(
            [".github/workflows/pr-ci.yml"],
            {".github/workflows/pr-ci.yml": f"jobs:\n  test:\n    steps:\n      - uses: actions/checkout@{pinned}\n"},
        )
        self.assertTrue(result["passed"])
        self.assertEqual(result["risk"], "automation-critical")


class PrGateTests(unittest.TestCase):
    def test_all_required_jobs_must_succeed(self) -> None:
        needs = {job: {"result": "success"} for job in REQUIRED_JOBS}
        self.assertTrue(evaluate_gate(needs)["passed"])

    def test_skipped_or_missing_jobs_fail(self) -> None:
        needs = {job: {"result": "success"} for job in REQUIRED_JOBS}
        needs["harness"] = {"result": "skipped"}
        del needs["core-windows-312"]
        result = evaluate_gate(needs)
        self.assertFalse(result["passed"])
        self.assertEqual(result["non_success"], {"harness": "skipped"})
        self.assertEqual(result["missing"], ["core-windows-312"])


class ReceiptBuilderTests(unittest.TestCase):
    def all_evidence(self) -> dict[str, dict]:
        return {job: evidence(job) for job in PR_REQUIRED_JOBS}

    def test_success_receipt_is_preflight_not_human_approval(self) -> None:
        receipt = build_receipt(
            event=workflow_event(),
            mode="pr",
            evidence=self.all_evidence(),
            required_jobs=PR_REQUIRED_JOBS,
        )
        self.assertEqual(receipt["method"], "COMPLETE")
        self.assertEqual(receipt["status_code"], 200)
        self.assertEqual(receipt["verification"]["status"], "passed")
        self.assertEqual(receipt["next_owner"], "maintainer")
        self.assertTrue(receipt["human_decision_required"])
        self.assertIn("not approval", receipt["residual_risk"])
        with TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.yaml"
            path.write_text(
                yaml.safe_dump(receipt, sort_keys=False), encoding="utf-8"
            )
            validation = validate_document(path)
        self.assertTrue(validation["valid"])
        self.assertEqual(validation["warnings"], [])

    def test_failed_or_skipped_check_blocks_receipt(self) -> None:
        items = self.all_evidence()
        items["harness"] = evidence("harness", status="failed")
        items["core-windows-312"] = evidence("core-windows-312", skipped=1)
        receipt = build_receipt(
            event=workflow_event(conclusion="failure"),
            mode="pr",
            evidence=items,
            required_jobs=PR_REQUIRED_JOBS,
        )
        self.assertEqual(receipt["method"], "BLOCK")
        self.assertEqual(receipt["status_code"], 412)
        self.assertEqual(receipt["verification"]["status"], "blocked")

    def test_new_head_sha_invalidates_old_evidence(self) -> None:
        receipt = build_receipt(
            event=workflow_event(head_sha="4" * 40),
            mode="pr",
            evidence=self.all_evidence(),
            required_jobs=PR_REQUIRED_JOBS,
        )
        self.assertEqual(receipt["method"], "FAIL")
        self.assertEqual(receipt["status_code"], 500)
        self.assertTrue(
            any("head SHA does not match" in item for item in receipt["extensions"]["sacp.evidence_errors"])
        )

    def test_missing_evidence_blocks_receipt(self) -> None:
        items = self.all_evidence()
        del items["harness"]
        receipt = build_receipt(
            event=workflow_event(),
            mode="pr",
            evidence=items,
            required_jobs=PR_REQUIRED_JOBS,
        )
        self.assertEqual(receipt["method"], "BLOCK")
        self.assertIn("missing evidence: harness", receipt["residual_risk"])

    def test_fork_pr_uses_sha_bound_evidence_without_secrets(self) -> None:
        receipt = build_receipt(
            event=workflow_event(fork=True),
            mode="pr",
            evidence=self.all_evidence(),
            required_jobs=PR_REQUIRED_JOBS,
        )
        self.assertEqual(receipt["method"], "COMPLETE")
        self.assertEqual(receipt["extensions"]["github.head_sha"], HEAD_SHA)

    def test_main_receipt_uses_github_run_id(self) -> None:
        items = {
            job: evidence(job, head_sha=HEAD_SHA)
            for job in PR_REQUIRED_JOBS
            if job != "pr-policy"
        }
        for item in items.values():
            item["base_sha"] = BASE_SHA
            item["merge_sha"] = HEAD_SHA
        event = {
            "before": BASE_SHA,
            "after": HEAD_SHA,
            "head_commit": {"id": HEAD_SHA, "timestamp": "2026-10-14T12:00:00+00:00"},
        }
        with patch.dict(os.environ, {"GITHUB_RUN_ID": "987654"}):
            receipt = build_receipt(
                event=event,
                mode="main",
                evidence=items,
                required_jobs=tuple(items),
            )
        self.assertEqual(receipt["attempt_id"], "github-run-987654")
        self.assertEqual(receipt["status_code"], 200)


class EvidenceRefTests(unittest.TestCase):
    def test_extracts_one_merge_sha_bound_to_current_event(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "core.json"
            path.write_text(json.dumps(evidence("core")), encoding="utf-8")
            refs = extract_refs(workflow_event(), Path(directory))
        self.assertEqual(refs["base_sha"], BASE_SHA)
        self.assertEqual(refs["head_sha"], HEAD_SHA)
        self.assertEqual(refs["merge_sha"], MERGE_SHA)

    def test_rejects_evidence_from_an_old_head(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "core.json"
            path.write_text(json.dumps(evidence("core", head_sha="4" * 40)), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exactly one tested merge SHA"):
                extract_refs(workflow_event(), Path(directory))


class WorkflowContractTests(unittest.TestCase):
    def test_repository_workflows_obey_static_security_policy(self) -> None:
        workflow_dir = Path(__file__).resolve().parent.parent / ".github" / "workflows"
        workflows = {
            str(path.relative_to(workflow_dir.parent.parent)).replace("\\", "/"): path.read_text(encoding="utf-8")
            for path in workflow_dir.glob("*.yml")
        }
        result = evaluate_policy(list(workflows), workflows)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["risk"], "automation-critical")

    def test_workflow_yaml_is_parseable(self) -> None:
        workflow_dir = Path(__file__).resolve().parent.parent / ".github" / "workflows"
        for path in workflow_dir.glob("*.yml"):
            with self.subTest(path=path.name):
                self.assertIsInstance(yaml.safe_load(path.read_text(encoding="utf-8")), dict)

    def test_pr_ci_is_fork_safe_and_does_not_reference_secrets(self) -> None:
        workflow = (
            Path(__file__).resolve().parent.parent
            / ".github"
            / "workflows"
            / "pr-ci.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("secrets.", workflow)
        self.assertNotIn("pull_request_target", workflow)


if __name__ == "__main__":
    unittest.main()
