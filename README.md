# Codex Plugins

한국어 중심의 Codex skills-only 플러그인을 독립적으로 관리하는 모노레포입니다.

## 포함 플러그인

| 플러그인 | package | 번들 스킬 | 용도 |
| --- | --- | --- | --- |
| `prompt-compiler` | `0.7.1` | `prompt-coach`, `prompt-compiler`, `prompt-evaluator` | 요청을 필요한 만큼 보완해 실행·검증하고 후속 변경분만 재컴파일하거나, 프롬프트만 작성·평가 |
| `uiux-advisor` | `0.9.1` | `uiux-advisor`, `uiux-auditor`, `implement-async-ui-state`, `implement-ui-interaction`, `implement-ui-motion`, `build-data-visualization`, `build-interactive-graphics`, `compose-creative-ui`, `build-design-system` | 근거 기반 UI/UX 설계·감사와 접근 가능한 widget 상호작용·비동기 작업 상태·모션·차트·2D·3D 그래픽·창의적 UI·디자인 시스템 구현 |
| `interactive-slides` | `0.7.1` | `create-interactive-slides` | 제작 견적·승인·design-plan gate를 거쳐 발표문을 timeline·diagram·code walkthrough·before/after 장면과 fallback이 있는 HTML 발표로 설계·검증 |

## 구조

```text
codex-plugins/
├── .agents/plugins/marketplace.json
├── .github/workflows/
│   ├── live-eval.yml
│   ├── release.yml
│   ├── source-liveness.yml
│   └── validate.yml
├── docs/
│   ├── history/
│   ├── plugin-updates.md
│   └── releases.md
├── evals/live-eval-policy.json
├── plugins/
│   ├── prompt-compiler/
│   │   ├── .codex-plugin/{plugin.json,quality-gates.json}
│   │   └── skills/
│   │       ├── prompt-coach/
│   │       ├── prompt-compiler/
│   │       └── prompt-evaluator/
│   ├── uiux-advisor/
│   │   ├── .codex-plugin/{plugin.json,quality-gates.json}
│   │   └── skills/
│   │       ├── build-design-system/
│   │       ├── build-data-visualization/
│   │       ├── build-interactive-graphics/
│   │       ├── compose-creative-ui/
│   │       ├── implement-async-ui-state/
│   │       ├── implement-ui-interaction/
│   │       ├── implement-ui-motion/
│   │       ├── uiux-advisor/
│   │       └── uiux-auditor/
│   └── interactive-slides/
│       ├── .codex-plugin/{plugin.json,quality-gates.json}
│       ├── CHANGELOG.md
│       └── skills/create-interactive-slides/
├── tests/
│   ├── observations.json
│   ├── skill-routing.jsonl
│   ├── skill-routing-observed-2026-08-14.jsonl
│   └── tool-trace-cases.jsonl
└── scripts/
    ├── check_freshness.py
    ├── check_release_readiness.py
    ├── check_source_liveness.py
    ├── check_version_bumps.py
    ├── create_release_attestation.py
    ├── eval_routing.py
    ├── live_eval.py
    ├── live_eval_lib/
    ├── update_plugins.ps1
    ├── update_plugins.sh
    ├── validate_all.py
    ├── validate_observation_manifest.py
    └── validate_release_tag.py
```

저장소와 marketplace는 하나지만 각 플러그인은 독립적으로 설치하고 버전을 관리합니다. 각 스킬의 실행 지침과 필요한 resources는 해당 스킬 폴더에 둡니다.

