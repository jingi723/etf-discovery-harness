# 데이터 소스 우선순위 정책

등록된 API 간 역할 분담: **시세·거래량·캔들·수급(투자주체별)·국내 지수/국채·환율 = 토스증권 Open API 최우선**, **재무제표·밸류에이션 배수·미국 ETF holdings·기업 프로필 = FMP 최우선**. 두 API 모두 웹 검색보다 우선한다.

## 등록된 데이터 API ①: 토스증권 Open API — 시세·수급 최우선

시세·거래량·캔들(차트)·투자자별 매매동향·공매도/신용/대차/프로그램 동향·국내 지수·국채 금리·환율이 필요하면 웹 검색·FMP보다 **토스증권 Open API를 먼저 사용**한다 (KRX·NXT 통합 거래소 데이터 기반, KR·US 종목 실시간성).

- **인증**: 환경 변수 `TOSS_CLIENT_ID`·`TOSS_CLIENT_SECRET` (`.env`). `POST https://openapi.tossinvest.com/oauth2/token`에 `grant_type=client_credentials&client_id=...&client_secret=...` (form-urlencoded) → 이후 모든 호출에 `Authorization: Bearer {access_token}`. 키 값은 산출물·로그·소스코드에 절대 기록하지 않는다.
- **토큰은 client당 1개만 유효** — 재발급하면 이전 토큰이 즉시 무효화된다. 병렬 에이전트가 각자 토큰을 발급하면 서로를 무효화하므로, **토큰을 파일로 캐시해 공유하고 만료 시에만 1회 재발급**한다 (병렬 스코어러 임시 파일 레이스 교훈과 동일 패턴).
- **Rate limit**: 그룹별 15 req/s (`x-ratelimit-*` 헤더). 시세·종목정보는 `symbols` 콤마 구분 최대 200건 배치 조회로 호출 수를 줄인다.
- 응답이 gzip으로 올 수 있다 — curl은 `--compressed` 필수.
- **검증된 엔드포인트** (2026-08-26 확인, base `https://openapi.tossinvest.com/api/v1`, 스펙: `https://openapi.tossinvest.com/openapi-docs/latest/openapi.json`):

| endpoint | 용도 | 커버리지 |
|----------|------|----------|
| `prices?symbols=A,B` | 현재가 (최대 200건 배치) | KR·US |
| `candles?symbol=X&interval=1d\|1m&count=N&adjusted=true` | OHLCV 캔들, 최대 200봉, `before`로 페이지네이션 (`symbol` 단수 주의) | KR·US |
| `orderbook` / `trades` / `price-limits` | 호가·당일 체결·상하한가 | KR·US |
| `stocks?symbols=` / `stocks/all` | 종목 기본정보(시장·상장일·발행주식수·레버리지 배수·거래정지 여부) | KR·US |
| `stocks/{symbol}/investor-trading` | **투자자별 매매동향** — 개인/외국인/기관(7개 세부 breakdown)/기타법인 순매수, 외국인 보유율 | **KR만** |
| `stocks/{symbol}/short-selling` 외 `credit-trades`·`securities-lending`·`program-trades` | 공매도·신용·대차·프로그램매매 동향 | **KR만** |
| `market-indicators/prices`, `market-indicators/{symbol}/candles`, `.../investor-trading` | KOSPI·KOSDAQ 지수, 한국 국채 2~30Y 금리 (카탈로그 8종), 지수 투자자별 매매대금 | KR |
| `exchange-rate?baseCurrency=USD&quoteCurrency=KRW` | 환율 (1분 갱신, 참고용) | KRW↔USD |
| `rankings?type=TOP_GAINERS...&marketCountry=&duration=` | 등락률·거래대금·거래량 랭킹 top100 | KR·US |

- 심볼 형식: KR `005930`, US `AAPL`/`SOXL` — FMP의 `.KS` 접미사 형식과 다르다.
- 수급 계열(investor-trading 등)은 KR 종목만 — US 종목은 400 `unsupported-market`. 당일 기록은 장중 잠정치라 개인·기관 세부가 null일 수 있고 확정치는 당일 저녁 반영.
- **미제공**: 재무제표·밸류에이션 배수·ETF 보유종목·기업 프로필 → FMP 사용(아래). 주문·계좌 API도 있으나 **이 하네스에서 주문 API는 절대 호출하지 않는다.**
- sources 기록 시: source_name "토스증권 Open API", source_type "broker", reliability_tier "secondary"(거래소 데이터 리레이), as_of_date는 응답의 timestamp/date 필드 사용.

