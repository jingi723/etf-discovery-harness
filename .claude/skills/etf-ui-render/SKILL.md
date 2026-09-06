---
name: etf-ui-render
description: "리서치 결과(analysis.json)를 모바일 WebView HTML과 일회성 PDF·PNG·DOCX로 변환하는 표준. ui_payload.json 계약, 구성종목 점수 지도(트리맵) 구조, 렌더 스크립트 실행, 내보내기 형식 선택이 필요할 때 사용할 것. 리서치 판단은 이 레이어에서 만들지 않는다."
---

# ETF UI·보고서 전달 표준

리서치 판단의 **시각적 표현물만** 담당한다. 등급을 계산하지 않고, 판단 문구를 만들지 않고, 원본에 없는 수치를 쓰지 않는다.

## 레이어 구조

```
analysis.json  → [ui-payload-builder]  → ui_payload.json      (발췌 — 유일한 해석 지점)
ui_payload.json → [tools/render.py]    → html/*.html          (결정적 렌더 — 해석 없음)
html/*.html     → [export_report.py]   → pdf / png / docx     (선택)
```

analysis.json은 감사 추적용이라 수백 KB다. 렌더러가 직접 읽으면 컨텍스트 낭비이자 원본 재해석(=왜곡) 위험이 생긴다. 발췌는 payload builder 한 곳에서만 일어나야 추적 가능하다.

## 렌더링은 스크립트가 한다

```bash
python3 tools/render.py _workspace/15_ui/ui_payload.json -o _workspace/15_ui/html/
python3 {이 스킬 디렉토리}/scripts/check_html.py _workspace/15_ui/html/ --payload _workspace/15_ui/ui_payload.json
```

**HTML을 에이전트가 직접 쓰지 않는다.** 이유 두 가지:
1. 수만 자 응답은 연결 중단으로 작업 전체가 유실된다 (2026-07-05 실행에서 2회 발생).
2. 값을 지어낼 수 없는 렌더러는 값을 왜곡할 수 없다. 같은 payload면 항상 같은 바이트가 나오므로 렌더 결과를 사람이나 에이전트가 재검수할 이유가 없다 — 검수는 payload에서 끝난다.

`check_html.py`가 미치환 플레이스홀더·금지 표현·태그 균형·중복 id·외부 리소스를 기계 검사한다. 0건이 아니면 payload나 render.py를 고친다.

디자인을 바꾸려면 `tools/render.py`의 스타일 토큰(`CARD`, `gcol`, `heat_col` 등)을 수정한다. payload 계약이 바뀌면 렌더러도 함께 고친다.

## ui_payload.json 계약

최상위 필수 키:

```json
{
  "meta": {"run_date": "", "as_of_date": "", "disclaimer": "", "data_dates": {"holdings": "", "price": "", "analysis_updated": ""}},
  "pages": ["discovery_index", "etf_463250", "..."],
  "discovery_index": {
    "headline": "", "market_one_liner": "",
    "selected_sectors": [{"name": "", "grade": "", "reason": ""}],
    "selected_themes": [{"name": "", "grade": "", "main_point": ""}],
    "finalists": [{"ticker": "", "name": "", "theme": "", "decision_state": "", "ratings": {}}],
    "data_warnings": [], "next_checks": []
  },
  "etf_pages": [ /* 아래 etf_page 계약 */ ],
  "compare_page": {"rows": [{"ticker": "", "name": "", "theme": "", "decision_state": "", "theme_structure": "", "financial": "", "valuation": "", "structure_gate": "", "why_remained": [], "check_points": []}]},
  "warnings": [],
  "source_trace": [{"field": "etf_pages[0].summary", "from": "analysis.json:explanation.463250.status_text"}]
}
```

etf_page 필수 필드:

```json
{
  "ticker": "", "name": "", "market": "", "theme": "",
  "price": null, "change": null,
  "decision_state": "조건부 검토",
  "ratings": {"theme_structure": "", "financial": "", "valuation": ""},
  "ratings_meta": {"theme_structure": {"coverage_pct": 0, "confidence": ""}, "financial": {}, "valuation": {}},
  "summary": "1-2문장 요약",
  "why_conditionally_considered": ["판단 상태 사유"],
  "structure_gate": {"status": "", "reasons": []},
  "theme_key_point": {"name": "", "structure_grade": "", "main_point": "", "interpretation": ""},
  "value_chain": [{"name": "", "pct": 0, "grade": "", "point": "", "risk": "", "related_holdings": []}],
  "holdings_heatmap": [{
    "name": "", "short_name": "", "ticker": null, "weight_pct": 0,
    "financial_grade": "", "valuation_grade": "",
    "value_chain": "이 종목이 속한 밸류체인", "data_confidence": "high|medium|low",
    "is_analyzed": true
  }],
  "holdings_heatmap_meta": {
    "display_count": 0, "coverage_pct": 0, "top10_weight_pct": 0,
    "other_bucket_label": "기타", "other_bucket_pct": 0,
    "area_rule": "weight_pct", "color_rule": "selected_tab_grade"
  },
  "top_holdings": [{"name": "", "weight_pct": 0, "role": ""}],
  "financial_detail": {"summary": "", "uplift": [], "drag": []},
  "valuation_detail": {"summary": "", "uplift": [], "drag": []},
  "data_warnings": ["스프레드·추적오차 미확보 등 — 숨기지 말 것"],
  "disclaimer": ""
}
```


## 변환 원칙 (payload builder)