`prompt-compiler`가 플러그인의 기본 진입점입니다. `@prompt-compiler` 또는 `$prompt-compiler`와 함께 작업을 요청하면 요청 충분성을 먼저 판단하고, 결과를 바꾸는 정보가 부족할 때만 질문한 뒤 같은 모델 실행 안에서 내부 실행 명세를 만들어 실제 수행·검증까지 이어갑니다. 컴파일된 프롬프트를 사용자가 복사해 다시 보낼 필요는 없습니다. 이 과정은 숨은 두 번째 모델 호출이나 스킬 간 자동 handoff가 아닙니다. 실행 없이 프롬프트 자체만 함께 만들 때는 `prompt-coach`, 기존 프롬프트의 평가·비교·회귀 진단에는 `prompt-evaluator`를 사용합니다.

플러그인은 메시지를 제출하기 전에 입력창을 가로채는 전역 인터셉터가 아닙니다. `@prompt-compiler`는 플러그인 번들을 현재 요청의 컨텍스트로 불러오는 진입점이며, 실제 동작은 선택된 `prompt-compiler` 스킬의 같은 턴 워크플로로 수행됩니다.

현재 작업의 이후 요청에도 같은 점검·실행 흐름을 적용하도록 요청할 수 있습니다. 이 모드는 현재 대화의 작업 지침이며 새 작업까지 자동으로 유지되거나 스킬이 매 턴 다시 주입된다는 보장은 없습니다. 확인 질문에 답하면 대기 중인 원 요청과 합쳐 이어서 실행하고, “먼저 보여주고 승인 후 보내 주세요” 같은 요청은 preview와 실제 외부 행동을 별도 단계로 분리합니다. 실행에 영향을 준 중요한 가정이나 capability 부족으로 남은 미완료 항목은 최종 결과에 구분해 밝힙니다.

후속 요청은 진행·수정·대체·승인·취소로 분류하고, 확정된 제약과 권한을 유지한 채 변경된 입력에 영향받는 산출물과 검증만 갱신합니다. 정정이나 대상 변경으로 오래된 가정·preview 승인·검증이 무효화되면 이전 성공을 재사용하지 않습니다.

## 검증

```bash
python3 scripts/validate_all.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/validate_observation_manifest.py tests/observations.json plugins/prompt-compiler/evals/observations.json
python3 scripts/live_eval.py validate
python3 scripts/eval_routing.py validate
python3 plugins/prompt-compiler/skills/prompt-compiler/scripts/eval_orchestration.py validate
python3 plugins/prompt-compiler/skills/prompt-compiler/scripts/eval_orchestration.py score plugins/prompt-compiler/skills/prompt-compiler/evals/orchestration-observed-2026-08-12.jsonl
python3 plugins/uiux-advisor/.codex-plugin/validators/eval_toolkit_search.py
python3 plugins/prompt-compiler/skills/prompt-coach/scripts/eval_harness.py validate
python3 plugins/prompt-compiler/skills/prompt-coach/scripts/eval_harness.py score plugins/prompt-compiler/skills/prompt-coach/evals/observed-results-2026-08-11.jsonl
python3 plugins/uiux-advisor/.codex-plugin/validators/eval_uiux_search.py
python3 scripts/check_version_bumps.py --base <base-ref>
git diff --check
```

공통 검증기는 marketplace와 manifest 연결, 전체 스킬 메타데이터와 UI 자산, Python 구문, observation manifest, UI/UX 지식베이스 참조 무결성과 freshness를 확인합니다. 플러그인별 skill 목록, 필수 파일·marker, KB·toolkit 수, freshness budget과 specialized evaluator command는 각 `.codex-plugin/quality-gates.json`이 소유하며 공통 validator가 안전한 Python argv로 자동 실행합니다.

저장된 behavior snapshot은 안정적인 `observations.json` manifest가 선택합니다. metadata에 dataset/result SHA-256, 관찰 시각, plugin 버전과 provenance 상태를 기록하며, 과거 실행에서 확인할 수 없는 model·Codex build는 추정하지 않고 `legacy-partial`로 표시합니다. 오케스트레이션 transcript 평가는 질문 수, 이어가기, preview 승인 경계와 외부 행동 주장을 판정하지만 그 자체로 side effect 부재를 증명하지 않습니다.

