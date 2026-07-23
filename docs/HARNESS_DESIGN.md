# ETF 발굴 에이전트 하네스 — 설계 문서

기준일: 2026-07-23 · 버전 1.3 (v1.1: 데이터 소스·하드 게이트·파일럿 / v1.2: UI 변환 레이어 / v1.3: GitHub 공개 구조, 환경 변수 기반 API 설정, 인쇄용 report.html과 PDF·요약 PNG·DOCX 전달 형식)

이 문서는 하네스의 설계 요약이다. 실행 정의의 원본(source of truth)은 `.claude/agents/`, `.claude/skills/`이며, 이 문서와 충돌하면 원본이 우선한다.

---

## 1. 전체 하네스 목적

ETF 투자 고수의 프로세스 — "시장 환경 판단 → 유리한 섹터 → 섹터 내 테마 → 핵심 테마 3개 → ETF 후보군 → 3축 검증 → 4단계 분류" — 를 에이전트 파이프라인으로 재현한다. 사용자가 특정 ETF를 찍지 않아도 후보를 좁혀가며, ETF를 추천하는 것이 아니라 **투자자가 판단할 수 있도록 후보와 근거·리스크를 함께 제공**한다.

## 2. 발굴 모드 정의 (Phase 2~7)

시장 환경에서 출발해 후보 공간을 좁히는 하향식 탐색.

- 입력: run_config (섹터 범위, MVP 우선 테마, 시장 범위 KR/US, 산출물 범위, 전달 형식)
- 흐름: 시장 진단 → 섹터 6기준 등급화(3~5개 선정) → 섹터당 테마 10개 발굴 → 사전 필터(섹터당 3개) → 테마별 evidence pack → 핵심 테마 3개 선정 → 테마별 ETF 후보 3~5개 발굴
- 산출: 후보 ETF 9~15개와 각 단계의 근거·탈락 사유

## 3. 검증 모드 정의 (Phase 8~13)

발굴된 ETF 후보를 기존 ETF 분석 화면의 3축 구조로 검증하는 상향식 검증.

- 밸류체인 매핑: 이름이 아니라 **실제 보유종목** 기준으로 ETF가 담은 밸류체인 비중과 테마 순도 계산
- 3축 스코어링 (상호 독립):
  - **테마 구조** — ETF가 담은 밸류체인 구성의 구조적 설득력 (전망 데이터 전용)
  - **재무 상태** — 구성종목의 현재 재무 데이터 (전망 금지)
  - **가격 적정성** — 현재 재무 대비 가격 수준 (성장성 맥락 병기)
- **ETF 구조·거래 하드 게이트**: 3축과 별개로 상품 자체의 구조(레버리지/인버스·합성·옵션 전략)와 거래 품질(AUM·거래대금·스프레드·괴리율·추적오차·상장기간)을 판정 — 3축이 좋아도 점수로 상쇄되지 않음
- 비교 → Decision Gate(4단계 분류) → 리포트 → QA·컴플라이언스 검수(파일럿 acceptance test 포함)

## 4. 에이전트 팀 구성

실행 모드: **서브 에이전트 (파이프라인 + 팬아웃 복합 패턴)**

선택 이유: (1) 단계 간 데이터가 엄격한 JSON 파일 계약으로 흐르는 결정적 파이프라인, (2) 3축 스코어러는 축 오염 방지를 위해 상호 참조가 금지되므로 팀 통신이 원칙 위반을 유발, (3) QA↔리포트는 오케스트레이터 중재 생성-검증 루프(최대 2회)로 충분. 팬아웃 구간(섹터별/테마별/ETF별)은 단일 메시지 병렬 호출로 처리한다.

