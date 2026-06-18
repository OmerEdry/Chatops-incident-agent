# scripts/smoke_test.py
#
# Prerequisites:
#   - Virtual environment active with `pip install -e ".[dev]"`
#   - GEMINI_API_KEY set in your .env or shell environment
#   - Run from the project root: python scripts/smoke_test.py

import asyncio
import logging
import os
import sys

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services import route_incident

logging.basicConfig(level=logging.WARNING)  # suppress INFO noise during smoke test

_DIVIDER = "-" * 60

_TEST_CASES = [
    {
        "label": "Case 1 — Critical (expects P1/P2, full pipeline)",
        "payload": (
            "CRITICAL: kubernetes pod api-server-7d9f crashed with OOMKilled. "
            "50 restarts in the last 5 minutes. Memory limit: 512Mi. "
            "Heap dump shows unbounded cache growth in request-handler pool. "
            "Production traffic impacted — 503s reported by monitoring."
        ),
    },
    {
        "label": "Case 2 — Informational (expects P3/P4, triage only)",
        "payload": (
            "INFO: scheduled nightly VACUUM ANALYZE completed on incidents table. "
            "Duration: 4.2s. Rows removed: 0. Dead tuples before: 12, after: 0. "
            "No anomalies detected."
        ),
    },
]


async def main() -> None:
    print(f"\n{'=' * 60}")
    print("  Gemini Routing Pipeline — Smoke Test")
    print(f"{'=' * 60}\n")

    for case in _TEST_CASES:
        print(_DIVIDER)
        print(f"  {case['label']}")
        print(_DIVIDER)
        try:
            result = await route_incident(case["payload"])
            print(result.model_dump_json(indent=2))
        except Exception as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
        print()

    print("Smoke test complete.")


if __name__ == "__main__":
    asyncio.run(main())