`live_eval.py`는 별도 경로입니다. 고정 Codex CLI와 지정 모델을 격리된 plugin 설치 환경에서 실행해 새로운 routing observation과 raw JSONL event를 만들고, preview/approval 사례는 transcript assertion과 fake external action의 structured tool trace assertion을 함께 적용합니다. 인증, marketplace plugin 발견, event parsing, provenance와 scoring은 `live_eval_lib` 모듈로 분리돼 있습니다. 결과에는 model, reasoning effort, Codex version, runner commit, plugin version, timestamp, case set, dataset/policy SHA와 인증 방식이 기록됩니다. 일반 PR에서는 API 호출 없이 deterministic validator만 사용하고, release 전 live 실행은 저장된 ChatGPT 로그인을 사용하는 로컬 Codex에서 수행합니다. GitHub-hosted API 평가는 운영자가 별도로 필요할 때만 수동 실행합니다.

외부 UI/UX 자료의 URL, canonical URL, title과 content hash는 주간 `source-liveness.yml`에서 비차단 보고서로 확인합니다. 외부 사이트의 일시 장애나 동적 콘텐츠 변화는 일반 PR과 release gate를 실패시키지 않으며, JSON·Markdown artifact를 사람이 검토합니다.

로컬 live eval은 기본적으로 현재 Codex CLI의 저장된 로그인과 ChatGPT 계정용 `gpt-5.6-sol`을 사용합니다. `saved` 모드는 원본 `auth.json`을 변경하거나 결과 artifact에 포함하지 않고, 실행 중에만 권한이 제한된 임시 `CODEX_HOME`으로 복사합니다. 사용자는 먼저 `codex login status`로 자신의 인증 방식을 확인해야 합니다. 파일 기반 로그인 cache가 없는 환경에서는 Codex의 credential storage를 file로 설정해 다시 로그인하거나 `api-key` 모드를 사용합니다. 모델은 필요할 때 `--model`로 명시할 수 있습니다.

```bash
python3 scripts/live_eval.py run \
  --suite routing \
  --case-set critical \
  --auth-mode saved
```

공개 CI와 release workflow는 저장된 개인 로그인을 배포하지 않습니다. release workflow는 로컬 live eval의 model·Codex version·run ID와 operator 확인을 attestation으로 보존하고 deterministic validator를 다시 실행합니다. 선택적 GitHub-hosted live eval만 운영자의 `CODEX_LIVE_EVAL_API_KEY`를 사용합니다. 플러그인을 설치한 일반 사용자는 자신의 Codex 로그인 또는 자신의 API 키로 실행하므로 저장소 운영자의 키나 사용료를 공유하지 않습니다.

프론트엔드 도구는 역할·생태계뿐 아니라 필요한 기능, 적용 surface, 도입 방식과 리스크 상한으로 검색할 수 있습니다. `--recommend`는 필터된 후보를 낮은 리스크, framework 직접 지원, 가벼운 도입 방식 순으로 정렬하며 보편적 품질 점수로 해석하지 않습니다.

```bash
python3 plugins/uiux-advisor/skills/uiux-advisor/scripts/search_toolkits.py \
  --capability carousel --surface carousel --ecosystem react \
  --recommend --max-risk medium --top 3
```

라우팅 평가 데이터는 예상 스킬과 비적용 경계를 정의합니다. 기대 라벨을 노출하지 않은 독립 관찰 snapshot도 통합 검증에서 점수화하며, 라우팅 사례가 바뀌면 새 관찰 결과와 metadata hash를 함께 갱신해야 합니다. 다른 실행에서 관찰한 선택 결과도 다음처럼 점수화할 수 있습니다.

```bash
python3 scripts/eval_routing.py score observed-routing.jsonl
```

