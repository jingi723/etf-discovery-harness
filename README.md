# ETF Discovery Harness

시장 환경에서 출발해 **섹터 → 테마 → ETF 후보 → 검증** 순서로 후보를 좁히고, 근거·리스크·데이터 한계를 함께 정리하는 Claude Code 하네스입니다.

17개 전문 에이전트와 6개 스킬이 시장 진단, 테마 근거 수집, ETF 구조·보유종목 분석, 3축 평가, 컴플라이언스 QA, 모바일 UI와 일회성 보고서 생성을 단계별로 수행합니다. 결과는 매수·매도 추천이 아니라 `검토 가능 / 조건부 검토 / 판단 보류 / 우선순위 낮음`의 네 상태로 분류됩니다.

> 이 프로젝트의 산출물은 정보 제공과 후보 검토 보조를 위한 것이며 투자 자문이나 매수·매도 추천이 아닙니다.

## 특징

- **하향식 발굴**: 시장 환경에서 유리한 섹터와 데이터로 검증 가능한 테마를 먼저 좁힙니다.
- **보유종목 기반 검증**: ETF 이름이 아니라 실제 보유종목과 비중으로 테마 순도와 밸류체인을 확인합니다.
- **독립된 3축 평가**: 테마 구조, 현재 재무, 가격 적정성을 서로 오염시키지 않고 별도로 평가합니다.
- **구조·거래 하드 게이트**: 레버리지·합성 구조, AUM, 거래량, 스프레드, 괴리율, 추적 품질을 점수와 별도로 판정합니다.
- **근거 추적**: 모든 중간 산출물에 기준일, 출처, 신뢰도, 데이터 커버리지를 기록합니다.
- **여러 전달 형식**: 인터랙티브 HTML을 원본으로 만들고, 기본 PDF·요약 PNG·편집용 DOCX를 용도에 맞게 내보냅니다.

## 구조

```text
.
├── .claude/
│   ├── agents/                         # 17개 전문 에이전트 정의
│   └── skills/                         # 6개 실행 방법론과 오케스트레이터
│       ├── etf-discovery-orchestrator/ # 메인 진입점
│       ├── etf-evidence-standards/     # 출처·근거 표준
│       ├── etf-grading-standards/      # 등급 계산 규칙과 스크립트
│       ├── etf-compliance-rules/       # 금지 표현·판정 상태 규칙
│       ├── etf-report-templates/       # 최종 리포트 계약
│       └── etf-ui-render/              # WebView·PDF·PNG·DOCX 변환과 검수
├── docs/
│   └── HARNESS_DESIGN.md               # 전체 아키텍처와 데이터 계약 요약
├── .env.example                         # 선택 API 키 입력 템플릿
├── .gitignore                           # 키·실행 산출물·캐시 제외
├── CLAUDE.md                            # 하네스 트리거 포인터와 변경 이력
├── LICENSE
└── README.md
```

실행 중 생성되는 `_workspace*/`와 `output/`은 감사·결과 산출물이며 Git 추적 대상에서 제외됩니다.

## 에이전트 팀

| 단계 | 에이전트 | 역할 |
|---|---|---|
| 시장·섹터 | `market-regime-analyst`, `sector-scorer` | 시장 관찰과 섹터 등급화 |
| 테마 발굴 | `theme-discoverer`, `theme-evidence-collector`, `theme-ranker` | 테마 후보 확장, 양방향 근거 수집, 핵심 테마 선정 |
| ETF 후보 | `etf-candidate-finder`, `value-chain-mapper` | 실존 ETF 확인, 보유종목 기반 밸류체인·순도 계산 |
| 독립 평가 | `theme-structure-scorer`, `holdings-financial-scorer`, `holdings-valuation-scorer` | 테마 구조·현재 재무·가격 적정성 3축 평가 |
| 판정·리포트 | `etf-evaluator`, `decision-gate`, `report-generator`, `qa-compliance-guard` | 비교, 하드 게이트, 4단계 판정, 리포트 QA |
| UI·전달 | `ui-payload-builder`, `html-mock-renderer`, `ui-render-qa` | QA 통과 데이터를 WebView HTML과 PDF·PNG·DOCX 원본으로 변환·검수 |

## 워크플로우

```text
시장 진단
  → 섹터 점수화
  → 테마 발굴·근거 수집
  → 핵심 테마 선정
  → ETF 후보 발굴
  → 보유종목·밸류체인 매핑
  → 테마 구조 / 재무 / 가격 3축 평가
  → ETF 구조·거래 하드 게이트
  → 4단계 Decision Gate
  → 리포트 QA
  → 모바일 WebView·인쇄용 HTML QA
  → PDF / 요약 PNG / DOCX 내보내기
```

세부 Phase, 파일 계약, 등급·커버리지 기준은 [하네스 설계 문서](docs/HARNESS_DESIGN.md)를 참고하세요.

## 사용 방법

### 요구 사항

