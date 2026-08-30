# 릴리스와 설치 채널

이 저장소는 `main`을 빠른 검증 채널로, immutable Git tag를 재현 가능한 stable 채널로 사용한다.

## 채널

| 채널 | Git ref | 용도 | 업데이트 방식 |
| --- | --- | --- | --- |
| stable | `codex-plugins-vX.Y.Z` | 일반 사용자와 재현 가능한 설치 | 새 stable tag를 명시해 marketplace를 다시 등록 |
| nightly | `main` | 다음 릴리스 사전 검증 | `marketplace upgrade` 후 플러그인 재설치 |

stable tag는 이미 게시된 뒤 이동하거나 다시 만들지 않는다. `prompt-compiler-vX.Y.Z`, `uiux-advisor-vX.Y.Z`, `interactive-slides-vX.Y.Z`는 각 plugin manifest 버전과 정확히 일치해야 한다.

## 버전 의미

- `plugins/*/.codex-plugin/plugin.json`의 SemVer는 설치 artifact 버전이다.
- Prompt Compiler의 `v3.2-ko`는 내부 protocol spec 버전이다.
- package 버전과 protocol spec은 별도 축이며 문서에는 둘을 함께 표기한다.

## 공개 릴리스 gate

릴리스 직전에 로컬 Codex의 저장된 ChatGPT 로그인으로 critical case를 2회, full case를 1회 실행한다. `.github/workflows/release.yml`을 수동 실행하면서 생성할 tag, 현재 `main`의 전체 commit SHA, model·Codex CLI version과 네 run ID를 입력하고 로컬 gate 통과를 확인한다. workflow는 다음 순서로 실행된다.

1. 입력 commit이 현재 `origin/main` HEAD이고 tag가 아직 존재하지 않는지 확인한다.
2. tag 형식과 plugin manifest 버전을 대조한다.
3. `LICENSE`, `THIRD_PARTY_NOTICES.md`와 attribution source를 검사한다.
4. deterministic validator와 validator unit test를 실행한다.
5. local live eval 확인값과 run ID 형식을 검사하고 operator attestation을 생성한다.
6. 모든 gate가 통과하고 `main`이 그대로인 경우에만 새 immutable tag와 GitHub Release를 함께 생성한다. Release에는 tag metadata와 local live eval attestation을 자산으로 첨부한다.

`.github/workflows/live-eval.yml`의 GitHub-hosted API 평가는 운영자가 별도로 필요할 때만 수동 실행하는 선택 사항이며 release gate가 아니다. 실행하려면 repository secret `CODEX_LIVE_EVAL_API_KEY`가 필요하고 API 사용료가 발생한다. 일반 릴리스와 플러그인 설치에는 이 키가 필요하지 않으며, 설치 사용자는 자신의 Codex 로그인 또는 자신의 API 키를 사용한다.

로컬에서는 `codex login`으로 저장된 인증을 재사용할 수 있다. 기본 `saved` 모드는 ChatGPT 계정용 `gpt-5.6-sol`을 선택하고 파일 기반 `auth.json`만 임시 격리 환경에 복사한 뒤 실행 종료 시 함께 폐기한다. 공개 또는 신뢰할 수 없는 CI에 개인 `auth.json`을 복사하지 않는다.

### 릴리스 간 live eval 비교 리포트(선택)

네 run ID와 기존 릴리스의 비교 리포트를 비교해 추세를 남기고 싶다면 아래 명령을 추가로 실행한다.

```bash
python3 scripts/build_live_eval_release_report.py \
  --current-tag codex-plugins-v0.1.0 \
  --run-ids '<routing-critical>,<routing-full>,<tool-trace-critical>,<tool-trace-full>' \
  --run-root artifacts/live-eval \
  --previous-report <이전-릴리스-릴리스-비교-JSON> \
  --output-json artifacts/live-eval-release-comparison.json \
  --output-markdown artifacts/live-eval-release-comparison.md
```

`previous-report`는 이전 릴리스의 `live-eval-release-comparison.json`을 이용해 비교를 계산한다. 입력이 없으면 현재 값만 저장된다.

릴리스 실행 시 비교 결과를 자산으로 함께 붙이려면 JSON을 압축해서 workflow 입력으로 전달한다.

