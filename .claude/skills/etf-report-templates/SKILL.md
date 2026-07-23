---
name: etf-report-templates
description: "ETF 발굴 하네스의 최종 산출물(sector_theme_discovery.md, etf_candidates.md, final_etf_decision.md, analysis.json, data_coverage.md) 생성 템플릿. 최종 리포트 생성, 리포트 재생성, 리포트 형식 수정, 투자 판단 가능성 섹션 작성, 파일럿(축소) 산출물 생성 작업에서 반드시 이 스킬을 사용할 것."
---

# ETF 리포트 템플릿

report-generator가 `_workspace/`의 01~12 산출물을 조립해 최종 산출물을 만든다. **리포트는 새 분석을 하지 않는다** — 상류 산출물에 없는 내용을 쓰면 근거 추적이 끊어지므로, 모든 문장은 상류 JSON의 데이터로 환원 가능해야 한다.

공통 규칙:
- 모든 파일 상단에 기준일(run_date), 생성일, 면책 문구: "본 자료는 투자 추천이 아니며 정보 제공 목적입니다. 최종 투자 판단의 책임은 투자자 본인에게 있습니다."
- 등급 표기 시 항상 `등급 (커버리지 %, 신뢰도, 기준일)` 형태.
- etf-compliance-rules의 금지 표현을 쓰지 않는다.

## 산출물 범위 (run_config.output_scope)

| scope | 산출물 |
|-------|--------|
| **pilot** (1차 실행) | 필수 4종: data_coverage.md, sector_theme_discovery.md, final_etf_decision.md, analysis.json. etf_candidates.md는 생성하지 않고 그 내용(후보군·유형·순도·비용·유동성)을 final_etf_decision.md의 "후보 비교" 섹션에 압축 포함 |
| **full** (2차 이후) | 5종 전부 — etf_candidates.md를 별도 산출물로 분리 |

analysis.json은 scope와 무관하게 전체 스키마를 채운다 (축소는 md 리포트만).

## sector_theme_discovery.md

```markdown
# 섹터·테마 발굴 리포트 ({run_date})
## 1. 현재 시장 환경          ← 01 summary + indicators + key_risks
## 2. 섹터 점수와 선정 결과    ← 02 표 (섹터/등급/근거/리스크) + 선정 3~5개
## 3. 섹터별 테마 후보         ← 03 섹터별 10개 표 (테마/긍정/부정/ETF투자가능/신뢰도)
## 4. 핵심 테마 3개            ← 05 selected (선정 이유·근거 데이터·부족 데이터·리스크·탈락 대비 우선 이유·연결 ETF·신뢰도·ETF 투자 가능성)
## 5. 탈락 테마와 이유         ← 05 rejected (탈락 사유 유형 + 구체 사유)
## 6. 데이터 부족 항목         ← 01~05 coverage.missing 취합
```

## etf_candidates.md (full scope에서만 별도 파일)

```markdown
# ETF 후보군 리포트 ({run_date})
## 테마별 후보군               ← 06 (테마마다 후보 표: 이름/코드/시장/운용사/유형/AUM/총보수)
## 밸류체인 비중과 테마 순도    ← 07 (ETF별 체인 비중 표 + purity_pct)
## 구조·거래 특성              ← 06 structure_trading (상장기간/구조 유형/스프레드/괴리율/추적 품질)
## 유동성·집중도·비용          ← 06+11 (top10 집중도, 거래대금, 총보수)
## 데이터 신뢰도               ← 06~07 confidence/coverage
```

## final_etf_decision.md

섹션 순서를 정확히 따른다:

```markdown
# 최종 ETF 검증 리포트 ({run_date})
## 1. 최종 후보 요약           ← 12 finalists (ETF별: 3축 등급 + 판단 상태 한 줄)
## 2. 후보별 판단 상태         ← 12 status + "검토 가능 ≠ 매수 추천" 병기
## 3. 후보별 3축 등급 상세
### {ETF명} — {판단 상태}
- 테마 구조: {등급} — ← 08 explanation
- 재무 상태: {등급} — ← 09 explanation
- 가격 적정성: {등급} — ← 10 explanation (성장성 맥락 병기)
## 4. ETF 구조·거래 게이트 결과 ← 11 structure_trading_gate (ETF별 status + 사유 + 영향)
## 5. 남은 이유                ← 12 why_remained
## 6. 제외된 이유              ← 12 excluded
## 7. 재검토 조건              ← 12 recheck_conditions
## 8. 대안 탐색 방향           ← 12 alternatives
   (pilot scope: 여기에 "후보 비교" 섹션 추가 — etf_candidates.md 내용 압축)
## 9. 투자 판단 가능성         ← 아래 고정 구조
## 10. 데이터 한계와 면책      ← coverage 취합 + 면책 문구
```