- [Claude Code](https://claude.ai/code)
- Python 3 — 등급 계산, QA, 보고서 내보내기 실행
- 선택 사항: [Financial Modeling Prep](https://financialmodelingprep.com/) API 키
- PDF·PNG: Chrome 또는 Chromium
- DOCX: pandoc 또는 macOS 기본 `textutil`

### 빠른 시작

```bash
git clone <YOUR_REPOSITORY_URL>
cd etf-discovery-harness
cp .env.example .env
```

`.env`에서 `FMP_API_KEY` 값을 채운 뒤, 같은 터미널 세션에 로드하고 Claude Code를 실행합니다.

```bash
set -a
source .env
set +a
claude
```

API 키 없이도 실행됩니다. 그 경우 공식 운용사·거래소·공시 웹 소스를 사용하며, 확보하지 못한 데이터는 추정하지 않고 커버리지 부족으로 기록합니다.

### API를 연결하는 이유

FMP 같은 구조화 API는 재무제표, 배수, 시세, 미국 ETF 보유종목을 일정한 JSON 형태로 반환합니다. 웹 검색만 사용할 때보다 다음 이점이 큽니다.

- 여러 검색 결과와 긴 HTML 페이지를 읽지 않아도 되어 **컨텍스트 토큰 사용량이 보통 크게 줄어듭니다**.
- 동일 필드를 반복 조회할 수 있어 종목 간 비교가 안정적이고 숫자 파싱 오류가 적습니다.
- 응답의 기준일이 명확해 출처 추적과 데이터 커버리지 계산이 쉬워집니다.
- 미국 종목·미국 ETF 분석의 누락이 줄어 결과 품질이 좋아집니다.

단, API는 공식 공시를 대체하지 않습니다. 하네스는 API를 벤더 출처(secondary)로 취급하고, 운용사·거래소·공시(primary)가 있으면 이를 우선합니다. 키는 `.env`나 `FMP_API_KEY` 환경 변수에만 두며 Git, 로그, 결과 파일에는 넣지 않습니다.

### 요청 예시

- `지금 시장에서 검토할 ETF 후보를 발굴해줘`
- `미국 상장 ETF만 대상으로 다시 실행해줘`
- `테마 선정 단계만 다시 검토해줘`
- `기존 분석으로 PDF 보고서만 다시 만들어줘`
- `메신저에 공유할 요약 이미지도 만들어줘`
- `문구를 고칠 수 있게 Word 파일로 내보내줘`

`etf-discovery-orchestrator`가 초기 실행, 새 실행, 부분 재실행을 구분해 필요한 하류 단계만 수행합니다. 결과 전달 형식을 지정하지 않으면 공유와 보관에 적합한 PDF를 기본으로 만듭니다.

## 결과 형식 선택

| 형식 | 적합한 용도 | 기본 여부 |
|---|---|---|
| PDF | 읽기, 보관, 메일·메신저 공유. 긴 보고서도 페이지로 안정적으로 나뉨 | 기본 |
| HTML | ETF 상세 탐색, 탭·히트맵 상호작용 | 항상 원본 생성 |
| PNG | 휴대폰에서 빠르게 보는 시장·후보 요약 한 장 | 요청 시 |
| DOCX | 사용자가 문구를 수정하거나 사내 Word 양식에 편집 | 요청 시 |

긴 전체 보고서를 한 장 PNG로 만들면 글자가 작아지고 검색도 되지 않으므로, 이미지는 `discovery_index` 요약에만 사용합니다. 일회성 전체 보고서는 PDF가 가장 단순하고 안전합니다. DOCX는 후편집이 실제로 필요할 때만 만듭니다.

내보내기 도구가 준비됐는지 확인할 수 있습니다.

```bash
python3 .claude/skills/etf-ui-render/scripts/export_report.py --check
```

## 산출물

```text
_workspace/                 # 단계별 원본·중간 산출물과 QA 기록
└── 00_input/ ... 16_*.json

output/{run_date}/          # QA 완료 리포트
├── sector_theme_discovery.md
├── etf_candidates.md       # full 모드
├── final_etf_decision.md
├── analysis.json
├── data_coverage.md
├── ui/
│   ├── ui_payload.json
│   ├── html/                  # 탐색 페이지 + 인쇄용 report.html
│   └── ui_render_qa.md
└── deliverables/
    ├── final_report.pdf       # 기본
    ├── summary.png            # 요청 시
    └── final_report.docx      # 요청 시
```

`_workspace*/`와 `output/`에는 실행 시점 데이터가 포함되므로 기본적으로 커밋하지 않습니다.

## 설계 원칙

- 데이터가 없으면 추정하지 않고 등급을 보류합니다.
- 출처 충돌은 삭제하지 않고 양쪽 값과 채택 근거를 남깁니다.
- 공식·최신 출처를 우선하며 기준일과 신뢰도 티어를 함께 기록합니다.
- 점수 계산은 결정적 스크립트가, 설명 생성은 에이전트가 담당합니다.
- `검토 가능`은 매수 추천을 의미하지 않습니다.

## 참고

저장소 공개 구조와 문서 구성은 [revfactory/webtoon-harness](https://github.com/revfactory/webtoon-harness)를 참고했습니다.

## 라이선스

[MIT License](LICENSE)
