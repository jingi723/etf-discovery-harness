#!/usr/bin/env python3
"""Run the checks this repo already owns, without waiting to be asked.

Every tool here ships a self-check and the compliance rules ship a scanner, but
until now both only ran when the model remembered to call them. That is the
weakest possible enforcement: the run that most needs checking is the run where
attention has already slipped.

Wired as a PostToolUse hook on Write and Edit:

  tools/*.py   -> run that file's self-check
  report .md   -> scan for banned recommendation language

A failure exits 2, which returns the message to Claude as feedback rather than
to the user as an error. Everything else exits 0 and stays silent — a hook that
chatters gets switched off.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CHECK_FORBIDDEN = ROOT / ".claude/skills/etf-compliance-rules/scripts/check_forbidden.py"

# Only run output gets scanned. The skill file that documents the banned list
# contains every phrase in it, so pointing the scanner at the repo's own prose
# reports the documentation as a violation.
OUTPUT_HINTS = ("_workspace/", "output/", "/reports/", "final_etf_decision",
                "etf_candidates", "sector_theme_discovery", "data_coverage")


def self_check(path: Path):
    """tools/*.py carry either --self-check or a demo() entry point."""
    src = path.read_text(errors="ignore")
    if '"--self-check"' in src or "'--self-check'" in src:
        cmd = [sys.executable, str(path), "--self-check"]
    elif re.search(r"^def demo\(", src, re.M):
        cmd = [sys.executable, "-c",
               f"import sys; sys.path.insert(0, {str(path.parent)!r}); "
               f"import {path.stem}; {path.stem}.demo()"]
    else:
        return None
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, timeout=120)
    if r.returncode == 0:
        return None
    return (f"{path.name} self-check failed. Fix it before moving on.\n"
            f"{(r.stdout + r.stderr).strip()[-1500:]}")


def forbidden(path: Path):
    if not any(h in str(path).replace("\\", "/") for h in OUTPUT_HINTS):
        return None
    r = subprocess.run([sys.executable, str(CHECK_FORBIDDEN), str(path)],
                       capture_output=True, text=True, cwd=ROOT, timeout=60)
    if r.returncode == 0:
        return None
    return (f"{path.name} contains recommendation language. The harness never "
            f"tells anyone to buy or sell — rewrite it as one of the four "
            f"verdict states.\n{r.stdout.strip()[:1500]}")


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0                                   # malformed input is not our problem
    raw = (event.get("tool_input") or {}).get("file_path")
    if not raw:
        return 0
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        return 0

    try:
        rel = path.relative_to(ROOT)
    except ValueError:
        return 0                                   # edits outside the repo
    problem = None
    if rel.parts[:1] == ("tools",) and path.suffix == ".py":
        problem = self_check(path)
    elif path.suffix in (".md", ".json"):
        problem = forbidden(path)

    if problem:
        print(problem, file=sys.stderr)
        return 2                                   # 2 sends this back to Claude
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:                         # never block work on a hook bug
        print(f"hook error (ignored): {e}", file=sys.stderr)
        sys.exit(0)
