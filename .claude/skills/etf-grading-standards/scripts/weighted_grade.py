#!/usr/bin/env python3
"""Weighted-average grade calculator.

Input (stdin or a file argument):
    {"items": [{"name": str, "weight": float, "grade": "B+"|null}]}
Output:
    {"final_grade", "numeric", "coverage_pct", "contributions"}

Items with a null or unknown grade are excluded from coverage; the average is
normalised over the weights of the graded items only. Acting on coverage (the
60% gate) is the caller's job.
"""
import json
import sys

GRADE_NUM = {"A+": 10, "A0": 9, "A-": 8, "B+": 7, "B0": 6, "B-": 5,
             "C+": 4, "C0": 3, "C-": 2, "D": 1}
NUM_GRADE = {v: k for k, v in GRADE_NUM.items()}


def main():
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    items = json.loads(raw)["items"]
    graded = [i for i in items if i.get("grade") in GRADE_NUM]
    total_w = sum(float(i["weight"]) for i in items)
    graded_w = sum(float(i["weight"]) for i in graded)
    coverage = round(100 * graded_w / total_w, 1) if total_w else 0.0

    if graded_w == 0:
        print(json.dumps({"final_grade": None, "numeric": None,
                          "coverage_pct": coverage,
                          "note": "cannot grade — no item carries a grade"},
                         ensure_ascii=False, indent=2))
        return

    numeric = sum(GRADE_NUM[i["grade"]] * float(i["weight"]) for i in graded) / graded_w
    final = NUM_GRADE[min(10, max(1, round(numeric)))]
    contributions = []
    for i in items:
        c = None
        if i.get("grade") in GRADE_NUM:
            c = round(GRADE_NUM[i["grade"]] * float(i["weight"]) / graded_w, 2)
        contributions.append({"name": i["name"], "weight": float(i["weight"]),
                              "grade": i.get("grade"), "contribution": c})
    print(json.dumps({"final_grade": final, "numeric": round(numeric, 2),
                      "coverage_pct": coverage, "contributions": contributions},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
