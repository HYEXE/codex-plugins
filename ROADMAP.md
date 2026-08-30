# Roadmap

## Public release hardening

- [x] deterministic validator와 routing/orchestration snapshot 평가
- [x] 새 관찰값을 생성하는 격리 live routing eval
- [x] preview/approval 경계를 transcript와 structured tool trace로 함께 검증
- [x] model, Codex CLI, plugin, dataset SHA와 raw event provenance 기록
- [x] 플러그인별 선언형 `quality-gates.json` 자동 발견
- [x] UI/UX knowledge base와 toolkit freshness budget
- [x] Ubuntu, Windows, macOS CI와 validator unit test, ShellCheck
- [x] deterministic validation과 로컬 live eval attestation 후 immutable tag를 생성하는 gated GitHub Release workflow
- [x] third-party attribution 정책과 public release gate
- [x] 공개 라이선스를 Apache-2.0으로 확정하고 `LICENSE` 추가
- [x] 로컬 저장 인증과 CI API key를 분리한 live eval 인증 모드
- [x] specialized evaluator command와 observation 선택을 plugin quality gate에서 선언
- [x] live eval의 인증·plugin 발견·event·provenance·scoring 모듈 분리
- [x] 외부 source URL·canonical·title·hash의 주간 비차단 보고
- [x] API 기반 GitHub-hosted live eval을 release gate에서 선택적 수동 workflow로 분리
- [x] 최초 stable tag `codex-plugins-v0.1.0`와 GitHub Release 게시
- [x] 저장소 visibility를 public으로 전환

최초 public release hardening 범위는 모두 완료했습니다.

## Next

- [x] live eval 결과를 릴리스 간 추세로 비교하는 summary report
- [x] 여러 모델·Codex build를 로컬에서 비교하는 비차단 canary matrix
- [ ] source liveness artifact를 이전 정상 baseline과 자동 비교하는 drift history 실제 Actions 실행 확인
- [x] interactive-slides routing fixture의 live observation과 metadata hash 갱신