## 등록된 데이터 API ②: FMP (Financial Modeling Prep)

재무제표·밸류에이션·미국 ETF holdings·기업 프로필이 필요하면 웹 검색보다 **FMP API를 먼저 사용**한다 (secondary/벤더 티어, 구조화 데이터라 수치 파싱 오류가 적고 기준일이 명확함). 단순 시세·거래량은 토스 API가 우선이다.

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

## 시세·거래량·수급(투자주체별)·지수·환율

| 순위 | 출처 |
|------|------|
| 1 (primary) | 토스증권 Open API, 거래소 공식 데이터(KRX) |
| 2 (secondary) | FMP `quote`, 신뢰 가능한 금융 포털 |
| 3 (tertiary) | 뉴스 기사 — 이벤트 근거로만 사용 |

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

## 실무 주의사항 (2026-09-04 추가)

### 토스 Open API — IP 허용목록
토큰 발급이 403 `access_denied` / `"IP address not allowed"`로 실패하면 **키 문제가 아니라 IP 문제**다. 토스는 개발자센터에 등록된 IP에서만 호출을 허용한다. 네트워크가 바뀌면(테더링·다른 사무실) 재발한다.
- 진단: `curl -s https://api.ipify.org`로 현재 공인 IP 확인 후 등록 여부 대조
- 대응: 자주 쓰는 네트워크의 IP를 미리 등록. 등록 전에는 FMP로 우회

### FMP — 한국 티커 지원 범위 (2026-09-04 검증)
| 대상 | `quote` | `historical-price-eod/full` | `ratios-ttm` | `etf/holdings` |
|------|---------|---------------------------|--------------|----------------|
| 한국 개별종목 (`005930.KS`) | ✅ | ✅ | ✅ | — |
| 한국 ETF (`091230.KS`) | ✅ | ✅ | — | ❌ **빈 응답** |
→ **한국 ETF 구성종목은 FMP·토스 모두 미지원.** 운용사 공식 페이지에서 확보한다(브라우저 자동화 필요 — 대부분 JS 렌더링). 미래에셋 TIGER는 상품 상세 페이지의 "구성종목 보기" 버튼을 눌러야 표가 로드된다.

### 뉴스 수치를 지표로 쓸 때 (필수 확인 5가지)
1. **기사일 ≠ 발표일 ≠ 기준일** — 산출물에는 반드시 **기준일(as-of)**을 적는다
2. **범위 명시** — 지역(미국/대만/중국/글로벌) × 대상(개별기업/서브섹터/산업 전체). 범위가 다르면 대체재로 쓰지 않는다
3. **신선도** — 기준일이 그 지표의 갱신 주기를 넘겨 낡으면 사용 금지(분기 지표는 1분기, 월간은 2개월)
4. **정성 표현 금지** — "high", "strong", "견조"를 점수로 환산하지 않는다. 배경 설명에만
5. **티어** — 1차(연준·SEMI·WSTS·기업 공시/실적발표) > 2차(TrendForce·Counterpoint·SMM 등 벤더) > 3차(일반 뉴스). 3차는 이벤트 발생 사실의 근거로만

**기각 사례**: 반도체 가동률 지표 도입 검토 → TSMC는 정성 표현만, SMIC 93.7%는 중국 기업이라 범위 불일치, 전부 기준일이 6개월 전 → **도입 보류**. FRED(CAPUTLG3344S)는 CSV·WebFetch 모두 403이라 무료 API 키 발급 시 재검토.

### 원자재주 — 스팟 가격을 그대로 대입하지 말 것
원자재 생산기업의 실적은 스팟이 아니라 **계약 비중·실현가격·원가 곡선 위치**가 결정한다.
- 사례(SQM, 2026-09): 리튬 중국 스팟이 1개월 **-10.3%**인데 주가는 20일 **+10.1%**. 원인 — ①2026년 물량 **80%가 이미 계약** ②실현가 **$21.80/kg으로 전분기 +23%**(스팟 $18.14보다 높음) ③원가 Tier 1 **$3~5/kg**이라 가격 하락이 고비용 경쟁자를 먼저 제거
→ 스팟은 방향 참고용. **계약 비중·실현가격·원가 순위를 함께 수집**한다.
