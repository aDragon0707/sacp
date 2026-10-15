"""Select one provider execution before projecting its terminal observations.

An action may retry with a new receipt. The latest accepted execution by provider
timestamp is current; unrelated providers or tied executions are ambiguous.
Within one execution failures dominate success regardless of callback arrival.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _time(item: dict[str, Any]) -> datetime:
    value = datetime.fromisoformat(item["observed_at"])
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def active_observations(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    accepted = [item for item in observations if item.get("provider_event") == "accepted"]
    if not accepted:
        return observations
    if len({item.get("provider") for item in accepted}) != 1:
        return []
    latest_time = max(_time(item) for item in accepted)
    latest = [item for item in accepted if _time(item) == latest_time]
    keys = {(item["provider"], item["receipt_id"]) for item in latest}
    if len(keys) != 1:
        return []
    key = keys.pop()
    return [item for item in observations if (item.get("provider"), item.get("receipt_id")) == key]


def terminal_attested(observations: list[dict[str, Any]]) -> bool:
    active = active_observations(observations)
    accepted = [item for item in active if item.get("provider_event") == "accepted"]
    terminals = [item for item in active if item.get("provider_event") in {"delivered", "healthy", "succeeded", "failed", "rolled_back", "bounced", "counterparty_declined"}]
    for start in accepted:
        metadata = start.get("metadata", {})
        expected_events = ({"healthy", "failed", "rolled_back"} if "revision" in metadata else {"succeeded", "failed"} if "order_id" in metadata else {"delivered", "bounced", "counterparty_declined"})
        for end in terminals:
            if end.get("provider_event") not in expected_events:
                continue
            details = end.get("metadata", {})
            if (start.get("provider"), start.get("receipt_id")) == (end.get("provider"), end.get("receipt_id")) and all(details.get(field) == value for field, value in metadata.items() if field in {"revision", "order_id", "amount", "currency"}):
                return True
    return False
