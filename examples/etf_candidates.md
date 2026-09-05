# ETF 후보군 리포트 (2026-07-05)

- 실행: run2-us-fmp / output_scope: full
- 기준일(run_date): 2026-07-05 / 생성일: 2026-07-05

> 본 자료는 투자 추천이 아니며 정보 제공 목적입니다. 최종 투자 판단의 책임은 투자자 본인에게 있습니다.

이 리포트는 06(후보 기본정보·구조)·07(밸류체인 매핑·순도)·11(비교표) 산출물을 조립한 것으로, 새 분석을 하지 않습니다. 선정 3개 테마(방산·AI 반도체·사이버보안)의 후보 4종씩 12종 + 차점 테마(AI 전력 인프라) 재검증 트랙 2종 = **총 14종**을 다룹니다.

모든 ETF는 미국 상장(NASDAQ/NYSE Arca/NYSE/Cboe BZX)이며, 기본정보 소스는 FMP(secondary, structured vendor)입니다.

---

## 1. 테마별 후보군 (06_etf_candidates)

### 방산 (defense)

| 티커 | 이름 | 시장 | 운용사 | 추종지수 | 유형 | 보유수 | AUM | 총보수 |
|------|------|------|--------|----------|------|:--:|------|:--:|
| SHLD | Global X Defense Tech ETF | NASDAQ | Global X | Global X Defense Tech Index | 밸류체인 혼합형 | 50 | USD 7.27B | 0.50% |
| XAR | SPDR S&P Aerospace & Defense ETF | NYSE | State Street SPDR | S&P A&D Select (수정 등가중) | 고분산형 | 48 | USD 6.49B | 0.35% |
| ITA | iShares U.S. Aerospace & Defense ETF | NYSE | iShares | 미국 A&D 지수(시총 가중) | 순수 테마형 | 49 | USD 14.72B | 0.38% |
| PPA | Invesco Aerospace & Defense ETF | NASDAQ | Invesco | SPADE Defense Index | 대표지수형 | 62 | USD 8.55B | 0.58% |

### AI 반도체 (ai-semi)

| 티커 | 이름 | 시장 | 운용사 | 추종지수 | 유형 | 보유수 | AUM | 총보수 |
|------|------|------|--------|----------|------|:--:|------|:--:|
| SMH | VanEck Semiconductor ETF | NASDAQ | VanEck | MVIS US Listed Semiconductor 25 | 빅테크 중심형 | 26 | USD 68.82B | 0.35% |
| SOXX | iShares Semiconductor ETF | NASDAQ | iShares | ICE Semiconductor Index | 대표지수형 | 30 | USD 40.97B | 0.34% |
| SOXQ | Invesco PHLX Semiconductor ETF | NASDAQ | Invesco | PHLX Semiconductor Sector (SOX) | 대표지수형 | 31 | USD 2.56B | 0.19% |
| XSD | SPDR S&P Semiconductor ETF | NYSE Arca | State Street SPDR | S&P Semiconductor Select | 고분산형 | 48 | USD 3.32B | 0.35% |

### 사이버보안 (cyber)

| 티커 | 이름 | 시장 | 운용사 | 추종지수 | 유형 | 보유수 | AUM | 총보수 |
|------|------|------|--------|----------|------|:--:|------|:--:|
| CIBR | First Trust Nasdaq Cybersecurity ETF | NASDAQ | First Trust | Nasdaq CTA Cybersecurity | 순수 테마형 | 30 | USD 14.01B | 0.58% |
| BUG | Global X Cybersecurity ETF | NASDAQ | Global X | Indxx Cybersecurity Index | 순수 테마형(시총가중) | 31 | USD 1.23B | 0.50% |
| HACK | Amplify Cybersecurity ETF | NYSE Arca | Amplify | Nasdaq ISE Cyber Security Select | 고분산형(동일가중) | 23 | USD 2.35B | 0.60% |
| IHAK | iShares Cybersecurity and Tech ETF | NYSE Arca | iShares | NYSE FactSet Global Cybersecurity | 글로벌 혼합형 | 35 | USD 0.98B | 0.47% |

### AI 전력 인프라·전력설비 (power) — 차점 테마 재검증 트랙

