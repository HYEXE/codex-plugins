# Roadmap

## Public release hardening

- [x] deterministic validator와 routing/orchestration snapshot 평가
- [x] 새 관찰값을 생성하는 격리 live routing eval
- [x] preview/approval 경계를 transcript와 structured tool trace로 함께 검증
- [x] model, Codex CLI, plugin, dataset SHA와 raw event provenance 기록
- [x] 플러그인별 선언형 `quality-gates.json` 자동 발견
- [x] UI/UX knowledge base와 toolkit freshness budget
- [x] Ubuntu, Windows, macOS CI와 validator unit test, ShellCheck
- [x] immutable repository/plugin tag 검증과 gated GitHub Release workflow
- [x] third-party attribution 정책과 public release gate
- [ ] 공개 라이선스 확정과 `LICENSE` 추가
- [ ] `CODEX_LIVE_EVAL_API_KEY` repository secret 설정
- [ ] 최초 stable tag와 GitHub Release 게시
- [ ] 저장소 visibility를 public으로 전환

마지막 네 항목은 법적 선택, 비밀정보 설정 또는 원격 변경이므로 별도 확인 후 진행한다.

## Next

- live eval 결과를 릴리스 간 추세로 비교하는 summary report
- 여러 모델·Codex build를 비교하는 비차단 canary matrix
- plugin 수가 늘어날 때 specialized evaluator command도 plugin manifest에서 선언하는 2단계 validator 분리
