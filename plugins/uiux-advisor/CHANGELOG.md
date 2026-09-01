# Changelog

## Package 0.9.2 — Plugin-local Content Validation

변경:
- knowledge-base와 toolkit 구조·freshness 검증 로직을 공통 validator에서 plugin-local 선언형 validator로 이동
- time-sensitive guide, stable guide와 toolkit role별 실제 재검토 일정을 추가하고 기준일을 검토 없이 변경하지 않는 원칙을 명시

## Package 0.9.1 — Bundled Search Validators

변경:
- knowledge-base와 toolkit 검색 회귀 evaluator 및 case dataset을 플러그인 `.codex-plugin` 내부로 이동
- specialized evaluator와 CLI smoke command를 `quality-gates.json`에 선언
- 외부 source URL·canonical·title·hash를 주간 비차단 보고서로 확인하는 저장소 workflow 추가

## Package 0.9.0 — Declarative Quality Gates and Freshness Budgets

변경:
- skill별 필수 파일과 의미적 marker를 `.codex-plugin/quality-gates.json`에서 선언
- UI/UX knowledge base의 guide 개수와 freshness budget을 플러그인 설정으로 이동
- frontend toolkit registry의 schema, 최소 항목 수, 필수 역할·도구와 freshness budget을 플러그인 설정으로 이동

freshness 정책:
- time-sensitive guide는 90일 이후 warning, 180일 이후 release-blocking error
- stable guide는 365일 이후 warning, 730일 이후 release-blocking error
- toolkit 검증일은 180일 이후 warning, 365일 이후 release-blocking error

## Package 0.8.0 — Async Operation State

변경:
- 요청·스트림·background job·batch lifecycle을 전담하는 `implement-async-ui-state` skill 추가
- widget input contract와 비동기 operation state의 routing 경계를 분리
- 중복·순서·취소·재시도·부분 성공·reconnect·optimistic 상태의 구현 및 검증 규칙 추가