| # | 에이전트 | 파일 |
|---|---------|------|
| 1 | Orchestrator | `.claude/skills/etf-discovery-orchestrator/SKILL.md` (스킬로 구현 — 하네스 표준) |
| 2 | Market Regime | `.claude/agents/market-regime-analyst.md` |
| 3 | Sector Scoring | `.claude/agents/sector-scorer.md` |
| 4 | Theme Discovery | `.claude/agents/theme-discoverer.md` |
| 5 | Theme Evidence Collector | `.claude/agents/theme-evidence-collector.md` |
| 6 | Theme Factor Ranker | `.claude/agents/theme-ranker.md` |
| 7 | ETF Candidate Finder | `.claude/agents/etf-candidate-finder.md` |
| 8 | Value Chain Mapper | `.claude/agents/value-chain-mapper.md` |
| 9 | Theme Structure Scorer | `.claude/agents/theme-structure-scorer.md` |
| 10 | Holdings Financial Scorer | `.claude/agents/holdings-financial-scorer.md` |
| 11 | Holdings Valuation Scorer | `.claude/agents/holdings-valuation-scorer.md` |
| 12 | ETF Candidate Evaluator | `.claude/agents/etf-evaluator.md` |
| 13 | Decision Gate | `.claude/agents/decision-gate.md` |
| 14 | Report Generator | `.claude/agents/report-generator.md` |
| 15 | QA & Compliance Guard | `.claude/agents/qa-compliance-guard.md` |
| 16 | UI Payload Builder | `.claude/agents/ui-payload-builder.md` |
| 17 | HTML Mock Renderer | `.claude/agents/html-mock-renderer.md` |
| 18 | UI Render QA | `.claude/agents/ui-render-qa.md` |

공유 스킬 4종: `etf-grading-standards`(등급 표준 + weighted_grade.py), `etf-evidence-standards`(근거 수집 표준), `etf-compliance-rules`(금지 표현 + check_forbidden.py + 4단계 분류 규칙), `etf-report-templates`(산출물 5종 템플릿).

## 5. 각 에이전트 역할

