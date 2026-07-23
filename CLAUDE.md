# ETF Discovery Harness

## 하네스: ETF 발굴 에이전트

**목표:** "섹터 → 테마 → ETF 후보 → 검증" 순서로 투자 후보 ETF를 발굴하고, 매수·매도 추천 없이 근거와 리스크를 구조화한 리포트 5종을 생성한다.

**트리거:** ETF 발굴·분석·검증, 섹터/테마 분석, 시장 환경 진단, 투자 후보 리포트 관련 작업 요청 시 `etf-discovery-orchestrator` 스킬을 사용하라. 부분 재실행("테마만 다시", "리포트만 다시", "ETF X 재검증")도 동일하다. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-07-23 | GitHub 공개 구조 정리 — README·MIT LICENSE·gitignore·API 환경 변수 템플릿·일회성 리포트 내보내기 추가, 설계 문서를 docs/로 이동 | 저장소 구조 / etf-evidence-standards / etf-ui-render | 안전한 공개와 사용자 설치·결과 공유 절차 단순화 |
| 2026-07-05 | 2차 실행(run2-us-fmp) 완료 — US 중심 재평가·FMP 보강. 스코어러 15종목 상한을 구조화 API 배치 시 해제(커버 80%+ 확대), 병렬 스코어러 임시 파일 티커 네임스페이스+앵커 assert 규칙 추가(레이스 2회 발생 교훈), 차점 테마 재검증 트랙 패턴 도입(GRID·AIPO). 산출: output/2026-07-05-us/ (full 5종 + ui/) | agents/holdings-{financial,valuation}-scorer / 실행 산출물 | XAR 등 커버리지 44%→99.9% 달성, 재검증 6종 전부 재평가 성공 |
| 2026-07-04 | 초기 구성 (에이전트 14 + 스킬 5) | 전체 | - |
| 2026-07-05 | 데이터 소스 우선순위·소스 품질 정책, ETF 구조·거래 하드 게이트, Decision Gate 판정 순서 5단계화, 테마 최소 선정 조건(8중2)·탈락 사유 유형화, 부정 근거 의무화, 투자 판단 가능성 섹션, analysis.json 신규 5키, 1차 파일럿 산출물 축소(output_scope)·acceptance test 15문항, Investor Fit Agent 추후 확장 명시 | 전체 하네스 / Decision Gate / Report / QA | 실제 투자 판단 검증 가능성을 높이기 위함 |
| 2026-07-05 | UI 변환 레이어 추가 (v1.2) — 에이전트 3개(ui-payload-builder, html-mock-renderer, ui-render-qa) + etf-ui-render 스킬(mock.html 자산·check_html.py 포함), 오케스트레이터 Phase 13.5 삽입, output/ui/ 구조 추가. 리서치 판단은 불변 — analysis.json→ui_payload.json→모바일 WebView HTML 후처리만 담당 | agents 3종 / skills/etf-ui-render / orchestrator / docs/HARNESS_DESIGN.md | 텍스트 리포트만으로 판단 검토가 어려워 목 UI에 실제 리서치 결과를 바인딩한 시각 표현물 필요 |
| 2026-07-05 | 구성종목 점수 지도를 종목 히트맵(트리맵) 중심 9단계 구조로 재정의 — 면적=비중·색=탭(재무/가격) 등급, 선택 요약·범례·상위 비중 요약·상세보기 토글, 표는 히트맵 아래 상세로. holdings_heatmap 계약 확장(short_name/ticker/value_chain/data_confidence/is_analyzed + meta) | skills/etf-ui-render / agents/ui-payload-builder / render.py | "표만 나오면 실패 — 히트맵이 메인" 사용자 피드백 |
| 2026-07-05 | UI 레이어 1차 실행 교훈 반영 — html-mock-renderer에 렌더 스크립트 생성 필수 규칙 추가(긴 HTML 직접 출력 시 API 중단 2회 발생 → render.py 방식으로 폴백 성공), 07↔09/10 종목명 표기 불일치(LS일렉트릭 사례)를 2차 실행 개선 후보로 기록 | agents/html-mock-renderer.md | UI 레이어 실행 테스트에서 발견된 실패 패턴 |
| 2026-07-05 | FMP API 등록 (키 경로·stable 엔드포인트 8종·KR/US 커버리지 검증 결과) — 재무·가격·미국 ETF holdings 수집 시 웹 검색보다 우선 사용 | skills/etf-evidence-standards/references/source-priority.md | 1차 파일럿에서 재무·배수 수치가 secondary 언론 인용에 의존 — 구조화 API로 정확도·기준일 명확성 개선 |