> 이 테마는 run2 랭킹 4위로 탈락(차점)했습니다. 아래 2종은 사용자 지정 재검증 대상으로 심층 스코어링만 수행했으며, **최종 후보(finalist) 자격은 없습니다.**

| 티커 | 이름 | 시장 | 운용사 | 추종지수 | 유형 | 보유수 | AUM | 총보수 |
|------|------|------|--------|----------|------|:--:|------|:--:|
| GRID | First Trust NASDAQ Clean Edge Smart Grid Infrastructure | NASDAQ | First Trust | Nasdaq Clean Edge Smart Grid | 고분산형 | 96 | USD 11.87B | 0.56% |
| AIPO | Defiance AI & Power Infrastructure ETF | NASDAQ | Defiance | MarketVector US AI & Power Infra | 밸류체인 혼합형 | 83 | USD 0.93B | 0.69% |

> 참고: SHLD AUM은 06(FMP etf/info) 기준 $7.27B이며, 12_decision.json은 "$10.5B급"으로 기재해 상류 간 불일치가 있습니다(data_coverage.md에 기록). 본 표는 FMP 원천값을 채택했습니다.

## 2. 밸류체인 비중과 테마 순도 (07_valuechain)

보유종목 기준으로 각 ETF를 테마 밸류체인에 분류한 순도(purity)입니다. holdings_coverage는 14종 전부 99.98~100%입니다.

| 티커 | 테마 | 순도(purity) | 최대 체인 (비중) | 비테마 비중 |
|------|------|:--:|------|:--:|
| SHLD | 방산 | **97.73%** | 완성 무기체계 OEM 62.08% | 2.3% |
| XAR | 방산 | 92.79% | 방산 부품·엔진·항전 39.85% | 7.2% |
| PPA | 방산 | 44.73% | 완성 OEM 27.17% (민항 혼합 36.6%) | ~55% |
| ITA | 방산 | 41.96% | 완성 OEM 30.01% (민항 혼합 54.47%) | ~58% |
| SMH | AI 반도체 | 82.04% | 팹리스 설계 45.54% | 17.94% |
| SOXQ | AI 반도체 | 76.87% | 팹리스 설계 39.15% | 23.06% |
| SOXX | AI 반도체 | 76.41% | 팹리스 설계 38.93% | 23.48% |
| XSD | AI 반도체 | 25.41% | 팹리스 설계 19.32% | ~75% |
| BUG | 사이버보안 | **99.89%** | 네트워크·엔드포인트 45.09% | 0.0% |
| IHAK | 사이버보안 | 84.10% | 네트워크·엔드포인트 35.41% | 15.9% |
| HACK | 사이버보안 | 75.81% | 네트워크·엔드포인트 42.70% | ~24% |
| CIBR | 사이버보안 | 58.42% | 네트워크·엔드포인트 38.84% | 41.17% |
| GRID | AI 전력 | 56.74% | 송배전 기기 38.88% | 43.3% |
| AIPO | AI 전력 | 54.20% | 발전설비 17.10% | ~45% |

핵심 관찰: 순도 최고는 방산 SHLD(97.73%)·사이버 BUG(99.89%)이며, ITA(41.96%)·PPA(44.73%)는 민항 혼합, CIBR(58.42%)은 광의 IT 혼합, XSD(25.41%)는 등가중 소형주로 순도 최하입니다.

## 3. 구조·거래 특성 (06 structure_trading)

14종 전부 레버리지/인버스·단일종목 레버리지·합성/스왑·옵션 전략이 **모두 없음**(일반 롱온리 패시브, FMP 확인)이며, 보유종목 투명성은 전부 daily입니다.