### "투자 판단 가능성" 섹션 (9번, 필수 — 누락 시 QA 위반)

```markdown
## 투자 판단 가능성

### 이 정보만으로 판단 가능한 것
- 어떤 섹터와 테마가 후보로 올라왔는지 / 왜 이 테마가 선택됐는지
- 어떤 ETF가 해당 테마를 실제로 담고 있는지 (보유종목 기준)
- 각 ETF의 테마 구조·재무 상태·가격 적정성과 구조·거래 품질
- 각 ETF의 판단 상태 (검토 가능/조건부 검토/판단 보류/우선순위 낮음)

### 아직 판단하기 어려운 것 (사용자 조건 필요)
- 사용자의 투자 기간·손실 허용도에 맞는지
- 기존 보유 ETF·종목과 중복되는지
- 세금·계좌 측면에서 적합한지
- 어느 정도 비중으로 담아야 하는지

### 추가로 확인해야 할 데이터
← 12 recheck_conditions + 전 단계 missing 취합 (실행 결과 기반으로 구체화)

### 다음 판단 행동
- 같은 테마 ETF와 비교 / 사용자 포트폴리오 중복 확인 / 가격 부담 완화 시 재검토
- 데이터 부족 항목 확인 후 보류 / 사용자 조건 기반 적합성 검토 (Investor Fit — 추후 확장)

### 이 결과가 매수 추천이 아닌 이유
이 하네스는 상품 자체의 후보 적합성만 평가하며, 실제 투자 실행 판단에 필요한 사용자 조건(기간·금액·손실 허용도·포트폴리오)을 반영하지 않기 때문입니다.

> 이 결과는 ETF 후보의 구조와 리스크를 판단하기 위한 참고 정보입니다. 실제 투자 실행 여부는 투자 기간, 투자 금액, 손실 허용도, 보유 포트폴리오 등을 함께 고려해야 합니다.
```

"판단 가능한 것" 목록은 위 고정 항목을 기본으로 하되, 이번 실행에서 실제로 판단 가능해진 것만 남긴다 (예: 판단 보류만 나왔으면 3축 비교 가능성은 제한적으로 서술).

## analysis.json

데이터 계약 문서(`etf-discovery-orchestrator/references/data-contracts.md` 5절)의 스키마(최상위 20키)를 정확히 따른다. 조립 규칙:
- 각 최상위 키에 해당 단계 payload를 그대로 넣는다 (재가공 최소화 — WebView 변환 시 원본 추적 유지)
- 신규 키: `etf_structure_trading_gate`(11 취합), `source_quality_policy`(전 단계 sources·source_conflicts 취합), `investment_judgment_readiness`(9번 섹션과 동일 내용), `investor_fit_required`(항상 true), `pilot_acceptance_summary`(QA가 채움 — 생성 시점엔 null)
- `data_coverage`: 단계별 `{stage, available, missing, impact}` 배열
- `explanation`: ETF별 `{ticker, theme_structure_text, financial_text, valuation_text, structure_gate_text, status_text}` — UI 표출용 순화 문구, 컴플라이언스 준수
- `sources`: 전 단계 sources를 URL 기준 중복 제거해 병합

## data_coverage.md

```markdown
# 데이터 커버리지 리포트 ({run_date})
## 사전 진단 결과              ← 00_coverage_precheck.md
## 영역별 커버리지             ← 표: 시장환경/섹터/테마/ETF후보/구조·거래/보유종목/재무/가격 — 확보율·부족 항목
## 소스 품질 요약              ← primary/secondary/tertiary 사용 비율, 출처 충돌 목록
## 신뢰도 낮은 영역            ← confidence=low 항목 목록과 이유
## 분석 불가 영역              ← 등급 null 처리된 항목과 판단에 준 영향
```