GitHub Actions는 pull request와 `main` push에서 Ubuntu·Windows·macOS 통합 검증, validator unit test, ShellCheck와 운영체제별 업데이트 스크립트 dry run을 실행합니다. 플러그인에 배포되는 파일이 바뀌면 해당 manifest의 SemVer가 기준 커밋보다 증가했는지도 검사합니다. GitHub-hosted API live eval은 운영자가 필요할 때만 수동으로 실행하며, stable Release는 로컬 Codex에서 통과한 critical·full live eval의 run ID와 실행 정보를 attestation으로 확인한 뒤 생성합니다.

## GitHub marketplace 설치 채널

일반 사용자에게는 게시된 immutable repository tag를 사용하는 stable 채널을 권장합니다.

```bash
codex plugin marketplace add HYEXE/codex-plugins --ref codex-plugins-vX.Y.Z
codex plugin add prompt-compiler@codex-plugins-kr
codex plugin add uiux-advisor@codex-plugins-kr
codex plugin add interactive-slides@codex-plugins-kr
```

다음 릴리스를 빠르게 확인하려면 `main` nightly 채널을 별도 환경에서 사용합니다.

```bash
codex plugin marketplace add HYEXE/codex-plugins --ref main
```

tag 형식, release gate와 stable/nightly 운영 규칙은 [릴리스와 설치 채널](docs/releases.md)에 정리돼 있습니다.

repository tag는 `codex-plugins-vX.Y.Z`, marketplace ID는 `codex-plugins-kr`로 통일합니다.

## 업데이트

저장소에 새 버전이 push돼도 각 PC에 이미 설치된 플러그인은 자동으로 바뀌지 않습니다. 업데이트에는 서로 독립적인 세 상태가 관여합니다.

1. **저장소 소스**: Git 또는 로컬 작업 복사본의 실제 플러그인 파일
2. **marketplace snapshot**: Git marketplace가 특정 시점의 저장소를 내려받아 보관한 복사본
3. **설치 cache**: Codex가 현재 로드할 수 있도록 플러그인별로 설치한 복사본

Git marketplace를 사용하는 PC에서는 marketplace snapshot을 갱신한 뒤 플러그인을 다시 설치해야 합니다. 로컬 marketplace는 작업 복사본을 직접 가리키므로 snapshot 갱신은 필요 없지만, 변경된 소스를 설치 cache에 반영하기 위한 재설치는 필요합니다.

### 업데이트 스크립트가 하는 일

운영체제별 스크립트는 다음 명령을 순서대로 실행합니다.

```text
codex plugin marketplace upgrade codex-plugins-kr
codex plugin add prompt-compiler@codex-plugins-kr
codex plugin add uiux-advisor@codex-plugins-kr
codex plugin add interactive-slides@codex-plugins-kr
```

첫 번째 명령은 Git marketplace snapshot을 등록된 ref에서 다시 가져옵니다. `main` nightly marketplace라면 최신 commit으로 이동하지만 immutable stable tag라면 같은 snapshot을 다시 확인할 뿐 더 새 stable tag로 자동 이동하지 않습니다. 이어지는 두 명령은 각 플러그인을 다시 설치해 Codex의 설치 cache를 교체합니다. 스크립트는 현재 작업 복사본에 `git pull`을 실행하거나 manifest 버전을 자동으로 올리거나 실행 중인 Codex 작업을 다시 시작하지 않습니다.

플러그인 소스 자체를 변경했다면 설치 전에 해당 `.codex-plugin/plugin.json`의 SemVer를 올리고 저장소 검증을 실행합니다.

```bash
python3 scripts/validate_all.py
```

### Git marketplace 업데이트

macOS/Linux:

```bash
./scripts/update_plugins.sh
```