- 원본에 없는 수치를 만들지 않는다. 등급을 재계산하지 않는다. analysis.json의 등급·커버리지·신뢰도·판단 상태를 그대로 복사한다.
- 텍스트는 UI 길이에 맞게 줄일 수 있으나 의미를 바꾸지 않는다. "조건부 검토"를 "검토 가능"처럼 완화하거나 그 반대로 표현하면 왜곡이다.
- 긴 설명은 버리지 말고 detail/accordion용 필드로 보낸다.
- 데이터 부족·출처 충돌·confidence low는 숨기지 않고 `data_warnings`에 넣는다 — UI에서 경고가 보이는 것이 이 서비스의 신뢰 장치다.
- 가격(price/change)은 analysis.json에 있을 때만 채운다. 없으면 null (렌더러가 "가격 데이터 없음" 처리).
- 주요 문구의 출처 필드를 `source_trace`에 기록한다 (원본 추적성 — UI QA 체크 대상).
- 매수·추천 표현 금지 (etf-compliance-rules의 금지 목록 준수).

### 페이지 구성

| 페이지 | 내용 |
|--------|------|
| discovery_index.html | 시장 환경 한 줄 + 선정 섹터 + 핵심 테마 3 + 최종 후보 3(판단 상태 뱃지) + 데이터 부족 경고 + 다음 확인 항목. mock의 카드 스타일 재사용 |
| etf_{ticker}.html | mock 레이아웃 그대로: 헤더(이름/코드/가격) → AI 분석 요약(판단 상태+요약) → 핵심 등급 3축 바 → 조건부 검토 사유 → 테마 핵심 포인트 → 밸류체인 비중(선택 인터랙션) → 구성종목 점수 지도(히트맵 필수, 아래 구조) → 상위 구성종목 → 데이터 기준·면책 |
| compare.html (선택) | 후보 3개 × (판단 상태/3축/게이트/남은 이유/확인할 점) 카드형 비교 — 표가 넓으면 카드로 |
| report.html | PDF·DOCX 원본. 시장·섹터·테마 요약 → 후보 비교 → finalist별 판단 상태·3축·게이트·리스크 → 데이터 부족·기준일·면책 순서의 단일 문서. 인터랙션 없이 인쇄 CSS(`@media print`)를 포함 |

### 구성종목 점수 지도 — 필수 구조 (순서 고정)

이 섹션의 메인 UI는 **종목 히트맵(트리맵)**이다. 표만 나오면 실패다 — 히트맵이 반드시 표보다 먼저 나와야 한다. 이유: 이 화면의 목적은 "비중 큰 종목의 등급이 ETF 전체 등급을 어떻게 끌고 가는가"를 한눈에 보이게 하는 것이며, 면적×색 인코딩이 그 역할을 한다.

1. 섹션 제목: 구성종목 점수 지도
2. 짧은 설명: "면적은 ETF 내 비중, 색은 선택한 기준의 등급입니다."
3. 탭: [재무 상태 | 가격 적정성] — 탭 전환 시 색만 바뀜 (면적=비중 고정)
4. 종목 히트맵: 면적=weight_pct, 색=선택 탭의 등급(financial_grade/valuation_grade). 등급 null=회색 "분석 제한". 레이아웃은 렌더 시점에 계산(squarify)하고 탭 전환은 JS로 색·라벨만 스왑
5. 히트맵 하단 선택 종목 요약: 종목명·비중·재무 등급·가격 등급 (타일 탭/클릭으로 갱신)
6. 범례: A계열 우호적 / B계열 양호 / C계열 확인 필요 / D·F계열 주의 / 분석 제한 회색
7. 상위 종목 비중 요약: "상위 {N}개 종목이 전체의 {top10_weight_pct}%를 차지합니다."
8. 구성종목 상세보기 버튼 (토글)
9. 상위 10개 종목 표 (종목명/비중/재무/가격) — 버튼 아래 상세로

## 일회성 보고서 형식 선택

- **PDF (기본)**: 읽기·보관·공유에 가장 안정적이다. 페이지가 길어도 인쇄 단위로 나뉘고 레이아웃이 고정된다.
- **HTML**: 밸류체인·히트맵 상호작용이 필요할 때 사용한다. 다른 내보내기 형식의 원본이므로 항상 생성한다.
- **PNG**: 메신저나 모바일에서 빠르게 훑는 `discovery_index.html` 요약에만 사용한다. 긴 전체 보고서를 한 장 이미지로 만들면 글자가 작아지므로 금지한다.
- **DOCX**: 사용자가 문구를 직접 편집하거나 사내 양식에 옮겨야 할 때만 생성한다. 보존·배포 기본값으로 사용하지 않는다.

로컬 도구 확인 및 내보내기:

```bash
python3 {이 스킬 디렉토리}/scripts/export_report.py --check
python3 {이 스킬 디렉토리}/scripts/export_report.py report.html --format pdf --output final_report.pdf
python3 {이 스킬 디렉토리}/scripts/export_report.py discovery_index.html --format png --output summary.png
python3 {이 스킬 디렉토리}/scripts/export_report.py report.html --format docx --output final_report.docx
```

PDF·PNG는 Chrome/Chromium(`CHROME_BIN`으로 경로 지정 가능), DOCX는 pandoc 또는 macOS `textutil`을 사용한다. 스크립트가 의존성을 설치하거나 네트워크로 전송하지 않는다. 필요한 도구가 없으면 HTML을 최종 폴백으로 보존하고 누락 형식을 명시한다.
