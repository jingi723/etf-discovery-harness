# Launch kit

Ready-to-edit copy for the maintainer. These drafts have not been posted.
Use the repository URL below after the documentation changes reach its default branch.

## Repository About

Suggested description:

```text
Evidence-first ETF research for Claude Code: 15 agents, holdings-level grades, pattern backtests, and explicit data gaps. Python stdlib only.
```

Suggested topics:

```text
claude-code, ai-agents, etf, financial-analysis, investment-research, python, backtesting, multi-agent, llm, explainable-ai
```

Topics help visitors discover repositories by subject; they do not promise a ranking
or star count. Add these through the repository's About settings using
[GitHub's topics instructions](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics).

## Korean community draft

Title: ETF 분석 AI가 모르는 것도 기록하게 만들었습니다 — Claude Code 리서치 에이전트

ETF 분석에서 결론보다 확인하기 어려웠던 건 그 결론의 근거와 빠진 데이터였습니다.
그래서 시장 → 섹터 → 테마 → ETF 후보를 좁혀 가면서, 찬반 근거와 구성종목 등급,
자료를 구하지 못한 항목까지 남기는 오픈소스 리서치 에이전트를 만들었습니다.

Claude Code 에이전트 15개가 조사를 나누고, Python 표준 라이브러리 도구가
계산과 패턴 백테스트를 담당합니다. 테마·재무·밸류에이션은 별도로 평가합니다.
매수·매도 추천 도구는 아닙니다.

API 키 없이 열어 볼 수 있는 과거 실행 보고서와 구성종목 맵을 넣었습니다.
실제 티커 채점에는 FMP 키가 필요합니다. 영어 프롬프트를 제공하는 `main`에서도
한국어로 요청하면 한국어로 답하며, 샘플은 과거 한국어 실행 결과입니다.
기본은 가벼운 스캔이고, 필요할 때 근거와 구성종목을 검증하는 전체 분석으로 확장합니다.

어떤 근거가 더 있어야 분석을 신뢰할 수 있을지, 첫 실행에서 어디가 막히는지
피드백을 받고 싶습니다.

https://github.com/jingi723/etf-research-agent

## English community draft

Title: Show HN: ETF research with explicit evidence gaps and holdings-level grades

I built ETF Research Agent for Claude Code to make ETF research easier to inspect: supporting
and negative evidence, separate theme/financial/valuation grades, and a report of
what data could not be obtained.

It combines 15 research agents with standard-library Python tools for scoring and
pattern backtesting. The repository includes a historical HTML holdings map you
can explore without API credentials. Live CLI analysis requires FMP access;
`main` provides English prompts and reports follow the request's language. The
historical sample reports are in Korean. Discovery starts with a scan and can be
deepened into the full evidence pipeline; measured run costs are documented.

This produces research notes, not trade recommendations. I would appreciate
feedback on the evidence trail, onboarding, and how to make missing data clearer.

https://github.com/jingi723/etf-research-agent

## 30–45 second demo recording outline

Record the actual bundled page; keep its historical date visible.

1. 0–8s: Show the README headline and launch the sample command.
2. 8–20s: Open the holdings map, select a holding, and show its weight and grade.
3. 20–30s: Open `examples/full/data_coverage.md` and show one missing-data entry.
4. 30–45s: Run `python3 tools/validate.py --self-check`, then show the repository URL.

Caption the last command as an offline self-check, not a live market analysis.
Attach a real recording when available; the current README uses an actual output screenshot.

## Follow-through

- Publish one relevant introduction, answer the feedback, then revise onboarding
  before adapting the post for another community. Check each community's current posting rules.
- For an Awesome-list submission, first verify that the list accepts this kind of
  project and follow its contribution rules. Describe the working features and sample language.
- Turn recurring user problems into small, reproducible issues that contributors can tackle.
- Record a baseline of stars, unique visitors, and clones using the repository's
  available traffic view, then compare after each release or post. Track useful bug
  reports and contributions alongside stars; do not infer causality from a single spike.

No purchased stars, automated starring, or promised Trending placement are part of this plan.
