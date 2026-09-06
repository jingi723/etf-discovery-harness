# ETF 발굴 하네스 — 데이터 계약

모든 에이전트가 준수하는 산출물 계약. 에이전트는 자신의 입력/출력 계약 섹션을 반드시 읽고 정확히 따른다.

## 목차
1. [공통 봉투(envelope)](#1-공통-봉투)
2. [등급·신뢰도 표준](#2-등급신뢰도-표준)
3. [워크스페이스 파일 배치](#3-워크스페이스-파일-배치)
4. [단계별 payload 계약](#4-단계별-payload-계약)
5. [analysis.json 최종 스키마](#5-analysisjson-최종-스키마)

---

## 1. 공통 봉투

모든 JSON 산출물은 아래 봉투로 감싼다. `payload`만 단계별로 다르다.

```json
{
  "artifact": "market_regime",
  "as_of_date": "YYYY-MM-DD",
  "generated_by": "market-regime-analyst",
  "sources": [
    {"source_name": "출처명", "source_type": "exchange|issuer|filing|gov|vendor|research|media|other",
     "url_or_reference": "URL 또는 '내부 계산'", "as_of_date": "YYYY-MM-DD", "retrieved_at": "YYYY-MM-DD",
     "reliability_tier": "primary|secondary|tertiary|unsupported",
     "used_for": "이 출처를 무엇에 썼는지", "notes": ""}
  ],
  "source_conflicts": [
    {"field": "충돌 항목", "values": [{"value": "...", "source_idx": 0}, {"value": "...", "source_idx": 1}],
     "resolution": "채택 값과 채택 근거 (공식 출처 우선 / 최신 기준일 우선)"}
  ],
  "confidence": "high|medium|low",
  "coverage": {
    "available": ["확보한 데이터 항목"],
    "missing": ["확보 못한 데이터 항목"],
    "impact_of_missing": "부족 데이터가 판단에 주는 영향 1-2문장"
  },
  "payload": {}
}
```

규칙:
- `sources`가 비어 있는 산출물은 무효다. 웹에서 확인한 데이터는 URL과 접근일을 남긴다.
- `reliability_tier` 판정과 데이터 영역별 소스 우선순위는 etf-evidence-standards 스킬(+ `references/source-priority.md`)을 따른다. `unsupported`는 등급 산정에 사용 금지.
- 출처 충돌은 삭제하지 않고 `source_conflicts`에 기록한다 (충돌 없으면 빈 배열).
- 데이터가 없는 항목은 `null`로 두고 `coverage.missing`에 기록한다. 값을 지어내지 않는다.

## 2. 등급·신뢰도 표준

- 등급 체계: `A+ A0 A- B+ B0 B- C+ C0 C- D` (10단계). 숫자 매핑 A+=10 … D=1.
- 가중평균 등급은 반드시 etf-grading-standards 스킬의 `scripts/weighted_grade.py`로 계산한다 (LLM 암산 금지).
- 커버리지 60% 미만이면 등급 대신 `null` + `"grade_note": "분석 제한 — 커버리지 부족"`.
- 출처 신뢰도는 4티어(`primary`/`secondary`/`tertiary`/`unsupported`) — etf-evidence-standards의 소스 우선순위 정책(references/source-priority.md)을 따른다. tertiary는 단독 근거 불가, unsupported는 사용 금지.
- 개별 주장(claim)의 `confidence`(high/medium/low)는 출처 티어·출처 수·데이터 명확성을 종합한 판정이다 — 출처 티어와 별개 필드.

## 3. 워크스페이스 파일 배치

기준 디렉토리: `프로젝트루트/_workspace/`

```
_workspace/
├── 00_input/run_config.json          # 실행 설정 (오케스트레이터 작성)
├── 00_coverage_precheck.md           # 사전 데이터 커버리지 진단
├── 01_market_regime.json
├── 02_sector_scores.json
├── 03_themes_{sector_slug}.json      # 섹터별 1개
├── 04_evidence_{theme_slug}.json     # 테마별 1개
├── 05_selected_themes.json
├── 06_etf_candidates_{theme_slug}.json
├── 07_valuechain_{etf_ticker}.json
├── 08_theme_structure_{etf_ticker}.json
├── 09_financial_{etf_ticker}.json
├── 10_valuation_{etf_ticker}.json
├── 11_comparison.json
├── 12_decision.json
├── 13_reports/                       # 최종 산출물 초안 (pilot 4종 / full 5종)
├── 14_qa_report.json
├── 15_ui/                            # UI 변환 레이어
│   ├── ui_payload.json               # 화면용 경량 JSON (계약: etf-ui-render 스킬)
│   ├── ui_payload_audit.md
│   └── html/                         # discovery_index·etf_{ticker}·compare·report.html
└── 16_ui_render_qa.json / .md
```

UI 레이어 산출물의 상세 계약(ui_payload 필수 필드, HTML 생성 원칙, UI QA 체크리스트)은 `.claude/skills/etf-ui-render/SKILL.md`에 있다. 최종 복사 위치: `output/{run_date}/ui/`.

slug 규칙: 한글은 짧은 영문 슬러그로 (예: `AI 반도체` → `ai-semi`, `정보기술` → `it`). 오케스트레이터가 run_config.json에 slug 매핑을 기록하고 모든 에이전트가 이를 따른다.

### run_config.json

```json
{
  "run_date": "YYYY-MM-DD",
  "market_scope": ["KR", "US"],
  "sectors_scope": ["정보기술", "산업재", "헬스케어", "에너지·전력", "커뮤니케이션"],
  "max_themes_per_sector": 10,
  "evidence_shortlist_per_sector": 3,
  "selected_themes_count": 3,
  "max_etf_per_theme": 5,
  "deep_score_etf_per_theme": 3,
  "output_scope": "pilot|full",
  "delivery_formats": ["pdf"],
  "structure_gate_thresholds": {
    "min_aum": {"KR": "500억원", "US": "USD 100M"},
    "min_avg_trading_value": {"KR": "5억원/일", "US": "USD 5M/일"},
    "max_spread_pct": 0.3,
    "max_abs_premium_discount_pct": 1.0,
    "min_listing_months": 6,
    "note": "기본값은 잠정치 — MVP 실행 결과를 보고 조정한다"
  },
  "slug_map": {"정보기술": "it", "AI 반도체": "ai-semi"}
}
```

`output_scope`: `pilot`이면 최종 산출물을 4종(data_coverage, sector_theme_discovery, final_etf_decision, analysis.json)으로 축소하고 etf_candidates.md 내용은 final_etf_decision.md의 후보 비교 섹션에 포함한다. `full`이면 5종 전부.

`delivery_formats`: 기본값은 `["pdf"]`. PDF는 읽기·공유용 일회성 보고서, HTML은 인터랙티브 탐색용, PNG는 `discovery_index` 요약 공유용, DOCX는 사용자가 후편집을 요청한 경우에만 사용한다. HTML은 다른 형식의 원본이므로 선택값과 관계없이 생성한다. 내보내기 도구가 없으면 HTML을 보존하고 누락 형식과 설치 조건을 완료 보고에 명시한다.

## 4. 단계별 payload 계약

### 01_market_regime.json — payload

```json
{
  "summary": "시장 환경 요약 3-5문장",
  "indicators": {
    "rates": {"value": "...", "trend": "up|down|flat", "source_idx": 0},
    "fx": {}, "inflation": {}, "commodities": {}, "equity_indices": {},
    "risk_appetite": {}, "monetary_policy": {}, "policy_events": {},
    "sector_earnings_outlook": {}
  },
  "favorable_sector_types": [{"type": "정보기술", "why": "..."}],
  "unfavorable_sector_types": [{"type": "...", "why": "..."}],
  "key_risks": ["..."]
}
```

### 02_sector_scores.json — payload

```json
{
  "sectors": [{
    "name": "정보기술",
    "criteria": {
      "macro_fit": "B+", "earnings_momentum": "A-", "relative_strength": "B0",
      "valuation_burden": "C+", "risk_overheat": "B-", "flows_positioning": "B0"
    },
    "grade": "B+",
    "rationale": ["좋은 근거 2-4개"],
    "risks_to_check": ["확인할 리스크 1-3개"],
    "selected": true
  }],
  "selected_sectors": ["정보기술", "산업재", "에너지·전력"]
}
```

`grade`는 6개 criteria의 동일가중 평균을 weighted_grade.py로 계산.

### 03_themes_{sector}.json — payload

```json
{
  "sector": "정보기술",
  "themes": [{
    "name": "AI 반도체",
    "positive": ["..."], "negative": ["..."],
    "value_chain": ["설계", "파운드리", "HBM", "장비"],
    "key_metrics": ["확인할 핵심 지표 후보"],
    "data_availability": "high|medium|low",
    "etf_investable": true,
    "example_etfs": ["티커 또는 이름"],
    "explainability": "high|medium|low",
    "impact": "high|medium|low",
    "confidence": "high|medium|low",
    "shortlisted": false
  }]
}
```

테마는 섹터당 최소 10개. `shortlisted`는 오케스트레이터가 사전 필터 후 갱신.

### 04_evidence_{theme}.json — payload

```json
{
  "theme": "AI 반도체",
  "checklist": ["이 테마에서 확인해야 할 질문들 — 데이터 수집 전에 먼저 작성"],
  "evidence": [{
    "claim": "확인된 사실 1문장",
    "data": "구체 수치/내용",
    "direction": "positive|negative",
    "source_idx": 0,
    "as_of": "YYYY-MM-DD",
    "confidence": "high|medium|low"
  }],
  "missing": ["확보하지 못한 데이터 항목"]
}
```

### 05_selected_themes.json — payload

```json
{
  "selected": [{
    "theme": "AI 반도체",
    "reason": "선정 이유 — 근거 데이터 명시",
    "vs_rejected": "탈락 테마 대비 우선인 이유",
    "main_point": "메인 투자 포인트 1개",
    "sub_points": ["보조 포인트"],
    "risks": ["리스크 포인트"],
    "etf_keywords": ["ETF 검색용 키워드"],
    "value_chain": ["..."],
    "missing_data": ["부족한 데이터"],
    "data_confidence": "high|medium|low",
    "etf_investability": "high|medium|low",
    "min_conditions_met": ["충족한 최소 선정 조건 번호(8개 중 2개 이상)"]
  }],
  "rejected": [{
    "theme": "...",
    "reason_type": "데이터 부족|ETF 후보 부족|가격 부담 과도|실적 연결성 부족|수요·병목 구조 불명확|리스크 과다|설명 가능성 낮음|테마가 너무 넓거나 모호함|ETF가 테마를 순수하게 담기 어려움",
    "reason": "구체 사유 1-2문장"
  }]
}
```

### 06_etf_candidates_{theme}.json — payload

```json
{
  "theme": "AI 반도체",
  "candidates": [{
    "name": "ETF명", "ticker": "코드", "market": "KRX|NYSE|NASDAQ",
    "issuer": "운용사", "index": "추종지수", "style": "패시브|액티브",
    "holdings_count": 30, "aum": "표기단위 포함 문자열", "avg_volume": "...",
    "expense_ratio": "0.45%",
    "type": "순수 테마형|밸류체인 혼합형|빅테크 중심형|대표지수형|고분산형|액티브형",
    "structure_trading": {
      "listing_date": "YYYY-MM-DD",
      "leverage_inverse": false,
      "single_stock_leverage": false,
      "synthetic_swap": false,
      "option_strategy": false,
      "currency_hedged": null,
      "spread_pct": null,
      "premium_discount_pct": null,
      "tracking_error": null,
      "tracking_difference": null,
      "real_cost_notes": "총보수 외 실질 비용 관련 확인 사항",
      "lp_quality": null,
      "holdings_transparency": "daily|periodic|opaque"
    }
  }]
}
```

`structure_trading`은 ETF 구조·거래 하드 게이트의 입력이다. 확인 불가 항목은 null + missing 기록 (구조 관련 boolean은 투자설명서·상품 페이지에서 반드시 확인 — 레버리지/합성 여부를 null로 두지 않는다).

### 07_valuechain_{etf}.json — payload

```json
{
  "etf": {"name": "...", "ticker": "..."},
  "theme": "AI 반도체",
  "chains": [{
    "chain": "AI 반도체·장비", "weight_pct": 35.0,
    "holdings": [{"name": "종목", "weight_pct": 8.2, "role": "이 종목이 체인에서 하는 역할"}]
  }],
  "unclassified_pct": 5.0,
  "purity_pct": 62.0,
  "holdings_coverage_pct": 95.0
}
```

`purity_pct` = 대상 테마의 핵심 밸류체인에 속한 비중 합. ETF 이름이 아니라 실제 보유종목 기준으로 분류한다.

### 08/09/10 스코어 파일 — 공통 payload 형태

```json
{
  "etf": {"name": "...", "ticker": "..."},
  "axis": "theme_structure|financial|valuation",
  "items": [{
    "name": "밸류체인명 또는 종목명", "weight_pct": 35.0,
    "grade": "A-", "rationale": "등급 근거 1-2문장 (데이터 인용)",
    "metrics": {}
  }],
  "final_grade": "B+",
  "final_numeric": 7.2,
  "coverage_pct": 88.0,
  "uplift_factors": ["등급 상승 요인"],
  "drag_factors": ["감점 요인"],
  "explanation": "최종 등급 설명 — weighted_grade.py 결과를 인용해 서술"
}
```

- 08(테마 구조): items = 밸류체인, metrics = 전망·구조 데이터. 07의 weight_pct를 그대로 사용.
- 09(재무 상태): items = 상위 보유종목(비중 80% 이상 커버 목표), metrics = 매출성장·영업이익률·ROE·FCF·부채비율 등 **현재/최근 데이터만**.
- 10(가격 적정성): items = 상위 보유종목, metrics = PER(TTM/선행)·PBR·EV/EBITDA·FCF yield 등 + 업종/자기 과거 대비. 성장성 맥락을 rationale에 병기.

### 11_comparison.json — payload

```json
{
  "themes": [{
    "theme": "AI 반도체",
    "table": [{
      "etf": "티커",
      "theme_structure": "A-", "financial": "B+", "valuation": "C-",
      "purity_pct": 62.0, "top10_concentration_pct": 58.0,
      "expense_ratio": "0.45%", "liquidity": "high|medium|low",
      "tracking_quality": "high|medium|low|unknown",
      "structure_trading_gate": {
        "status": "pass|conditional|hold|low_priority",
        "reasons": ["게이트 판정 사유 — 걸린 체크 항목"],
        "impact": "이 판정이 Decision Gate에 주는 영향 1문장"
      },
      "verdict_hint": "조건부 검토",
      "notes": ["비교 코멘트"]
    }]
  }]
}
```

`structure_trading_gate.status` 한국어 대응: pass=구조·거래 문제 없음, conditional=조건부 확인 필요, hold=판단 보류, low_priority=우선순위 낮음.

### 12_decision.json — payload

```json
{
  "finalists": [{
    "etf": {"name": "...", "ticker": "...", "theme": "..."},
    "status": "검토 가능|조건부 검토|판단 보류|우선순위 낮음",
    "axes": {"theme_structure": "A-", "financial": "B+", "valuation": "C-"},
    "structure_trading_gate": {"status": "pass|conditional|hold|low_priority", "reasons": []},
    "gate_trace": "5단계 판정 순서에서 어느 게이트에 걸렸는지 1문장",
    "why_remained": ["남은 이유"],
    "check_points": ["확인할 점"],
    "recheck_conditions": ["재검토 조건"],
    "alternatives": ["비교가 필요한 대안"]
  }],
  "excluded": [{"etf": "...", "why": "제외 이유"}]
}
```

### 14_qa_report.json — payload

```json
{
  "forbidden_phrase_hits": [{"file": "...", "line": 0, "phrase": "..."}],
  "structural_checks": [{"check": "...", "passed": true, "evidence": "..."}],
  "data_integrity_checks": [{"check": "...", "passed": true, "evidence": "..."}],
  "gate_checks": [{"check": "구조·거래 게이트 적용/판정 순서 일치 등", "passed": true, "evidence": "..."}],
  "pilot_acceptance": {"passed": [], "failed": [], "needs_revision": []},
  "verdict": "pass|fix_required",
  "fix_instructions": ["report-generator에게 전달할 수정 지시"]
}
```

`pilot_acceptance`는 output_scope=pilot일 때 15문항 acceptance test 결과 (full이면 null).

## 5. analysis.json 최종 스키마

report-generator가 01~12 산출물을 조립한다. 최상위 키(모두 필수, meta 포함 20개):

```json
{
  "meta": {"run_date": "", "as_of_date": "", "harness_version": "1.1", "output_scope": "pilot|full", "disclaimer": "본 자료는 투자 추천이 아니며 정보 제공 목적입니다."},
  "market_regime": {},          // 01 payload
  "sector_scores": {},          // 02 payload
  "theme_candidates": [],       // 03 payload 배열 (섹터별)
  "theme_evidence": [],         // 04 payload 배열
  "selected_themes": {},        // 05 payload
  "etf_candidates": [],         // 06 payload 배열
  "value_chain_mapping": [],    // 07 payload 배열
  "theme_structure_scores": [], // 08 payload 배열
  "financial_scores": [],       // 09 payload 배열
  "valuation_scores": [],       // 10 payload 배열
  "decision_gate_result": {},   // 12 payload
  "etf_structure_trading_gate": [],      // ETF별 게이트 결과 (11의 structure_trading_gate 취합)
  "source_quality_policy": {},           // 소스 품질 요약
  "investment_judgment_readiness": {},   // 투자 판단 가능성
  "investor_fit_required": true,         // 사용자 조건 기반 적합성 검토 필요 여부 (항상 true — Investor Fit은 추후 확장)
  "pilot_acceptance_summary": {},        // 1차 파일럿 체크리스트 결과 (QA가 작성, full 실행은 null 허용)
  "data_coverage": {},          // 전 단계 coverage 취합
  "explanation": {},            // ETF별 최종 설명 문구 (UI 표출용)
  "sources": []                 // 전 단계 sources 병합 (중복 제거)
}
```

### 신규 키 상세

```json
"etf_structure_trading_gate": [{
  "etf": "티커",
  "status": "pass|conditional|hold|low_priority",
  "checks": {"aum": {}, "trading_value": {}, "spread": {}, "premium_discount": {},
             "tracking_error": {}, "expense": {}, "structure": {}, "listing_period": {}},
  "reasons": [],
  "impact_on_decision_gate": ""
}],
"source_quality_policy": {
  "primary_sources_used": [],
  "secondary_sources_used": [],
  "tertiary_sources_used": [],
  "source_conflicts": [],       // 전 단계 source_conflicts 취합
  "unsupported_claims": []      // unsupported 출처에 의존해 제외된 주장 (있으면 안 되지만 감사용)
},
"investment_judgment_readiness": {
  "can_decide_from_this_analysis": ["이 정보만으로 판단 가능한 것"],
  "cannot_decide_without_user_context": ["사용자 조건 없이는 판단 불가한 것"],
  "next_actions": ["사용자가 다음에 할 수 있는 행동"],
  "requires_investor_fit_check": true,
  "disclaimer": "이 결과는 ETF 후보의 구조와 리스크를 판단하기 위한 참고 정보입니다. 실제 투자 실행 여부는 투자 기간, 투자 금액, 손실 허용도, 보유 포트폴리오 등을 함께 고려해야 합니다."
},
"pilot_acceptance_summary": {
  "passed": [], "failed": [], "needs_revision": []
}
```
