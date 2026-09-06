#!/usr/bin/env python3
"""Mechanical checks on rendered UI HTML.

Checks: banned phrases, duplicate ids, tag balance
(by parsing), unresolved {{ }}, external network resources, bundler UUID
residue. With --payload, also checks that the input is valid JSON.
It does not prove that HTML values match their source; compare those separately.

    python3 check_html.py <html file or directory> [--payload ui_payload.json]

Exit code 0 when clean, 1 when anything is found.
"""
import argparse
import json
import os
import re
import sys
from html.parser import HTMLParser

# kept in sync with etf-compliance-rules/scripts/check_forbidden.py
FORBIDDEN = ["buy this", "you should buy", "you should sell", "we recommend",
             "our recommendation", "recommended stock", "recommended pick",
             "buying opportunity", "strong buy", "must-buy", "time to buy",
             "guaranteed return", "guaranteed profit", "risk-free",
             "can't lose", "will go up", "will rise", "poised to rally",
             "set to surge", "don't miss", "act now", "price target",
             "buy the dip",
             "사세요", "파세요", "추천합니다", "추천드립니다", "추천 종목",
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
                self.errors.append(f"unclosed tag: <{self.stack.pop()}>")
            if self.stack:
                self.stack.pop()
        else:
            self.errors.append(f"unmatched closing tag: </{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)


def check_file(path, payload_text):
    issues = []
    text = open(path, encoding="utf-8").read()
    for s in FORBIDDEN:
        if s.casefold() in text.casefold():
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
        c.errors.extend(f"unclosed tag: <{tag}>" for tag in reversed(c.stack))
    except Exception as e:
        issues.append({"type": "parse_error", "value": str(e)[:100]})
    for i, n in c.ids.items():
        if n > 1:
            issues.append({"type": "duplicate_id", "value": f"{i} x{n}"})
    for e in c.errors[:10]:
        issues.append({"type": "tag_balance", "value": e})
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+")
    parser.add_argument("--payload", help="also validate this payload's JSON syntax")
    args = parser.parse_args()
    payload_text = None
    if args.payload:
        try:
            with open(args.payload, encoding="utf-8") as f:
                payload_text = f.read()
            json.loads(payload_text)
        except (OSError, ValueError) as error:
            parser.error(f"invalid payload: {error}")
    results, total = {}, 0
    for target in args.targets:
        files = []
        if os.path.isdir(target):
            files = [os.path.join(target, f) for f in sorted(os.listdir(target))
                     if f.endswith(".html")]
        elif os.path.isfile(target) and target.endswith(".html"):
            files = [target]
        if not files:
            parser.error(f"no HTML files found at {target}")
        for f in files:
            try:
                issues = check_file(f, payload_text)
            except OSError as error:
                parser.error(str(error))
            results[f] = issues
            total += len(issues)
    print(json.dumps({"total_issues": total, "files": results},
                     ensure_ascii=False, indent=2))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
