# 데이터 소스 우선순위 정책

## 등록된 데이터 API: FMP (Financial Modeling Prep)

재무·가격·ETF 데이터가 필요하면 웹 검색보다 **FMP API를 먼저 사용**한다 (secondary/벤더 티어, 구조화 데이터라 수치 파싱 오류가 적고 기준일이 명확함).

- **API 키**: 환경 변수 `FMP_API_KEY`로 전달한다. 저장소의 `.env.example`을 `.env`로 복사해 로컬에서 관리할 수 있지만, 키 값은 산출물·로그·소스코드에 절대 기록하지 않는다. 환경 변수가 없으면 FMP를 건너뛰고 아래 출처 우선순위에 따라 공식 웹 소스를 사용한다.
- **엔드포인트**: `https://financialmodelingprep.com/stable/{endpoint}?symbol={심볼}&apikey=$FMP_API_KEY` — 반드시 `stable` 경로 사용 (`/api/v3/` 레거시는 이 키에서 차단됨).
- **검증된 엔드포인트** (2026-07-05 확인):

| endpoint | 용도 | 사용하는 축 |
|----------|------|------------|
| `profile?symbol=X` | 시총·베타·섹터·기업 개요 | 공통 |
| `income-statement?symbol=X&limit=N` | 손익계산서 (연/분기 `period=quarter`) | 재무 상태(09) |
| `balance-sheet-statement`, `cash-flow-statement` | 재무상태표·현금흐름 (FCF·부채) | 재무 상태(09) |
| `ratios-ttm?symbol=X` | TTM 마진·ROE·부채비율 등 배수 일괄 | 재무(09)·가격(10) |
| `key-metrics-ttm?symbol=X` | PER·EV/EBITDA·FCF yield 등 | 가격 적정성(10) |
| `etf/holdings?symbol=X` | **ETF 보유종목·비중** (미국 상장) | 밸류체인 매핑(07) |
| `etf/info?symbol=X` | ETF AUM·보수·상장일 | ETF 후보(06)·구조 게이트 |
| `quote?symbol=X` | 현재가·거래량 | 공통 |

- **커버리지 확인 결과**: 미국 주식·미국 상장 ETF 전반 지원. **한국 개별종목은 `005930.KS` 형식으로 프로필·재무 지원**. 한국 상장 ETF의 보유종목(`463250.KS` 등)은 **미지원(빈 응답)** — KR ETF holdings는 기존 방식(발행사 페이지·검색)을 유지한다.
- 빈 배열 응답은 "커버리지 없음"이다 — 다른 심볼 형식 1회 재시도 후 missing으로 확정.
- sources 기록 시: source_name "FMP(Financial Modeling Prep)", source_type "vendor", reliability_tier "secondary", as_of_date는 응답 데이터의 date 필드 사용.

데이터 영역별로 어떤 출처를 우선하는지 정의한다. 1순위 = primary, 2순위 = secondary, 3순위 = tertiary. 티어 규칙: 같은 데이터가 여러 출처에 있으면 항상 높은 순위 출처를 채택하고, 낮은 순위 출처는 교차 확인용으로만 쓴다.

## ETF 기본정보 (이름·지수·보수·AUM·운용방식)

| 순위 | 출처 |
|------|------|
| 1 (primary) | 거래소 공식 데이터(KRX 등), 운용사 공식 ETF 페이지, 운용사 fact sheet, 투자설명서/prospectus |
| 2 (secondary) | ETF.com, Morningstar, 운용사 공식 데이터 feed, 신뢰 가능한 금융 데이터 벤더 |
| 3 (tertiary) | 일반 금융 포털, 뉴스 기사 |
| 사용 금지 | 블로그/커뮤니티 |

## ETF 보유종목

| 순위 | 출처 |
|------|------|
| 1 (primary) | 운용사 daily holdings, 공식 PCF, 운용사 fact sheet, 거래소 공시 |
| 2 (secondary) | 데이터 벤더, Morningstar, ETF.com |
| 3 (tertiary) | 일반 금융 포털 |
| 사용 금지 | 출처 불명 데이터 |

보유종목은 운용사 daily holdings가 항상 최우선이다 (구성이 매일 바뀔 수 있으므로).

## 구성종목 재무 데이터

| 순위 | 출처 |
|------|------|
| 1 (primary) | 기업 공시(DART, SEC EDGAR), 거래소/감독기관 공시, 재무 데이터 벤더 |
| 2 (secondary) | 신뢰 가능한 금융 데이터 API, 운용사·리서치 자료 |
| 3 (tertiary) | 일반 웹 검색 결과 — 보조 근거로만 사용 |

## 가격·밸류에이션 데이터

| 순위 | 출처 |
|------|------|
| 1 (primary) | 데이터 벤더, 거래소, 공식 재무 데이터, 기업 공시 |
| 2 (secondary) | 신뢰 가능한 금융 포털, Morningstar, Bloomberg/Refinitiv/FactSet를 인용한 자료 |
| 3 (tertiary) | 뉴스 기사 — 이벤트 근거로만 사용 |

## 테마 데이터 (수요·병목·CapEx·정책)

| 순위 | 출처 |
|------|------|
| 1 (primary) | 정부/기관 자료, 산업 리포트, 기업 공시, 기업 IR 자료, 신뢰 가능한 리서치 자료 |
| 2 (secondary) | 운용사 리서치, 산업협회 자료, 시장 데이터 벤더 |
| 3 (tertiary) | 뉴스 — 이벤트 근거로만 사용 |

**단일 뉴스만으로 테마 구조 등급을 만들지 않는다.** 뉴스는 "이런 이벤트가 있었다"의 근거일 뿐, 구조 판단에는 primary/secondary 데이터가 최소 1건 필요하다.

## 소스 충돌 처리

출처 간 수치·사실이 충돌하면:

1. 공식 출처(primary)가 우선한다.
2. 같은 티어면 기준일(as_of_date)이 최신인 출처를 우선한다.
3. ETF 보유종목은 운용사 daily holdings를 최우선으로 한다.
4. 수치가 서로 다르면 삭제하지 말고 봉투의 `source_conflicts`에 기록한다 (양쪽 값 + 출처 + 채택 근거).
5. 충돌이 핵심 등급에 영향을 주면 해당 항목 confidence를 낮춘다.
6. 설명 문장에서 충돌 사실을 숨기지 않는다 — "출처 간 수치 차이가 있어 {채택 출처} 기준으로 표기" 형태로 드러낸다.
