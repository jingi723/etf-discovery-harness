# 데이터 커버리지 리포트 (2026-07-05)

- 실행: run2-us-fmp (2차 실행 — 미국 ETF 중심 재평가, FMP 보강)
- 기준일(run_date): 2026-07-05 / 생성일: 2026-07-05
- 범위(output_scope): full (5종)

> 본 자료는 투자 추천이 아니며 정보 제공 목적입니다. 최종 투자 판단의 책임은 투자자 본인에게 있습니다.

이 리포트는 새 분석을 하지 않으며, 00~12 산출물의 커버리지·소스·부족 데이터를 그대로 취합해 정리한 것입니다.

---

## 1. 사전 진단 결과 (00_coverage_precheck.md)

1차 파일럿 사전 진단에서 확인된 구조적 한계와, run2에서 FMP 도입으로 해소된 부분을 함께 정리합니다.

| 데이터 영역 | 프로빙 대상 | 1차 진단 결과 | run2 변화 |
|------------|------------|--------------|-----------|
| 거시 지표 | FRED·TradingEconomics·재무부 | 접근 가능 (10Y 4.48~4.49%) | 동일 재사용 |
| 미국 ETF 발행사 직접 페이지 | ishares.com 등 | 403 차단 (WebFetch 불가) | 여전히 차단 — 벤더/FMP 경유 |
| 미국 ETF 보유종목 | stockanalysis.com / FMP `etf/holdings` | 벤더 경유 확보 (secondary) | **FMP로 6종 재검증 대상 전부 100% 비중합 확보** (27/33/52/50/126/83종목) |
| 미국 ETF 기본정보 | FMP `etf/info` | — | AUM·총보수·상장일·평균거래량 확보 |
| 구성종목 재무·배수 | FMP `ratios-ttm`·`income-statement` | 벤더 경유 (secondary) | 배치 수집으로 전 종목 확보 |
| 스프레드·괴리율·추적오차 | — | 미확보 (병목) | **FMP 미제공 — 여전히 미확보** |

판정: **US 진행 — 1차의 최대 약점(보유종목·재무 커버리지)이 FMP로 해소.** 잔여 병목은 거래 품질 3종(스프레드·괴리율·추적오차)으로, 구조·거래 게이트의 conditional 상한이 지속됩니다.

## 2. 영역별 커버리지

| 영역 | 확보율·상태 | 부족 항목 |
|------|------------|-----------|
| 시장 환경 | 확보 (confidence high) | 미국·한국 6월 CPI 확정치(미공개), 크레딧 스프레드(IG/HY), 6월 고용·2분기 GDP 세부치 |
| 섹터 점수 | 정보기술·산업재 각 6/6 기준 100% (confidence medium) | 산업재 자금흐름 정량치, KR 상장 섹터 상대강도(미국 대표 ETF로 대체) |
| 테마 후보 | 정보기술 12개·산업재 12개 발굴, shortlist 6개 evidence 확보 | 탈락 테마 ETF 순도(purity) 정량치(심층 미진행) |
| ETF 후보(구조·규모) | 14종 전부 AUM·총보수·상장일·평균거래량·구조 boolean 확보 (FMP secondary) | — |
| 구조·거래 품질 | **미확보 — 14종 전부 스프레드·괴리율·추적오차·추적차이 null** | bid-ask 스프레드, premium/discount, tracking error/difference (FMP 미제공) |
| 보유종목 매핑 | 14종 전부 holdings_coverage 99.98~100% (FMP holdings 100%) | — |
| 재무(09) | 심층 11종 커버리지 81.4~100% (전부 60% 게이트 통과) | 심층 미수행 3종(PPA·XSD·HACK) 3축 null |
| 가격(10) | 심층 11종 커버리지 66.5~100% (최저 GRID 66.5%·CIBR 68.9%) | 상위 15종 캡으로 일부 ETF 60~80% 밴드(SOXQ·SOXX·CIBR·GRID), 선행 PER 전 종목 미확보(TTM만) |

## 3. 소스 품질 요약

