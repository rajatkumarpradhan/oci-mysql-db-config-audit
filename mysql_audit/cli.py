"""Command line entry point: audit an offline MySQL DB system export."""

from __future__ import annotations

import argparse
import sys

from .model import ExportError, load_export
from .rules import exit_code, run_all


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mysql-audit",
        description="Offline config audit for OCI MySQL HeatWave DB systems (synthetic export).",
    )
    parser.add_argument("export", help="path to a JSON export of DB systems")
    args = parser.parse_args(argv)
    try:
        systems = load_export(args.export)
    except ExportError as exc:
        print(f"export error: {exc}", file=sys.stderr)
        return 3
    findings = run_all(systems)
    prod = sum(1 for d in systems if d.is_prod())
    print(f"MySQL DB system audit - {len(systems)} system(s) ({prod} prod-labeled), {len(findings)} finding(s)")
    for f in findings:
        print(f"[{f.severity:6}] {f.rule} db_system={f.target}")
        print(f"        {f.detail}")
    if findings:
        print(f"RESULT: {'HIGH findings present' if exit_code(findings) == 2 else 'medium/low findings only'}")
    else:
        print("RESULT: clean, no findings")
    return exit_code(findings)


if __name__ == "__main__":
    raise SystemExit(main())
