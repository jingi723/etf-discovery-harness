---
name: etf-discovery-orchestrator
description: "ETF 발굴 에이전트 하네스의 오케스트레이터. '섹터 → 테마 → ETF 후보 → 검증' 파이프라인으로 투자 후보 ETF를 발굴하고 최종 리포트(pilot 4종/full 5종), 모바일 WebView UI, 일회성 PDF·요약 PNG·편집용 DOCX를 생성한다. ETF 발굴/분석/검증, 섹터 분석, 테마 발굴, 시장 환경 진단, ETF 후보 비교, 투자 후보 리포트 요청 시 반드시 이 스킬을 사용할 것. 후속 작업 — ETF 분석 다시 실행, 재실행, 업데이트, 특정 단계만 다시(테마만 다시, 리포트만 다시, 특정 ETF만 재검증, UI나 PDF/이미지/Word만 다시), 이전 결과 개선/보완/수정, 결과 리포트 재생성, UI/HTML/WebView/PDF/PNG/DOCX 생성·재생성·수정 요청 시에도 반드시 이 스킬을 사용."
---

# ETF Discovery Orchestrator

"섹터 → 테마 → ETF 후보 → 검증" 순서로 투자 후보를 발굴하는 에이전트 파이프라인의 조율자. 특정 ETF를 좋게 설명하는 도구가 아니라, 시장 환경에서 출발해 후보를 좁혀가는 발굴 도구다.

**절대 원칙** (모든 단계에 우선):
1. 매수·매도 추천 금지. 최종 결론은 반드시 `검토 가능 / 조건부 검토 / 판단 보류 / 우선순위 낮음` 중 하나.
2. 데이터 없는 내용 추정 금지 — 부족하면 "분석 제한 / 신뢰도 낮음 / 판단 보류".
3. 점수 계산(스크립트)과 설명 생성(LLM) 분리. 테마 분석(전망)과 구성종목 분석(현재 재무) 분리.
4. 모든 결과에 기준일·출처·신뢰도 표기.

## 실행 모드: 서브 에이전트 (파이프라인 + 팬아웃)

선택 이유: 단계 간 데이터가 엄격한 파일 계약(`references/data-contracts.md`)으로 흐르는 결정적 파이프라인이며, 스코어러 3축은 상호 참조가 금지(축 독립성)되어 팀원 간 통신이 오히려 원칙 위반을 유발한다. QA↔리포트는 오케스트레이터가 중재하는 생성-검증 루프로 처리한다. 모든 Agent 호출에 `model: "opus"`를 명시한다.

## 에이전트 구성

