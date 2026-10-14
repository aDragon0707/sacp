from __future__ import annotations

import random
import unittest
from datetime import datetime, timedelta, timezone

from sacp_verify import Claim, EventStore, MockProvider, Verifier


BASE = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
PROVIDER_EVENTS = ("accepted", "delivered", "bounced", "unauthorized", "bad_request")


class StateMachinePropertyTests(unittest.TestCase):
    def _new_action(self, action_id: str) -> tuple[EventStore, Verifier, MockProvider]:
        store = EventStore()
        store.append_claim(
            Claim(
                action_id=action_id,
                claim_type="notification_sent",
                text="notification_sent",
                thread_id="thread-1",
                run_id="run-1",
                checkpoint_id="cp-1",
                created_at=BASE,
            )
        )
        return store, Verifier(store), MockProvider(store)

    def test_random_provider_sequences_preserve_conservative_boundaries(self) -> None:
        generator = random.Random(20260831)
        for index in range(100):
            store, verifier, provider = self._new_action(f"property-{index}")
            try:
                events = [generator.choice(PROVIDER_EVENTS) for _ in range(generator.randint(1, 8))]
                for offset, event in enumerate(events):
                    provider.emit(
                        f"property-{index}",
                        event,
                        f"provider-{index}-{offset}",
                        BASE + timedelta(seconds=offset),
                    )
                receipt = verifier.project_receipt(f"property-{index}", BASE + timedelta(minutes=1))
                if "bounced" in events:
                    self.assertEqual(receipt.status, "bounced", events)
                elif any(event in {"unauthorized", "bad_request"} for event in events):
                    self.assertEqual(receipt.status, "provider_error", events)
                elif "delivered" not in events:
                    self.assertNotEqual(receipt.status, "provider_reported_delivered", events)
            finally:
                store.close()

    def test_projection_is_idempotent_for_same_event_history(self) -> None:
        store, verifier, provider = self._new_action("property-idempotent")
        try:
            provider.emit("property-idempotent", "accepted", "provider-idempotent", BASE)
            first = verifier.project_receipt("property-idempotent", BASE)
            second = verifier.project_receipt("property-idempotent", BASE)
            self.assertEqual(first.as_dict(), second.as_dict())
        finally:
            store.close()

    def test_duplicate_events_do_not_shrink_or_mutate_history(self) -> None:
        store, verifier, provider = self._new_action("property-history")
        try:
            before = store.event_count("property-history")
            first = provider.emit("property-history", "accepted", "provider-history", BASE)
            after_first = store.event_count("property-history")
            second = provider.emit("property-history", "accepted", "provider-history", BASE)
            after_duplicate = store.event_count("property-history")
            self.assertEqual(first, second)
            self.assertGreater(after_first, before)
            self.assertEqual(after_duplicate, after_first)
            self.assertEqual(verifier.project_receipt("property-history", BASE).status, "transport_accepted")
        finally:
            store.close()


if __name__ == "__main__":
    unittest.main()
