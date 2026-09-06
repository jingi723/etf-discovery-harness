#!/usr/bin/env python3
"""Scan output for recommendation language. Takes files or directories
(recursive) and prints violations as JSON.

    python3 check_forbidden.py <path> [<path> ...]

Exit code 0 when clean, 1 when anything is found.

Point it at run output (_workspace/13_reports/, output/{run_date}/), not at the
repository's own prose: the skill file that documents the banned list naturally
matches every entry in it.

Matching is literal substring, so both language lists are checked on every
file — an English run and a Korean run are caught by the same pass.
"""
import json
import os
import sys

FORBIDDEN = [
    # English
    "buy this", "you should buy", "you should sell", "we recommend",
    "our recommendation", "recommended stock", "recommended pick",
    "buying opportunity", "strong buy", "must-buy", "time to buy",
    "guaranteed return", "guaranteed profit", "risk-free", "can't lose",
    "will go up", "will rise", "poised to rally", "set to surge",
    "don't miss", "act now", "price target", "buy the dip",
    # Korean — kept so Korean-language runs are checked by the same pass
    "사세요", "파세요", "추천합니다", "추천드립니다", "추천 종목",
    "매수 기회", "매수하세요", "매도하세요", "매수 추천", "매도 추천",
    "상승 가능성이 높", "오를 것", "수익이 기대", "수익을 보장",
    "안전합니다", "무조건", "확실한 수익", "놓치지 마세요",
    "지금이 기회", "저점 매수", "목표 주가",
]
EXTS = {".md", ".json", ".html", ".txt"}


def scan_file(path, hits):
    try:
        with open(path, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                for phrase in FORBIDDEN:
                    if phrase in line:
                        hits.append({"file": path, "line": lineno,
                                     "phrase": phrase, "text": line.strip()[:120]})
    except (UnicodeDecodeError, OSError):
        pass


def main():
    hits = []
    for target in sys.argv[1:]:
        if os.path.isdir(target):
            for root, _, files in os.walk(target):
                for name in files:
                    if os.path.splitext(name)[1] in EXTS:
                        scan_file(os.path.join(root, name), hits)
        elif os.path.isfile(target):
            scan_file(target, hits)
    print(json.dumps({"violations": hits, "count": len(hits)},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