Windows PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\update_plugins.ps1
```

실제 변경 전에 실행될 명령만 확인하려면 dry run을 사용합니다.

```bash
./scripts/update_plugins.sh --dry-run
```

```powershell
pwsh -NoProfile -File .\scripts\update_plugins.ps1 -DryRun
```

### 로컬 marketplace 업데이트

로컬 작업 복사본을 직접 테스트하려면 최초 한 번만 저장소 루트를 marketplace로 등록합니다.

```bash
codex plugin marketplace add /absolute/path/to/codex-plugins
```

그 뒤 소스가 변경될 때마다 세 플러그인을 다시 설치합니다. 로컬 marketplace에는 원격 snapshot이 없으므로 `marketplace upgrade`를 실행하지 않습니다.

```bash
codex plugin add prompt-compiler@codex-plugins-kr
codex plugin add uiux-advisor@codex-plugins-kr
codex plugin add interactive-slides@codex-plugins-kr
```

### Windows 실행 정책 대응

조직 또는 PC의 실행 정책이 서명되지 않은 `update_plugins.ps1`을 차단하면 `-ExecutionPolicy Bypass`로 우회하지 않습니다. 대신 허용된 Codex CLI를 찾아 위 명령을 직접 실행합니다. 아래 예시의 `marketplace upgrade`는 Git marketplace에서만 필요하며, 로컬 marketplace에서는 해당 줄을 생략합니다.

```powershell
$Codex = Get-ChildItem "$env:LOCALAPPDATA\OpenAI\Codex\bin" `
  -Recurse -Filter codex.exe |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1 -ExpandProperty FullName

& $Codex plugin marketplace upgrade codex-plugins-kr
& $Codex plugin add "prompt-compiler@codex-plugins-kr"
& $Codex plugin add "uiux-advisor@codex-plugins-kr"
& $Codex plugin add "interactive-slides@codex-plugins-kr"
```

### 업데이트 확인과 적용

설치 후 marketplace 경로와 플러그인 상태를 확인합니다.

```bash
codex plugin marketplace list
codex plugin list
```

완료 기준은 다음과 같습니다.

- `codex-plugins-kr`가 의도한 Git 또는 로컬 저장소를 가리킵니다.
- `prompt-compiler`, `uiux-advisor`, `interactive-slides`가 모두 `installed, enabled` 상태입니다.
- 표시된 버전이 각 플러그인의 manifest 버전과 일치합니다.
- 저장소 작업 트리에 업데이트 과정이 만든 의도하지 않은 변경이 없습니다.

이미 열려 있던 작업은 이전 plugin snapshot을 계속 사용할 수 있습니다. 설치 또는 업데이트 후에는 Codex를 재시작하거나 새 작업을 열어 변경 사항을 불러옵니다. 최초 설정, CLI 경로 지정, launchd·cron·Windows 작업 스케줄러 자동화는 [플러그인 업데이트 가이드](docs/plugin-updates.md)를 참고해 주세요.

## 배포 상태와 권리

- 이 저장소의 자체 코드와 콘텐츠는 [Apache License 2.0](LICENSE)으로 배포합니다.
- `uiux-advisor`의 세부 출처는 `references/kb/SOURCE_REGISTRY.md`와 `sources.json`에 기록돼 있습니다.
- 제3자 attribution과 재배포 검토 원칙은 `THIRD_PARTY_NOTICES.md`에 기록돼 있습니다.
- public release readiness gate는 Apache-2.0 원문과 필수 attribution 파일이 유지되는지 검사합니다.
- 실제 배포 전에는 현재 커밋의 검증 결과, plugin package/protocol 버전, 지원 범위, 지식베이스 최신성과 full live eval을 다시 확인합니다.

## 프로젝트 참여와 보안

- 변경을 제안하려면 [기여 안내](CONTRIBUTING.md)를 확인해 주세요.
- 보안 취약점은 공개 issue 대신 [보안 정책](SECURITY.md)의 비공개 신고 절차를 이용해 주세요.
- 프로젝트 공간에서는 [행동 강령](CODE_OF_CONDUCT.md)을 따라 주세요.