| 티커 | 상장일 | 상장기간 | 구조 안전성 | 환헤지 | 스프레드/괴리율/추적오차 |
|------|--------|:--:|:--:|:--:|:--:|
| SHLD | 2023-09-11 | 약 2.8년 | 안전 | false(유럽 방산 환노출) | **전부 미확보(null)** |
| XAR | 2011-09-28 | 약 14년 | 안전 | false | 미확보 |
| ITA | 2006-05-01 | 약 20년 | 안전 | false | 미확보 |
| PPA | 2005-10-26 | 약 20년 | 안전(non-diversified) | false | 미확보 |
| SMH | 2011-12-20 | 약 14년 | 안전 | false | 미확보 |
| SOXX | 2001-07-10 | 약 25년 | 안전 | false | 미확보 |
| SOXQ | 2021-06-11 | 약 4년 | 안전 | false | 미확보 |
| XSD | 2006-01-31 | 약 20년 | 안전 | false | 미확보 |
| CIBR | 2015-07-06 | 약 11년 | 안전 | false | 미확보 |
| BUG | 2019-10-25 | 약 5.7년 | 안전 | false | 미확보 |
| HACK | 2014-11-11 | 약 11.6년 | 안전 | false | 미확보 |
| IHAK | 2019-06-11 | 약 6년 | 안전(글로벌 환노출) | false | 미확보 |
| GRID | 2009-11-16 | 약 16년 | 안전 | false | 미확보 |
| AIPO | 2025-07-24 | 약 11.5개월 | 안전(이력 최단) | false | 미확보 |

**공통 병목**: bid-ask 스프레드·괴리율(premium/discount)·추적오차·추적차이가 14종 전부 null(FMP 미제공)입니다. run_config는 FMP 데이터만으로 구조·거래 게이트를 자동 pass 처리하지 않도록 규정하므로, 이 3종 미확보가 전 후보의 게이트 상한을 conditional에 묶는 원인입니다(자세한 게이트 판정은 final_etf_decision.md 4절).

## 4. 유동성·집중도·비용 (06 + 11)

| 티커 | AUM | 평균 거래대금(FMP) | 유동성 | top10 집중도 | 총보수 |
|------|------|------|:--:|:--:|:--:|
| SHLD | 7.27B | 약 $124M/일 | high | 62.2% | 0.50% |
| XAR | 6.49B | 약 $63M/일 | medium | 30.6% | 0.35% |
| ITA | 14.72B | 약 $213M/일 | high | 75.7% | 0.38% |
| PPA | 8.55B | 약 $45M/일 | medium | 55.4% | 0.58% |
| SMH | 68.82B | 약 $6.16B/일 | high | 69.5% | 0.35% |
| SOXX | 40.97B | 약 $5.11B/일 | high | 60.7% | 0.34% |
| SOXQ | 2.56B | 약 $247M/일 | high | 60.9% | 0.19% |
| XSD | 3.32B | 약 $77.9M/일 | medium | 28.2% | 0.35% |
| CIBR | 14.01B | 약 $148.9M/일 | high | 57.4% | 0.58% |
| BUG | 1.23B | 약 $42.8M/일 | medium | 60.8% | 0.50% |
| HACK | 2.35B | 약 $13.97M/일 | low | 51.7% | 0.60% |
| IHAK | 0.98B | 약 $10.6M/일 | low | 45.1% | 0.47% |
| GRID | 11.87B | 약 $148.7M/일 | high | 57.9% | 0.56% |
| AIPO | 0.93B | 약 $38.9M/일 | medium | 55.1% | 0.69% |

- 최저 비용: SOXQ 0.19% / 최고 비용: AIPO 0.69%.
- 최고 집중도: ITA 75.7%(민항 대형주)·SMH 69.5%(NVDA/TSMC) / 최저 집중도(분산 우위): XSD 28.2%·XAR 30.6%·IHAK 45.1%.
- 유동성 하한 근접(min $5M/일): IHAK 약 $10.6M/일(경계선), HACK 약 $13.97M/일.

## 5. 데이터 신뢰도 (06~07 + 11)

- **확보**: 14종 3축 등급(심층 11종)·순도·top10 집중도·총보수·AUM·거래대금·상장일·구조 boolean·유동성 판정. 보유종목 매핑 커버리지 99.98~100%.
- **미확보**: 14종 전부 bid-ask 스프레드·괴리율·추적오차·추적차이(FMP 미제공). PPA·XSD·HACK 3축(심층 미수행).
- **비교표 confidence**: medium. 심층 11종의 3축 final_grade·coverage_pct는 08~10 원본과 전수 대조해 100% 일치(불일치 0).
- **출처 충돌**: CIBR 총보수 0.58%(FMP) vs 0.60%(tertiary) — FMP 채택, Decision Gate 영향 없음.