| 에이전트 | 담당 Phase | 팬아웃 단위 | 출력 (_workspace/) |
|---------|-----------|------------|-------------------|
| market-regime-analyst | 2 | 단일 | 01_market_regime.json |
| sector-scorer | 3 | 단일 | 02_sector_scores.json |
| theme-discoverer | 4 | 섹터당 1 | 03_themes_{sector}.json |
| theme-evidence-collector | 5 | 테마당 1 | 04_evidence_{theme}.json |
| theme-ranker | 6 | 단일 | 05_selected_themes.json |
| etf-candidate-finder | 7 | 테마당 1 | 06_etf_candidates_{theme}.json |
| value-chain-mapper | 8 | ETF당 1 | 07_valuechain_{etf}.json |
| theme-structure-scorer | 9 | ETF당 1 | 08_theme_structure_{etf}.json |
| holdings-financial-scorer | 9 | ETF당 1 | 09_financial_{etf}.json |
| holdings-valuation-scorer | 9 | ETF당 1 | 10_valuation_{etf}.json |
| etf-evaluator | 10 | 단일 | 11_comparison.json |
| decision-gate | 11 | 단일 | 12_decision.json |
| report-generator | 12 | 단일 | 13_reports/ (pilot 4종/full 5종) |
| qa-compliance-guard | 13 | 단일 | 14_qa_report.json |
| ui-payload-builder | 13.5a | 단일 | 15_ui/ui_payload.json (+audit) |
| html-mock-renderer | 13.5b | 단일 | 15_ui/html/*.html (탐색 페이지 + 인쇄용 report.html) |
| ui-render-qa | 13.5c | 단일 | 16_ui_render_qa.json/md |

## 워크플로우

### Phase 0: 컨텍스트 확인 (후속 작업 지원)

1. `_workspace/` 존재 여부 확인.
2. 실행 모드 결정:
   - **미존재** → 초기 실행, Phase 1로.
   - **존재 + 부분 수정 요청** (예: "리포트만 다시", "테마 다시 뽑아줘", "ETF X 재검증") → **부분 재실행**: 요청이 걸리는 가장 이른 Phase를 찾아 그 지점부터 하류만 재실행한다. 상류 산출물은 그대로 재사용. 해당 에이전트 프롬프트에 기존 산출물 경로와 사용자 피드백을 포함한다.
   - **존재 + 새 실행 요청** (기준일 변경, 새 조건) → 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동 후 초기 실행.
3. 부분 재실행의 하류 전파: 예를 들어 05가 바뀌면 06 이후 전부 재실행 대상이다. 파일 의존 그래프는 위 표의 Phase 순서를 따른다.

### Phase 1: 준비 + 데이터 커버리지 사전 진단

1. `_workspace/00_input/run_config.json` 작성 — data-contracts의 스키마. 사용자가 범위를 지정하지 않으면 MVP 기본값: sectors_scope = [정보기술, 산업재, 헬스케어, 에너지·전력, 커뮤니케이션], max_etf_per_theme=5, deep_score_etf_per_theme=3, selected_themes_count=3, **output_scope는 첫 실행이면 "pilot"**(산출물 4종 축소 — etf_candidates.md는 final_etf_decision.md에 압축 포함), 이후 실행은 "full". `delivery_formats` 기본값은 `["pdf"]`이며, 인터랙티브 탐색은 html, 짧은 공유 이미지는 png, 후편집은 docx를 추가한다. `structure_gate_thresholds`(AUM·거래대금·스프레드·괴리율·상장기간 최소 기준)는 data-contracts의 잠정 기본값을 넣고 MVP 결과에 따라 조정한다. slug_map을 이때 확정한다.
2. **사전 커버리지 진단** → `_workspace/00_coverage_precheck.md`: 주요 데이터 원천(거시 지표, 국내/미국 ETF 정보, 보유종목, 재무·가격 데이터)에 WebSearch/WebFetch 표본 조회를 각 1회 수행해 접근 가능 여부를 기록한다. 핵심 원천이 막혀 있으면 사용자에게 알리고 범위 축소(예: KR만) 여부를 결정한 뒤 진행한다. 이 진단이 최종 data_coverage.md의 "사전 진단" 섹션이 된다.

### Phase 2: 시장 환경 진단
`Agent(subagent_type: "market-regime-analyst", model: "opus")` 단일 호출. 프롬프트에 run_config 경로와 출력 경로를 명시.

### Phase 3: 섹터 점수화
`Agent(subagent_type: "sector-scorer", model: "opus")`. 01 완료 후 실행. 완료 시 selected_sectors(3~5개)를 확인 — 2개 이하면 사용자에게 경고 후 진행.

### Phase 4: 테마 발굴 (팬아웃)
선정 섹터마다 `Agent(subagent_type: "theme-discoverer", model: "opus", run_in_background: true)`를 **단일 메시지에서 병렬 호출**. 프롬프트에 담당 섹터와 출력 slug를 명시.

### Phase 4.5: 근거 수집 대상 사전 필터 (오케스트레이터 직접 수행)
03 파일들을 읽고 섹터당 상위 `evidence_shortlist_per_sector`(기본 3)개 테마를 고른다. 필터 기준: impact=high 우선 → etf_investable=true 필수 → data_availability 높은 순. run_config의 우선 테마 목록과 겹치면 가점. 선정 테마의 `shortlisted`를 true로 갱신하고 slug_map에 테마 slug를 추가한다. (전 테마 30~50개에 깊은 근거 수집은 비용 대비 무의미하므로 여기서 9~15개로 좁힌다 — 탈락 테마도 05의 rejected에 사유와 함께 남는다.)

### Phase 5: 근거 수집 (팬아웃)
shortlisted 테마마다 `theme-evidence-collector` 병렬 호출 (테마당 1, 동시 실행 최대 6개 — 초과분은 배치 분할).

### Phase 6: 핵심 테마 3개 선정
`theme-ranker` 단일 호출. 완료 후 selected가 3개 미만이면 사유를 확인하고 그대로 진행 (억지 충원 금지).

### Phase 7: ETF 후보 발굴 (팬아웃)
선정 테마마다 `etf-candidate-finder` 병렬 호출.

### Phase 8: 밸류체인 매핑 (팬아웃)
모든 후보 ETF마다 `value-chain-mapper` 병렬 호출 (동시 최대 6, 배치 분할). 실패한 ETF는 1회 재시도 후 후보에서 제외하고 기록.

### Phase 8.5: 심층 스코어링 대상 필터 (오케스트레이터 직접 수행)
07 파일들의 purity_pct 기준으로 테마당 상위 `deep_score_etf_per_theme`(기본 3)개만 Phase 9로 보낸다. 단, 유형 다양성을 위해 purity 최상위가 아니어도 대표지수형/혼합형 1개는 비교군으로 포함 가능. 제외 ETF는 11 단계에서 "심층 분석 미수행"으로 표기된다.

### Phase 9: 3축 스코어링 (팬아웃 × 3)
대상 ETF마다 `theme-structure-scorer`, `holdings-financial-scorer`, `holdings-valuation-scorer` 3개를 병렬 호출 (ETF 3개면 9개 에이전트 — 동시 최대 6, 배치 분할). 세 스코어러는 서로의 산출물을 참조하지 않는다.

### Phase 10: 후보 비교 + ETF 구조·거래 하드 게이트
`etf-evaluator` 단일 호출 (전 스코어 파일 완료 후 — 배리어). 비교표 산출과 함께 ETF별 구조·거래 하드 게이트(pass/conditional/hold/low_priority)를 판정한다 — 3축이 좋아도 상품 구조·거래 품질 문제는 점수로 상쇄되지 않는다.

### Phase 11: Decision Gate
`decision-gate` 단일 호출. 판정 순서: 커버리지 게이트 → 구조·거래 하드 게이트 → 3축 등급 게이트 → 명시적 리스크 게이트 → 최종 상태 확정.

### Phase 12: 리포트 생성
`report-generator` 단일 호출 → `_workspace/13_reports/`에 output_scope에 따라 4종(pilot) 또는 5종(full). final_etf_decision.md에는 "투자 판단 가능성" 섹션이 반드시 포함된다.

### Phase 13: QA & 컴플라이언스 (생성-검증 루프)
1. `qa-compliance-guard` 호출. output_scope=pilot이면 1차 파일럿 acceptance test 15문항도 함께 실행된다.
2. verdict=fix_required면 fix_instructions를 포함해 `report-generator` 재호출 → QA 재호출. **최대 2회 반복.**
3. 2회 후에도 미통과면 리포트 상단에 "QA 미통과 항목 존재 + 목록"을 표기하고 진행.

### Phase 13.5: UI·일회성 보고서 전달 레이어 (순차 4단계 + 생성-검증 루프)

리서치 QA 통과 후 실행. **이 레이어는 리서치 판단을 새로 만들지 않는다** — 상류 결과의 시각적 표현물일 뿐이다. 세 에이전트 모두 `etf-ui-render` 스킬을 따른다.

1. **13.5a**: `ui-payload-builder` 호출 → `_workspace/15_ui/ui_payload.json` + audit. analysis.json에서 화면용 데이터를 추출하는 유일한 지점.
2. **13.5b**: `html-mock-renderer` 호출 → `_workspace/15_ui/html/` (discovery_index + finalist별 etf_{ticker} + compare + 인쇄용 report.html + render_notes). 렌더러는 ui_payload.json만 소비한다 (analysis.json 직접 읽기 금지).
3. **13.5c**: `ui-render-qa` 호출 → `_workspace/16_ui_render_qa.json`. verdict=fix_required면 fix_instructions로 html-mock-renderer(payload 문제면 ui-payload-builder) 재호출 → 재검수. **최대 2회.** 2회 후 미통과면 HTML 상단에 "UI QA 미통과 항목 존재" 배너 표기 후 진행.
4. **13.5d**: QA 통과 후 `delivery_formats`에 따라 `.claude/skills/etf-ui-render/scripts/export_report.py`를 실행한다. PDF·DOCX는 `report.html`, PNG는 짧은 요약인 `discovery_index.html`만 원본으로 사용한다. `--check` 결과 필요한 로컬 도구가 없으면 형식을 가짜로 만들지 말고 HTML을 보존한 뒤 완료 보고에 누락 사유를 명시한다.

부분 재실행: "UI만 다시" 요청이면 13.5a부터 (상류 산출물 재사용), "HTML만 다시"면 13.5b부터, "PDF/이미지/Word만 다시"면 QA 통과한 기존 HTML을 사용해 13.5d만 실행한다.

### Phase 14: 완료
1. `_workspace/13_reports/` 산출물을 `output/{run_date}/`로, `_workspace/15_ui/`의 ui_payload.json·html/*·render_notes.md와 `_workspace/16_ui_render_qa.md`를 `output/{run_date}/ui/`로 복사한다. 선택한 PDF·PNG·DOCX는 `output/{run_date}/deliverables/`에 복사한다.
2. `_workspace/` 보존 (감사 추적).
3. 사용자 보고: 최종 후보와 판단 상태 요약, 데이터 부족·신뢰도 낮음 영역, QA 결과, 바로 공유할 deliverable 경로. 마지막에 피드백 기회 제공: "결과나 워크플로우에서 개선할 부분이 있나요?"

## 에이전트 호출 프롬프트 규칙

모든 호출 프롬프트에 반드시 포함: (1) 담당 에이전트 정의 파일이 자동 로드되므로 그 지침을 따르라는 지시, (2) 담당 대상(섹터/테마/ETF)과 slug, (3) 절대 경로 기준 입력 파일 목록과 출력 파일 경로, (4) 부분 재실행이면 기존 산출물 경로 + 사용자 피드백.

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 에이전트 1개 실패 | 1회 재시도. 재실패 시: 팬아웃 단위(섹터/테마/ETF 1개)면 해당 단위 제외 후 진행 + 리포트에 누락 명시. 단일 단계(01/02/05/11/12)면 파이프라인 중단하고 사용자 보고 |
| 팬아웃 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| 산출물 계약 위반 (JSON 파싱 실패, 필수 키 누락) | 해당 에이전트에 위반 내용을 명시해 1회 재호출 |
| 데이터 충돌 | 삭제하지 않고 출처 병기, data_coverage에 기록 |
| QA 루프 2회 초과 | 미통과 항목 표기 후 산출 (위 Phase 13) |
| 커버리지 게이트 다수 발동 | 정상 동작이다 — "판단 보류"가 늘어나는 것이 올바른 결과. 등급을 만들어내려 재시도하지 않는다 |

## 테스트 시나리오

### 정상 흐름
1. 사용자: "지금 시장에서 볼만한 ETF 후보 발굴해줘" → Phase 0 (초기 실행) → Phase 1 (run_config + 사전 진단)
2. Phase 2~3: 시장 진단 → 섹터 3~5개 선정
3. Phase 4~6: 섹터별 테마 10개 → 사전 필터 → 근거 수집 → 핵심 테마 3개
4. Phase 7~9: 테마별 ETF 3~5개 → 밸류체인 매핑 → 테마당 3개 심층 3축 스코어링
5. Phase 10~13: 비교 + 구조·거래 게이트 → Decision Gate → 리포트(scope별 4~5종) → QA 통과(+pilot acceptance)
6. 예상 결과: `output/{run_date}/`에 산출물, 최종 후보 1~3개가 4단계 상태로 분류되고 final_etf_decision.md에 투자 판단 가능성 섹션 존재

### 에러 흐름
1. Phase 9에서 ETF X의 holdings-financial-scorer가 재무 데이터 커버리지 40%로 등급 null 반환
2. 오케스트레이터는 재시도하지 않는다 (게이트 발동은 정상) → 11에서 X의 재무 축 null → 12에서 X는 규칙에 따라 "판단 보류"
3. 리포트에 "X: 재무 데이터 커버리지 부족으로 판단 보류, 재검토 조건: 구성종목 재무 데이터 확보" 명시

### 부분 재실행 흐름
1. 사용자: "최종 리포트 톤만 다시 다듬어줘" → Phase 0에서 `_workspace/` 감지 + 부분 수정 판정 → Phase 12부터 재실행 (report-generator에 피드백 전달) → Phase 13 QA → 완료
