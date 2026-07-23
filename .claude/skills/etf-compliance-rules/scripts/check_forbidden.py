#!/usr/bin/env python3
"""금지 표현 검사기. 파일 또는 디렉토리(재귀)를 받아 위반 목록을 JSON으로 출력한다.

사용: python3 check_forbidden.py <path> [<path> ...]
종료 코드: 위반 0건이면 0, 있으면 1.
"""
import json
import os
import sys

FORBIDDEN = [
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