| 티어 | 주요 사용처 |
|------|-------------|
| **primary** | 거시 정책·금리(BOK·BLS·White House·CBOE/FRED VIX), SEC 8-K 공시(RTX·GD·CRWD·PANW·ZS ARR·백로그), SIPRI·NATO·IEA·DOE 정책/수요 |
| **secondary** | **FMP(structured vendor) — 미국 ETF holdings·info·ratios·재무·배수의 1차 소스**, FactSet·Goldman·Deloitte 리서치, stockanalysis.com·Morningstar 벤더 |
| **tertiary** | AI 매도 이벤트(CNN/CNBC), 일부 시장규모(C4ISR 등), stale 스프레드(ITA 2024-08 0.05%) — 단독 근거로 미사용 |

- **FMP 정책 준수**: FMP는 secondary(structured vendor)로 기록하며, FMP 데이터만으로 구조·거래 게이트를 자동 pass 처리하지 않습니다(run_config `fmp_policy`).

### 출처 충돌 (source_conflicts)

| 항목 | 충돌 값 | 해소 |
|------|---------|------|
| CIBR 총보수 | 0.58%(FMP secondary) vs 0.60%(tertiary 웹요약) | FMP 0.58% 채택 — tertiary 단독 근거 불가. Decision Gate 영향 없음 |
| USD/KRW 수준 | 1,528.92 vs 1,543.05 (동일 벤더 스냅샷 차) | 밴드(1,529~1,543)로 표기 |
| 미국 10Y 금리 | 4.49%(연구자료) vs 4.48%(사전진단 표본) | 인용 시점차 — 4.49% 채택 |
| SK하이닉스 Q1 2026 매출 | 52.58조 vs 27.8조 (04 ai-semi) | 미해소 — coverage.missing 기록, 등급 근거 미사용 |

## 4. 신뢰도 낮은 영역 (confidence=low / 주의 항목)

- **가격(10) 축 커버리지 60~80% 밴드**: SOXQ(78.3%)·SOXX(77.7%)·CIBR(68.9%)·GRID(66.5%)는 상위 15종 캡으로 ETF 누적 비중이 60~80% 구간이며, 자기 과거 배수 시계열·선행 PER 미확보로 confidence low~medium. 등급은 유효하나 표본이 상대적으로 얇습니다.
- **SHLD AUM 상류 불일치**: 06_etf_candidates_defense.json은 $7.27B(FMP etf/info), 12_decision.json 게이트 서술은 "$10.5B급"으로 기재 — 상류 간 값이 다릅니다. 본 리포트는 FMP 원천인 06의 $7.27B를 채택하고 이 불일치를 여기 기록합니다.
- **환헤지 실효 노출**: SHLD·IHAK은 currency_hedged=false만 확인되고 실효 환노출 규모(해외자산 비중·통화별) 정량치는 미확보.
- **AI 소프트웨어 evidence verification_status 필드 부재**: 부정 근거 8건은 실재하나 명문 표기 없음(어차피 5위 탈락).

## 5. 분석 불가 영역 (등급 null 처리 + 판단 영향)

| 항목 | 처리 | 판단에 준 영향 |
|------|------|----------------|
| 구조·거래 품질 3종(스프레드·괴리율·추적오차) | 14종 전부 null | 구조·거래 하드 게이트가 어떤 후보도 **pass로 확정할 수 없어 최종 상태의 상한이 '조건부 검토'에 묶임**. 게이트 실패가 아니라 데이터 수집 한계(FMP 미제공)의 정상 반영이며, FMP 단독 pass 금지 정책에 부합 |
| PPA·XSD·HACK 3축(08/09/10) | 심층 미수행 → null | 3종 전부 종합 판단 불가 → **판단 보류** 확정 |
| SHLD CSG(0.38%)·ITA 현금 3라인 등 | 개별 종목 null | 비중 작아 등급 영향 제한적 (커버리지 99%대 유지) |
| 탈락 테마 ETF 순도 | 미산정(심층 미진행) | 테마 선정에는 영향 없음 |

**요약**: run2의 핵심 성과는 FMP holdings 보강으로 1차에서 커버리지 미달/심층 미수행으로 판단 보류였던 XAR·ITA·SOXX·GRID 4종이 전부 조건부 검토로 상향된 것입니다. 다만 스프레드·괴리율·추적오차는 1차와 마찬가지로 여전히 미확보라 '검토 가능' 상한이 열리지 않은 점은 동일합니다.
