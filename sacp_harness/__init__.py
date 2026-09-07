"""Reproducible evidence harness for SACP.

Runs the reference engine's breaker cases and emits a fixed report:
for each case, what a trace/observability tool records (the false claim,
verbatim) versus what the SACP engine projects (the conservative veto).
"""

from .run import build_report

__all__ = ["build_report"]