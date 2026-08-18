# 릴리스와 설치 채널

이 저장소는 `main`을 빠른 검증 채널로, immutable Git tag를 재현 가능한 stable 채널로 사용한다.

## 채널

| 채널 | Git ref | 용도 | 업데이트 방식 |
| --- | --- | --- | --- |
| stable | `codex-workflows-vX.Y.Z` | 일반 사용자와 재현 가능한 설치 | 새 stable tag를 명시해 marketplace를 다시 등록 |
| nightly | `main` | 다음 릴리스 사전 검증 | `marketplace upgrade` 후 플러그인 재설치 |

stable tag는 이미 게시된 뒤 이동하거나 다시 만들지 않는다. `prompt-compiler-vX.Y.Z`와 `uiux-advisor-vX.Y.Z`는 각 plugin manifest 버전과 정확히 일치해야 한다.

## 버전 의미

- `plugins/*/.codex-plugin/plugin.json`의 SemVer는 설치 artifact 버전이다.
- Prompt Compiler의 `v3.2-ko`는 내부 protocol spec 버전이다.
- package 버전과 protocol spec은 별도 축이며 문서에는 둘을 함께 표기한다.

## 공개 릴리스 gate

tag push 뒤 `.github/workflows/release.yml`은 다음 순서로 실행된다.

1. tag 형식과 plugin manifest 버전을 대조한다.
2. `LICENSE`, `THIRD_PARTY_NOTICES.md`와 attribution source를 검사한다.
3. deterministic validator와 validator unit test를 실행한다.
4. 고정된 Codex CLI와 지정 모델로 full routing/tool-trace live eval을 실행한다.
5. 모든 gate가 통과한 경우에만 GitHub Release를 생성한다.

GitHub-hosted live eval에는 저장소 운영자의 repository secret `CODEX_LIVE_EVAL_API_KEY`가 필요하다. 키는 실제 실행 step에만 전달하며 artifact에는 raw event, transcript, tool trace와 비밀이 아닌 provenance만 보존한다. 이 키는 저장소나 플러그인에 포함되지 않으며 설치 사용자는 자신의 Codex 로그인 또는 자신의 API 키를 사용한다.

로컬에서는 `codex login`으로 저장된 인증을 재사용할 수 있다. 기본 `saved` 모드는 ChatGPT 계정용 `gpt-5.6-sol`을 선택하고 파일 기반 `auth.json`만 임시 격리 환경에 복사한 뒤 실행 종료 시 함께 폐기한다. 공개 또는 신뢰할 수 없는 CI에 개인 `auth.json`을 복사하지 않는다.

## 로컬 사전 점검

```bash
python3 scripts/check_release_readiness.py
python3 scripts/validate_release_tag.py --tag prompt-compiler-v0.7.0
python3 scripts/validate_release_tag.py --tag uiux-advisor-v0.9.0
python3 scripts/validate_all.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/live_eval.py run --suite routing --case-set full --dry-run
python3 scripts/live_eval.py run --suite tool-trace --case-set full --dry-run
python3 scripts/live_eval.py run --suite routing --case-set critical --auth-mode saved
```

실제 tag 생성·push, 저장소 공개 전환과 GitHub Release 생성은 각각 별도의 원격 변경이다. 로컬 gate가 통과한 뒤 명시적으로 승인된 경우에만 수행한다.
