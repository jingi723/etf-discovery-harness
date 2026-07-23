---
name: etf-ui-render
description: "ETF 발굴 하네스의 UI·일회성 보고서 전달 레이어 표준. analysis.json → ui_payload.json 변환, mock.html 기반 모바일 WebView HTML과 인쇄용 report.html 생성, UI 렌더 QA, PDF·요약 PNG·편집용 DOCX 내보내기에서 반드시 이 스킬을 사용할 것. UI/HTML/WebView/PDF/PNG/Word/DOCX 생성·재생성·수정과 렌더 검수 작업에서 트리거."
---

# ETF UI·보고서 전달 표준

리서치 산출물을 모바일 WebView HTML과 공유 가능한 일회성 보고서로 변환하는 후처리 레이어의 공용 표준. **이 레이어는 분석하지 않는다** — 등급·판단 상태·수치를 새로 만들거나 바꾸면 상류 QA를 통과한 결과가 왜곡되므로, 상류 값을 그대로 표현만 한다.

## 레이어 구조와 데이터 흐름

```
analysis.json (감사용 원본, ~700KB — 렌더러가 직접 읽기 금지)
  → [ui-payload-builder] → ui_payload.json (UI용 경량 JSON, 유일한 렌더 입력)
  → [html-mock-renderer] → html/*.html (탐색 페이지 + 인쇄용 report.html)
  → [ui-render-qa]       → ui_render_qa.json/md (왜곡·잔여 mock·컴플라이언스 검수)
  → [export_report.py]   → deliverables/final_report.{pdf|docx}, summary.png (선택)
```

경량화를 거치는 이유: analysis.json은 전체 파이프라인 감사 추적용이라 크고(수백 KB), 렌더러가 직접 읽으면 컨텍스트 낭비 + 원본 재해석(=왜곡) 위험이 생긴다. 화면용 발췌는 payload builder 한 곳에서만 일어나야 추적 가능하다.

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

## mock.html 사용 규칙 (renderer)

템플릿: 이 스킬의 `assets/mock.html` (402px 모바일 ETF AI 분석 탭, 인라인 스타일, Pretendard 폰트).

**중요 — 이 목업은 그대로 열면 동작하지 않는다.** 커스텀 런타임(DCLogic, `{{ }}` 바인딩)과 번들러 UUID 리소스(`src="cda153ca-..."`, 폰트 url)가 원본 번들에만 존재하기 때문이다. 따라서 렌더러는:

1. mock.html을 **시각 레퍼런스**로 사용한다 — 레이아웃 구조, 인라인 CSS, 색상(#F4F6F8 배경, #1A1D21 텍스트 등), 카드 스타일을 그대로 가져온다.
2. **정적 렌더링**한다 — `{{ 표현식 }}`을 ui_payload 값으로 직접 치환하고, 반복 블록(밸류체인 바, 종목 리스트)은 payload 배열만큼 전개한다. DCLogic 클래스와 `<script src="cda153ca-...">`는 제거한다.
3. 깨진 리소스를 정리한다 — UUID를 참조하는 `@font-face`의 url()은 제거하고 `font-family: Pretendard, -apple-system, 'Apple SD Gothic Neo', sans-serif` 폴백 스택만 유지한다.
4. mock 데이터(네오 미국 AI반도체 밸류체인, 490100, 12,340원, mock 등급·종목·컨센서스 문구)는 전부 실제 값으로 교체한다. **payload에 대응 값이 없는 mock 블록은 제거하거나 "데이터 부족" 처리한다** (예: '시장 컨센서스', '지난 분석 이후'는 상류에 데이터가 없으면 섹션 제거 또는 "첫 분석 — 다음 실행부터 기록" 문구).
5. 인터랙션(밸류체인 선택, 아코디언, 바텀시트, 탭)은 프레임워크 없이 바닐라 JS 수십 줄로 재구현한다. 그 이상의 JS 금지.
6. 매핑이 애매한 블록은 임의로 채우지 말고 render_notes.md에 기록 후 미매핑 처리한다.

## HTML 생성 원칙

- 외부 네트워크 리소스 0 (완전 오프라인 동작).
- API 키·secret·analysis.json 원본 전문을 HTML에 넣지 않는다.
- 면책 문구와 데이터 기준일(run_date, as_of, holdings/price 기준일)은 모든 페이지에 필수.
- 모바일 폭 360~430px 기준. mock의 402px 고정폭 컨테이너는 `width:100%;max-width:430px`로 완화해 360px에서 깨지지 않게 한다.
- 페이지 간 이동: 같은 폴더의 상대 링크(`etf_463250.html` 등)로 연결.

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

## UI QA 체크리스트 (ui-render-qa)

기계 검사는 스크립트로 실행한다:
```bash
python3 {이 스킬 디렉토리}/scripts/check_html.py <html 디렉토리> --payload <ui_payload.json>
```
(mock 잔여 문자열, 금지 표현, 중복 id, 태그 균형, 외부 리소스·UUID 잔존, {{ }} 미치환을 검사)

판정 항목 10개:
1. **mock 잔여**: 네오/490100/12,340원/mock 등급·종목이 남아 있으면 실패 (스크립트)
2. **등급 일치**: HTML의 3축 등급·decision_state가 ui_payload와 일치하고, ui_payload가 analysis.json과 일치 (표본 교차 대조)
3. **판단 상태 비왜곡**: 조건부 검토→검토 가능 완화, 판단 보류→"나쁜 ETF" 폄하 표현 실패
4. **데이터 부족 표시**: data_warnings가 화면에 실제로 보이는지 (숨김 처리 실패)
5. **금지 표현 0건** (스크립트)
6. **UI 구조 유지**: AI 분석 요약/테마 핵심 포인트/구성종목 점수 지도/데이터 기준 섹션 존재
7. **모바일 렌더**: 360px 기준 고정폭 초과 요소·가로 스크롤 요소 없는지 (스타일 정적 검사)
8. **기준일 보존**: run_date/as_of/holdings·price 기준일/confidence/coverage 표기
9. **HTML 유효성**: 파싱 가능, 중복 id 0, 미치환 {{ }} 0 (스크립트)
10. **원본 추적성**: 주요 문구의 출처가 render_notes.md 또는 source_trace에 기록됨

verdict: `pass` / `fix_required` (+ fix_instructions는 파일·위치·수정 방향 구체 기재, 렌더러가 그대로 실행 가능한 수준).

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
