# 릴리스와 설치 채널

이 저장소는 `main`을 빠른 검증 채널로, immutable Git tag를 재현 가능한 stable 채널로 사용한다.

## 채널

| 채널 | Git ref | 용도 | 업데이트 방식 |
| --- | --- | --- | --- |
| stable | `codex-plugins-vX.Y.Z` | 일반 사용자와 재현 가능한 설치 | 새 stable tag를 명시해 marketplace를 다시 등록 |
| nightly | `main` | 다음 릴리스 사전 검증 | `marketplace upgrade` 후 플러그인 재설치 |

stable tag는 이미 게시된 뒤 이동하거나 다시 만들지 않는다. `prompt-compiler-vX.Y.Z`와 `uiux-advisor-vX.Y.Z`는 각 plugin manifest 버전과 정확히 일치해야 한다.

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