```bash
gh workflow run release.yml --ref main \
  -f tag=codex-plugins-v0.1.0 \
  -f commit=<main-full-sha> \
  -f local_live_eval_confirmed=true \
  -f local_live_eval_model=gpt-5.6-sol \
  -f 'local_live_eval_codex_version=codex-cli 0.147.0' \
  -f local_live_eval_run_ids='<routing-critical>,<routing-full>,<tool-trace-critical>,<tool-trace-full>' \
  -f local_live_eval_trend_report="$(jq -c . artifacts/live-eval-release-comparison.json)"
```

workflow는 전달된 비교 리포트의 `current_tag`와 네 run ID가 release 입력과 일치하는지 다시 검증한다. workflow input에는 GitHub 크기 제한이 있으므로 비교 리포트에는 run 원문이 아니라 요약·추세·provenance만 포함한다.

### 로컬 다중 모델/빌드 canary matrix

릴리스 전후로 모델별/빌드별 동작 차이를 빠르게 비교하려면 다음처럼 canary matrix를 실행할 수 있다.

```bash
python3 scripts/build_live_eval_canary_matrix.py \
  --model "gpt-5.6,gpt-5.6-sol" \
  --codex-build "baseline=codex" \
  --codex-build "candidate=/path/to/codex-canary-bin" \
  --suite routing \
  --suite tool-trace \
  --case-set critical \
  --attempts 1 \
  --reasoning-effort medium \
  --output-json artifacts/live-eval-canary-matrix.json \
  --output-markdown artifacts/live-eval-canary-matrix.md
```

`--codex-build`는 `label=path` 형태로 입력하며, `path`는 로컬에서 실행 가능한 `codex` 바이너리를 가리키는 경로이다.
필요하면 `--baseline`으로 기준 셀을 지정해 기준 대비 하락율 경고를 확인할 수 있다.

보고서는 다음 파일에 저장된다.

- `artifacts/live-eval-canary-matrix.json`: cell, run 요약, baseline 비교, alert 목록
- `artifacts/live-eval-canary-matrix.md`: 사람이 보기 쉬운 테이블 보고서

### source-liveness drift history

source URL·canonical·title·hash 점검을 이전 정상 기준값과 누적 비교하려면 `--history`를 추가해 실행한다.

```bash
python3 scripts/check_source_liveness.py \
  --output-json artifacts/source-liveness/report.json \
  --output-markdown artifacts/source-liveness/report.md \
  --history artifacts/source-liveness/history.json
```

`source-liveness.yml`은 이전 성공 실행에서 `history.json`을 가져와 현재 결과와 자동으로 baseline 비교를 수행한다.

## 로컬 사전 점검

```bash
python3 scripts/check_release_readiness.py
python3 scripts/validate_release_tag.py --tag prompt-compiler-v0.7.1
python3 scripts/validate_release_tag.py --tag uiux-advisor-v0.9.1
python3 scripts/validate_all.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/live_eval.py run --suite routing --case-set full --dry-run
python3 scripts/live_eval.py run --suite tool-trace --case-set full --dry-run
python3 scripts/live_eval.py run --suite routing --case-set critical --attempts 2 --auth-mode saved
python3 scripts/live_eval.py run --suite routing --case-set full --attempts 1 --auth-mode saved
python3 scripts/live_eval.py run --suite tool-trace --case-set critical --attempts 2 --auth-mode saved
python3 scripts/live_eval.py run --suite tool-trace --case-set full --attempts 1 --auth-mode saved
```

네 run이 모두 gate를 통과한 뒤 다음 순서의 run ID를 쉼표로 연결해 release workflow에 입력한다.

1. routing critical
2. routing full
3. tool-trace critical
4. tool-trace full

```bash
gh workflow run release.yml --ref main \
  -f tag=codex-plugins-v0.1.0 \
  -f commit=<main-full-sha> \
  -f local_live_eval_confirmed=true \
  -f local_live_eval_model=gpt-5.6-sol \
  -f 'local_live_eval_codex_version=codex-cli 0.147.0' \
  -f local_live_eval_run_ids='<routing-critical>,<routing-full>,<tool-trace-critical>,<tool-trace-full>'
```

attestation은 operator가 입력한 확인과 provenance 식별자를 보존한다. GitHub가 로컬 observation 내용을 독립적으로 재실행하거나 증명한다는 의미는 아니다.

Release workflow 실행은 새 tag와 GitHub Release를 함께 생성하는 원격 변경이다. 저장소 공개 전환은 별도 원격 변경이며, 두 작업 모두 로컬 gate가 통과하고 명시적으로 승인된 경우에만 수행한다.