각 에이전트 정의 파일에 8개 요구 항목이 매핑되어 있다: 역할(# 헤더+페르소나), 입력(시작 시 필수 로드), 출력(출력 섹션 — 파일 경로+계약), 필요한 데이터(작업 절차 내 명시), 사용하는 스킬(필수 로드 목록), 실패 시 처리(실패·데이터 부족 처리), 데이터 부족 시 처리(동일 섹션 — null+missing+게이트), 다음 에이전트로 넘기는 형식(데이터 계약 참조+협업 섹션).

한 줄 요약:

- **market-regime-analyst**: 10개 매크로 항목을 체크리스트 기반으로 수집, 유리/불리 섹터 유형 도출. 예측 금지, 관찰만.
- **sector-scorer**: 섹터를 6기준 루브릭으로 등급화(동일가중 스크립트 평균), 3~5개 선정.
- **theme-discoverer**: 섹터당 테마 최소 10개, 긍정·부정 요인 필수, ETF 실존 확인. 후보 공간 확장이 임무(선별은 하류).
- **theme-evidence-collector**: 체크리스트 먼저 → 데이터 수집. 긍정/부정 양방향, negative 0건은 미완성.
- **theme-ranker**: 최소 선정 조건(8개 중 2개 이상) 게이트 후 7기준으로 evidence pack 심사, 핵심 3개 선정 + 전 탈락 테마 사유(9개 유형으로 유형화). 새 검색 없이 입력만 사용.
- **etf-candidate-finder**: 테마당 실존 확인된 ETF 3~5개, 유형 다양성 확보 + 구조·거래 데이터(상장일·레버리지/합성 여부·스프레드·괴리율·추적오차 등 14항목) 수집.
- **value-chain-mapper**: 보유종목 85% 커버 목표로 밸류체인 분류, 순도 계산. 이름 불신, 종목만 신뢰.
- **theme-structure-scorer**: 체인별 구조 등급 × 비중. 전망 데이터 전용 (축 분리).
- **holdings-financial-scorer**: 종목별 현재 재무 등급 × 비중. 전망·밸류에이션 금지 (축 분리).
- **holdings-valuation-scorer**: 종목별 배수를 업종/자기 과거/성장률 3맥락으로 등급화 × 비중. "비싸다" 단정 금지.
- **etf-evaluator**: 3축+순도+집중도+비용+유동성 비교표 + **ETF 구조·거래 하드 게이트 판정**(pass/conditional/hold/low_priority), 규칙 기반 verdict_hint. 새 분석 금지.
- **decision-gate**: 4단계 분류 규칙 재검증, 최종 1~3개 확정, 재검토 조건 명시. 0개도 유효한 결과.
- **report-generator**: 01~12 조립만. 상류에 없는 문장 금지, 자체 컴플라이언스 검사 후 제출.
- **qa-compliance-guard**: 경계면 교차 비교(리포트 ↔ 원본 JSON 대조, 등급 재계산 표본 검사) + 금지 표현 스크립트 검사.

## 6. 전체 워크플로우

```
Phase 0  컨텍스트 확인 (초기/부분 재실행/새 실행 판별)
Phase 1  run_config 작성 + 데이터 커버리지 사전 진단
Phase 2  시장 환경 진단          [단일]
Phase 3  섹터 점수화 → 3~5개     [단일]
Phase 4  테마 발굴               [팬아웃: 섹터당 1]
Phase 4.5 근거 수집 사전 필터     [오케스트레이터: 섹터당 3개]
Phase 5  근거 수집               [팬아웃: 테마당 1]
Phase 6  핵심 테마 3개 선정       [단일]
Phase 7  ETF 후보 발굴           [팬아웃: 테마당 1]
Phase 8  밸류체인 매핑            [팬아웃: ETF당 1]
Phase 8.5 심층 스코어링 필터      [오케스트레이터: 순도 기준 테마당 3개]
Phase 9  3축 스코어링            [팬아웃: ETF당 3 에이전트, 상호 독립]
Phase 10 후보 비교               [단일, 배리어]
Phase 11 Decision Gate          [단일]
Phase 12 리포트 5종 생성          [단일]
Phase 13 QA·컴플라이언스          [생성-검증 루프, 최대 2회]
Phase 13.5 UI·보고서 전달 레이어   [payload → 탐색·인쇄 HTML → UI QA → PDF/PNG/DOCX 내보내기]
Phase 14 output/{run_date}/ (+ui/+deliverables/) 복사 + 보고 + 피드백 수집
```

## 7. 데이터 계약

`.claude/skills/etf-discovery-orchestrator/references/data-contracts.md`에 전량 정의. 핵심:

- **공통 봉투**: 모든 JSON 산출물은 `{artifact, as_of_date, generated_by, sources[], source_conflicts[], confidence, coverage{available, missing, impact_of_missing}, payload}`. sources 없는 산출물은 무효.
- **소스 품질 메타데이터**: sources의 각 항목은 8필드 — source_name, source_type, url_or_reference, as_of_date, retrieved_at, reliability_tier(primary/secondary/tertiary/unsupported), used_for, notes. unsupported는 등급 산정 사용 금지.
- **파일 배치**: `_workspace/` 아래 `01_market_regime.json` ~ `14_qa_report.json`, 번호가 Phase 의존 순서.
- **단계별 payload**: 01(시장), 02(섹터), 03(테마), 04(evidence), 05(선정 테마), 06(ETF 후보 + structure_trading 14항목), 07(밸류체인), 08/09/10(3축 공통 스코어 형태), 11(비교표 + structure_trading_gate), 12(결정 + gate_trace), 14(QA + pilot_acceptance).

### 데이터 소스 우선순위 정책

`etf-evidence-standards` 스킬의 `references/source-priority.md`에 데이터 영역별(ETF 기본정보/보유종목/재무/가격/테마) 1·2·3순위 출처를 정의. 요지: 거래소·운용사 공식·공시가 1순위(primary), Morningstar·ETF.com·데이터 벤더가 2순위(secondary), 일반 포털·뉴스는 3순위(tertiary — 이벤트·보조 근거만), 블로그·커뮤니티·출처 불명은 사용 금지(unsupported). 보유종목은 운용사 daily holdings 최우선. 단일 뉴스만으로 테마 구조 등급을 만들지 않는다.

재무·가격·미국 ETF 보유종목은 환경 변수 `FMP_API_KEY`가 있으면 FMP의 구조화 JSON을 웹 검색보다 먼저 사용한다. 긴 검색 결과·HTML 파싱을 줄여 컨텍스트 토큰과 숫자 파싱 오류를 낮추지만, FMP는 secondary 출처다. 공식 공시·거래소·운용사 자료가 있으면 primary 출처를 우선하며, 키가 없으면 공식 웹 소스로 폴백한다. 키 값은 저장소·로그·산출물에 기록하지 않는다.

**소스 충돌 처리 6원칙**: ① 공식 출처 우선 ② 최신 기준일 우선 ③ 보유종목은 daily holdings 최우선 ④ 충돌 수치는 삭제하지 않고 source_conflicts에 기록 ⑤ 핵심 등급에 영향 주면 confidence 하향 ⑥ 설명 문장에서 충돌 사실을 숨기지 않음.

## 8. 데이터 커버리지 진단 방식

- **사전 진단** (Phase 1): 거시/ETF/보유종목/재무/가격 데이터 원천에 표본 조회 → `00_coverage_precheck.md`. 핵심 원천 불가 시 범위 축소 결정.
- **단계별 진단**: 모든 에이전트가 봉투의 `coverage`에 확보/부족 항목과 부족의 영향을 기록.
- **게이트**: 커버리지 60% 미만 → 등급 null "분석 제한", 60~80% → 등급 유지 + confidence low.
- **취합**: report-generator가 전 단계 coverage를 `data_coverage.md`와 analysis.json의 `data_coverage`로 취합. QA가 누락 여부 표본 대조.
- 부족 시 등급을 억지로 만들지 않는다 — "판단 보류"가 늘어나는 것이 올바른 동작이다.

## 9. 섹터 점수화 방식

6기준(매크로 적합성, 이익 모멘텀, 시장 대비 흐름, 가격 부담, 리스크·과열도, 수급·포지셔닝)에 A~D 루브릭으로 기준별 등급 부여 → `weighted_grade.py` 동일가중 평균 → 섹터 등급. 근거·리스크를 데이터 인용으로 기록, 상위 3~5개 선정. 기준 3개 이상 null인 섹터는 등급 보류·선정 제외.

## 10. 테마 후보 발굴 방식

섹터당 최소 10개, 테마마다 11개 필드(테마명/섹터/긍정/부정/밸류체인/핵심 지표 후보/데이터 확보 가능성/ETF 투자 가능성/대표 ETF/설명 가능성/신뢰도+영향도). 부정 요인이 빈 테마는 미완성 처리. MVP 우선 테마 10종은 해당 섹터에서 반드시 후보에 포함. 억지로 10개를 채우지 않고 못 채우면 부족을 기록.

## 11. 핵심 테마 3개 선정 방식

**최소 선정 조건 게이트 (점수보다 먼저)**: 선정 테마는 아래 8개 중 최소 2개 이상을 데이터로 만족해야 한다 — ① 수요 증가 데이터 ② 공급 부족/병목 데이터 ③ CapEx·수주·백로그 실물 투자 데이터 ④ 관련 ETF 후보 3개 이상 ⑤ ETF 보유종목-밸류체인 연결 가능 ⑥ 리스크 요인 1개 이상 설명 가능 ⑦ 가격 부담/과열 평가 가능 ⑧ 출처가 primary/secondary 이상. 예외: ETF 3개 미만의 좁은 테마는 "후보 ETF 부족" 표시 조건으로 잔류 가능하되 최종 ETF 단계에서 감점.

그 위에 7기준(구조적 성장성/실적 연결성/데이터 확보 가능성/ETF 투자 가능성/설명 가능성/가격 부담/리스크 관리 가능성)을 evidence pack 기반으로 등급화 → 스크립트 종합 → 상위 3개. ETF 투자 가능성 C 이하는 순위 무관 탈락. 부정 근거 미확보("검증 불충분") 테마는 리스크 관리 가능성 C 이하 처리.

**필수 출력 8항목**: 왜 선택 / 근거 데이터 / 부족 데이터 / 리스크 / 탈락 테마 대비 우선인 이유 / 연결 ETF 후보 / 데이터 신뢰도 / ETF 투자 가능성.

**탈락 사유 유형화**: "점수 낮음" 금지. 9개 유형(데이터 부족 / ETF 후보 부족 / 가격 부담 과도 / 실적 연결성 부족 / 수요·병목 구조 불명확 / 리스크 과다 / 설명 가능성 낮음 / 테마가 너무 넓거나 모호함 / ETF가 테마를 순수하게 담기 어려움) + 구체 사유.

## 12. ETF 후보군 추출 방식

테마 키워드·밸류체인으로 KR/US 시장별 검색 → 운용사 공식 페이지 등에서 실존+기본 정보 확인 → 테마당 3~5개. 6유형(순수 테마형/밸류체인 혼합형/빅테크 중심형/대표지수형/고분산형/액티브형) 분류, 유형 다양성 우선. 실존 미확인 ETF는 후보 불가.

## 13. ETF 후보 평가 방식

1. **밸류체인 매핑**: 보유종목(비중 85% 커버 목표) → 체인 분류 → 체인 비중 + 테마 순도.
2. **3축 스코어링**: 각 축이 `항목 등급 × 비중`을 스크립트로 가중평균. 축 분리 원칙 — 테마 구조=전망 전용, 재무=현재 데이터 전용, 가격=배수+3맥락 해석.
3. **ETF 구조·거래 하드 게이트**: 14항목 체크(AUM/거래대금/스프레드/괴리율/추적오차/추적차이/총보수·실질비용/상장기간/레버리지·인버스/단일종목 레버리지/합성·스왑/커버드콜·옵션/LP 품질/환헤지) → pass/conditional/hold/low_priority. 수치 기준은 run_config의 `structure_gate_thresholds`(잠정 기본값, MVP 후 조정). 강한 보류·제외 조건: 레버리지/인버스가 일반 후보로 분석됨, 단일종목 레버리지, AUM·거래대금 미달, 스프레드 과도, 괴리율 반복적 확대, 추적오차 과대, 구조 설명 부족한 합성/파생, 상장 기간 과소, 보유종목 불투명.
4. **비교표**: 3축 + 순도 + top10 집중도 + 총보수 + 유동성 + 추적 품질 + 구조·거래 게이트 + 신뢰도. 순도 40% 미만은 "테마 순도 낮음" 명시.

## 14. 최종 Decision Gate

판정 순서: **① 데이터 커버리지 게이트 → ② ETF 구조·거래 하드 게이트 → ③ 3축 등급 게이트 → ④ 명시적 리스크 게이트 → ⑤ 최종 상태 확정** (먼저 걸리는 것 적용):

1. **판단 보류**: 3축 중 커버리지 60% 미만/등급 null, 필수 보유종목 데이터 부족, ETF 구조·거래 데이터 부족(게이트 hold), 핵심 근거 충돌
2. **우선순위 낮음**: 3축 중 2개 이상 C+ 이하, 테마 순도 40% 미만, 구조·거래 게이트 심각 문제(low_priority — 레버리지/인버스/단일종목 레버리지 등 부적합 구조 포함)
3. **조건부 검토**: 3축 중 1개 C+ 이하, 가격 부담 또는 상위 종목 쏠림, 유동성·스프레드 확인 필요, 추적 품질 데이터 부족, 명시적 리스크 존재
4. **검토 가능**: 3축 모두 B- 이상 + 전 축 커버리지 70% 이상 + 구조·거래 게이트 pass + 미해결 치명 리스크 없음

최종 후보 1~3개 + 남은 이유/제외 이유/재검토 조건/대안 탐색 방향 + 게이트 판정 추적(gate_trace). "검토 가능 ≠ 매수 추천" 상시 병기. 후보 0개도 유효한 결과.

## 15. 산출물 파일 구조

```
_workspace/                     # 중간 산출물 (보존 — 감사 추적)
├── 00_input/run_config.json
├── 00_coverage_precheck.md
├── 01~12_*.json                # 단계별 산출물
├── 13_reports/                 # 최종 4~5종 초안
├── 14_qa_report.json
├── 15_ui/
│   ├── ui_payload.json
│   ├── ui_payload_audit.md
│   └── html/                   # 탐색 페이지 + 인쇄용 report.html
└── 16_ui_render_qa.json/.md
output/{run_date}/              # QA 통과본
├── sector_theme_discovery.md   # 시장→섹터→테마 발굴 결과
├── etf_candidates.md           # full scope에서만 별도 파일
├── final_etf_decision.md       # 최종 후보 3축+게이트+판단 상태
├── analysis.json               # 감사·변환용 구조화 데이터
├── data_coverage.md            # 커버리지·소스 품질
├── ui/
│   ├── ui_payload.json
│   ├── html/                   # discovery_index, ETF 상세, compare, report
│   └── ui_render_qa.md
└── deliverables/
    ├── final_report.pdf        # 기본
    ├── summary.png             # 요청 시, discovery_index 요약만
    └── final_report.docx       # 요청 시, 후편집용
```

**산출물 범위 (run_config.output_scope)**: 1차 실행은 `pilot` — 필수 4종(data_coverage, sector_theme_discovery, final_etf_decision, analysis.json)만 생성하고 etf_candidates.md 내용은 final_etf_decision.md의 후보 비교 섹션에 압축 포함한다. 2차 실행부터 `full` — etf_candidates.md를 별도 산출물로 분리.

### UI·일회성 보고서 전달 레이어 (v1.3)

리서치 QA **이후** Phase 13.5에서 상류 결과를 탐색 UI와 공유 가능한 일회성 보고서로 변환한다. **이 레이어는 리서치 판단을 새로 만들지 않는다** — 등급·판단 상태·수치·설명은 QA 통과 값을 그대로 표현한다.

analysis.json을 직접 렌더러에 넣지 않고 `ui_payload.json`으로 경량화한 뒤 목업(`etf-ui-render/assets/mock.html`)에 바인딩한다:

```
analysis.json → ui_payload.json → 탐색 HTML + report.html → UI QA → PDF/요약 PNG/DOCX
```

- **ui-payload-builder**: analysis.json에서 화면용 데이터를 추출하는 유일한 지점. 등급·판단 상태를 그대로 복사하고, 데이터 부족은 data_warnings, 원본 위치는 source_trace로 보존한다.
- **html-mock-renderer**: ui_payload.json만 소비. 모바일 탐색 페이지와 단일 인쇄 문서 report.html을 정적으로 생성한다. 외부 리소스 0, mock 값 제거, 기준일·면책 필수.
- **ui-render-qa**: HTML ↔ ui_payload ↔ analysis.json 3중 교차 대조, check_html.py 기계 검사, 모바일·인쇄 레이아웃과 추적성을 검수한다. fix 루프는 최대 2회다.
- **export_report.py**: QA 통과 HTML만 변환한다. PDF는 일회성 전체 보고서 기본, PNG는 discovery_index 요약 공유용, DOCX는 후편집 요청 시에만 사용한다. PDF·PNG는 Chrome/Chromium, DOCX는 pandoc 또는 macOS textutil을 사용하며 의존성을 자동 설치하지 않는다.

`run_config.delivery_formats` 기본값은 `["pdf"]`다. HTML은 다른 전달 형식의 원본이므로 항상 보존한다. 도구가 없으면 HTML을 최종 폴백으로 남기고 누락 형식과 사유를 완료 보고에 명시한다.

**final_etf_decision.md 10섹션 순서**: ① 최종 후보 요약 ② 후보별 판단 상태 ③ 후보별 3축 등급 ④ ETF 구조·거래 게이트 결과 ⑤ 남은 이유 ⑥ 제외된 이유 ⑦ 재검토 조건 ⑧ 대안 탐색 방향 ⑨ **투자 판단 가능성** ⑩ 데이터 한계와 면책.

**투자 판단 가능성 섹션 (⑨, 필수)**: "이 정보만으로 판단 가능한 것 / 아직 판단하기 어려운 것(사용자 조건 필요) / 추가로 확인해야 할 데이터 / 다음 판단 행동 / 이 결과가 매수 추천이 아닌 이유" 5개 하위 항목 + 안내 문구("이 결과는 ETF 후보의 구조와 리스크를 판단하기 위한 참고 정보입니다. 실제 투자 실행 여부는 투자 기간, 투자 금액, 손실 허용도, 보유 포트폴리오 등을 함께 고려해야 합니다."). 최종 리포트가 실제 투자 판단에 어디까지 도움이 되는지 스스로 명확히 말하는 장치다.

## 16. JSON Schema 개요

analysis.json 최상위 20키 (전체 스키마는 data-contracts.md 5절):
`meta`(면책·output_scope 포함), `market_regime`, `sector_scores`, `theme_candidates`, `theme_evidence`, `selected_themes`, `etf_candidates`, `value_chain_mapping`, `theme_structure_scores`, `financial_scores`, `valuation_scores`, `decision_gate_result`, **`etf_structure_trading_gate`**(ETF별 status/checks/reasons/impact), **`source_quality_policy`**(primary/secondary/tertiary 사용 목록·source_conflicts·unsupported_claims), **`investment_judgment_readiness`**(can_decide/cannot_decide/next_actions/requires_investor_fit_check/disclaimer), **`investor_fit_required`**(항상 true), **`pilot_acceptance_summary`**(passed/failed/needs_revision), `data_coverage`, `explanation`, `sources`. 상류 payload를 재가공 없이 넣어 원본 추적을 유지 — WebView/이미지 카드/MTS 위젯이 필요한 키만 골라 렌더링하는 구조.

## 17. 실패·데이터 부족 처리

- 에이전트 실패: 1회 재시도 → 팬아웃 단위는 제외+누락 명시, 단일 단계는 중단+보고
- 계약 위반(파싱 실패/키 누락): 위반 내용 명시해 1회 재호출
- 데이터 부족: 추정 금지, null+missing+영향 기록, 커버리지 게이트로 등급 보류
- 데이터 충돌: 삭제 금지, 출처 병기
- QA 미통과 2회: 미통과 항목 표기한 채 산출
- 후보 0개/테마 3개 미만: 유효한 결과로 그대로 보고 (억지 충원 금지)

## 18. QA·컴플라이언스 체크리스트

(`etf-compliance-rules` 스킬에 정의, 스크립트 검사 포함 — A/B/C 15항목 + D 파일럿 15문항)

**A. 컴플라이언스·형식**: ① 금지 표현 0건(`check_forbidden.py`, 21종) ② 모든 최종 결론이 4단계 상태 중 하나 ③ 모든 등급에 기준일·출처·신뢰도·커버리지 표기 ④ 면책 문구 존재 ⑤ 사용자 조건이 필요한 판단(기간·비중·계좌·세금 적합성)을 ETF 자체 판단으로 단정하지 않음

**B. 데이터 정합성**: ⑥ 축 분리(테마 구조↔현재 재무 혼입 검사) ⑦ 등급 정합성(weighted_grade.py 재계산 대조, 표본) ⑧ 데이터 소스 우선순위 준수 — reliability_tier 구분 기재, unsupported 미사용 ⑨ 출처 충돌이 source_conflicts에 기록·표출 ⑩ evidence pack에 긍정·부정 근거 모두 존재(부정 0건 → "검증 불충분" 표시 확인) ⑪ 핵심 테마 3개의 최소 선정 조건 판정 기록 존재

**C. 게이트·구조**: ⑫ ETF 구조·거래 하드 게이트가 전 후보에 적용되고 Decision Gate에 반영 ⑬ final_etf_decision.md에 투자 판단 가능성 섹션 존재(5개 하위 항목+안내 문구) ⑭ analysis.json 필수 키 20개(신규 5키 포함)+파싱 ⑮ coverage.missing → data_coverage.md 반영 누락 없음

**D. 1차 파일럿 acceptance test** (output_scope=pilot 시): 15문항 — 섹터-시장 환경 연결 납득 / 테마 10개 비허구성 / 테마별 긍정·부정 근거 / 핵심 3개 데이터 설명 / 탈락 사유 구체성 / ETF 실존 확인 / 비교 가능한 유형 분류 / 보유종목 기준 매핑 / 3축 비혼입 / 구조·거래 게이트 적용 / 4단계 결론 / 투자 판단 가능성 섹션 / data_coverage 유용성 / 금지 표현 없음 / analysis.json UI 변환 가능성 — 결과를 `pilot_acceptance_summary`에 기록.

## 19. MVP 구현 순서

1. **1차 (파이프라인 골격 검증, output_scope=pilot)**: 섹터 2개(정보기술·산업재), 테마 근거 수집 섹터당 2개, ETF 테마당 3개, 심층 스코어링 테마당 2개로 축소해 전체 파이프라인 1회 완주. 산출물은 4종으로 축소(etf_candidates.md는 final_etf_decision.md에 압축 포함).

   **1차 실행 목적**: ① 전체 파이프라인 완주 확인 ② 데이터 커버리지 진단이 실제로 유용한지 확인 ③ 테마 후보 10개가 납득되는지 확인 ④ 핵심 테마 3개 선정이 데이터로 설명되는지 확인 ⑤ ETF 후보가 실존하고 비교 가능한지 확인 ⑥ Decision Gate 결과가 투자 추천이 아니라 판단 상태로 끝나는지 확인.

   **1차 파일럿 acceptance test**: 실행 후 QA & Compliance Guard가 18절 D의 15문항 체크리스트를 판정해 `pilot_acceptance_summary`(passed/failed/needs_revision)를 기록 — 통과 여부가 2차 진행의 게이트다.
2. **2차 (범위 확장, output_scope=full)**: 섹터 5개·우선 테마 10종 전체, 기본 파라미터로 실행. etf_candidates.md를 별도 산출물로 분리. `structure_gate_thresholds` 기본값을 1차 결과 기반으로 조정.
3. **3차 (품질 루프)**: 실행별 QA 위반·게이트 발동 패턴을 보고 루브릭/에이전트 정의를 갱신 (CLAUDE.md 변경 이력 기록)
4. **4차 (데이터 소스 안정화)**: 반복 검색되는 원천(거래소·운용사·재무 사이트)을 source-priority.md에 표준 소스 목록으로 보강

## 20. 이후 확장 방법 (MTS/WebView + Investor Fit)

### Investor Fit Agent (추후 확장 — MVP 1차에서는 포함하지 않음)

목적: ETF 자체 검증 결과를 **사용자의 투자 조건**과 비교해 실제 투자 실행 적합성을 판단하는 별도 단계. 현재 하네스의 Decision Gate는 "상품 자체가 투자 후보로 검토 가능한가"만 판단하며 "검토 가능"은 매수 추천이 아니다 — 실행 판단에 필요한 사용자 맥락은 이 에이전트가 담당한다.

- 입력: 투자 기간, 투자 금액, 투자 목적, 손실 허용도, 투자 경험, 기존 보유 ETF, 기존 보유 종목, 계좌 유형, 세금 고려 여부
- 출력(4단계): 내 조건에 적합 / 소액·분할 조건부 적합 / 판단 보류 / 부적합
- 접점: analysis.json의 `decision_gate_result` + `investment_judgment_readiness`를 입력으로 받아 Decision Gate **이후**에 동작하는 별도 게이트로 설계. `investor_fit_required: true`가 이 단계의 필요성을 표시한다.
- 안내 문구: "현재 하네스는 ETF 자체의 후보 적합성을 평가합니다. 실제 투자 실행 여부는 사용자 조건 기반 Investor Fit Gate를 통해 별도로 판단해야 합니다."

### MTS/WebView 확장

- **analysis.json이 확장의 접점이다.** WebView/이미지 카드/MTS 위젯은 이 파일만 소비하면 된다 — 하네스 수정 불필요.
- **WebView**: `explanation` + 3축 등급 + `decision_gate_result`로 기존 ETF 분석 화면의 3축(테마 구조/재무 상태/가격 적정성) UI에 직접 매핑. 등급 옆에 coverage·confidence 배지 표기.
- **이미지 카드**: ETF 1개당 `explanation.{ticker}` + axes 등급으로 카드 1장 렌더링.
- **MTS 위젯**: `decision_gate_result.finalists`를 후보 리스트 위젯으로, 탭하면 WebView 상세로 연결.
- **정기 실행**: 오케스트레이터를 스케줄 실행(예: 주 1회)하고 `output/{run_date}/` 히스토리로 판단 상태 변화 추적 — `recheck_conditions` 충족 여부를 다음 실행에서 자동 확인하는 것이 자연스러운 다음 단계.
- 컴플라이언스: UI 표출 문구는 analysis.json의 explanation만 사용 (QA 통과본) — 프론트에서 문구를 재생성하지 않는 것이 원칙.
