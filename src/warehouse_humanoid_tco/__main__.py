"""CLI entry point.

See PROJECT_CHARTER.md §8.7 CLI Interface.
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="warehouse-humanoid-tco",
        description="Humanoid robot TCO analyzer for Austrian intralogistics.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract", help="Run Module 1: capability extraction")
    extract_parser.add_argument("--dataset-revision", required=True)

    simulate_parser = subparsers.add_parser("simulate", help="Run Module 2: warehouse simulation")
    simulate_parser.add_argument("--config", required=True)

    tco_parser = subparsers.add_parser("tco", help="Run Module 3: TCO model")
    tco_parser.add_argument("--simulation", required=True)

    export_parser = subparsers.add_parser("export", help="Run Module 4: dashboard export")
    export_parser.add_argument("--target", choices=["tableau", "powerbi", "all"], default="all")

    args = parser.parse_args()

    print(f"Command: {args.command} — implementation pending Module build phase.")
    sys.exit(0)


if __name__ == "__main__":
    main()
