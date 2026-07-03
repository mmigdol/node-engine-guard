from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

from . import __version__
from .check import CheckResult, check_node_engine


def parse_hook_cwd() -> Path | None:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except Exception:
        payload = {}

    cwd = payload.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd)

    roots = payload.get("workspace_roots")
    if isinstance(roots, list) and roots and isinstance(roots[0], str):
        return Path(roots[0])

    return None


def codex_hook_output(result: CheckResult) -> str:
    if result.ok:
        return ""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": f"WARNING: {result.message}",
            }
        }
    )


def install_snippet() -> str:
    installed = shutil.which("node-engine-guard")
    if installed:
        command = f"{Path(installed).expanduser()} --codex-hook"
    else:
        executable = Path(sys.argv[0]).expanduser()
        command = f"/usr/bin/python3 {executable} --codex-hook"
    return f"""Add this to ~/.codex/config.toml:

[hooks]
SessionStart = [
  {{ matcher = "startup|resume|clear|compact", hooks = [
    {{ type = "command", command = "{command}", timeout = 5 }}
  ] }}
]
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="node-engine-guard",
        description="Check that non-interactive node satisfies package.json engines.node.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--cwd", type=Path, default=None, help="Project directory to check.")
    parser.add_argument("--codex-hook", action="store_true", help="Read Codex hook JSON from stdin and emit Codex hook JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when node does not satisfy engines.node.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument("--print-codex-install", action="store_true", help="Print a manual Codex hook install snippet.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.print_codex_install:
        print(install_snippet())
        return 0

    cwd = args.cwd
    if args.codex_hook:
        cwd = parse_hook_cwd()
    cwd = cwd or Path(os.getcwd())

    result = check_node_engine(cwd)

    if args.codex_hook:
        output = codex_hook_output(result)
        if output:
            print(output)
        return 0

    if args.json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "message": result.message,
                    "package_json": str(result.package_json) if result.package_json else None,
                    "engine": result.engine,
                    "node_path": result.node_path,
                    "node_version": str(result.node_version) if result.node_version else None,
                },
                indent=2,
            )
        )
    else:
        stream = sys.stdout if result.ok else sys.stderr
        print(result.message, file=stream)

    return 1 if args.strict and not result.ok else 0
