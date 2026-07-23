#!/usr/bin/env python3
"""UI HTML 기계 검사기.

검사: mock 잔여 문자열, 금지 표현, 중복 id, 태그 균형(파싱), 미치환 {{ }},
외부 네트워크 리소스, 번들러 UUID 잔존, (--payload 지정 시) 등급 문자열 존재 대조.

사용: python3 check_html.py <html 파일 또는 디렉토리> [--payload ui_payload.json]
종료 코드: 위반 0건이면 0, 있으면 1.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser

MOCK_RESIDUE = ["네오 미국 AI반도체", "490100", "12,340",
                "예시입니다", "예시 데이터 기준", "DCLogic"]
FORBIDDEN = ["사세요", "파세요", "추천합니다", "추천드립니다", "추천 종목",
             "매수 기회", "매수하세요", "매도하세요", "매수 추천", "매도 추천",
             "상승 가능성이 높", "오를 것", "수익이 기대", "수익을 보장",
             "안전합니다", "무조건", "확실한 수익", "놓치지 마세요",
             "지금이 기회", "저점 매수", "목표 주가"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr"}


class Checker(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = {}
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id":
                self.ids[v] = self.ids.get(v, 0) + 1
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        elif tag in self.stack:
            while self.stack and self.stack[-1] != tag:
                self.errors.append(f"닫히지 않은 태그: <{self.stack.pop()}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"짝 없는 닫는 태그: </{tag}>")


def check_file(path, payload_text):
    issues = []
    text = open(path, encoding="utf-8").read()
    for s in MOCK_RESIDUE:
        if s in text and (payload_text is None or s not in payload_text):
            issues.append({"type": "mock_residue", "value": s})
    for s in FORBIDDEN:
        if s in text:
            issues.append({"type": "forbidden_phrase", "value": s})
    for m in re.finditer(r"\{\{[^}]*\}\}", text):
        issues.append({"type": "unresolved_placeholder", "value": m.group(0)[:60]})
    for m in re.finditer(r'(?:src|href)=["\']https?://', text):
        issues.append({"type": "external_resource", "value": m.group(0)})
    for m in re.finditer(r'(?:src=["\']|url\(["\']?)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}', text):
        issues.append({"type": "bundler_uuid_residue", "value": m.group(0)[:50]})
    c = Checker()
    try:
        c.feed(text)
        c.close()
    except Exception as e:
        issues.append({"type": "parse_error", "value": str(e)[:100]})
    for i, n in c.ids.items():
        if n > 1:
            issues.append({"type": "duplicate_id", "value": f"{i} x{n}"})
    for e in c.errors[:10]:
        issues.append({"type": "tag_balance", "value": e})
    return issues


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    payload_text = None
    if "--payload" in sys.argv:
        payload_text = open(sys.argv[sys.argv.index("--payload") + 1], encoding="utf-8").read()
    results, total = {}, 0
    for target in args:
        files = []
        if os.path.isdir(target):
            files = [os.path.join(target, f) for f in sorted(os.listdir(target))
                     if f.endswith(".html")]
        elif target.endswith(".html"):
            files = [target]
        for f in files:
            issues = check_file(f, payload_text)
            results[os.path.basename(f)] = issues
            total += len(issues)
    print(json.dumps({"total_issues": total, "files": results},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
