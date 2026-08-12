# Codex Workflows

한국어 중심의 Codex 워크플로를 독립적인 skills-only 플러그인으로 관리하는 모노레포다.

## 포함 플러그인

| 플러그인 | 번들 스킬 | 용도 |
| --- | --- | --- |
| `prompt-compiler` | `prompt-coach`, `prompt-compiler`, `prompt-evaluator` | 요청을 필요한 만큼 보완해 실행·검증하고 후속 변경분만 재컴파일하거나, 프롬프트만 작성·평가 |
| `uiux-advisor` | `uiux-advisor`, `uiux-auditor`, `implement-ui-interaction`, `implement-ui-motion`, `build-data-visualization`, `build-interactive-graphics`, `compose-creative-ui`, `build-design-system` | 근거 기반 UI/UX 설계·감사와 접근 가능한 상호작용·모션·차트·2D·3D 그래픽·창의적 UI·디자인 시스템 구현 |

## 구조

```text
codex-workflows/
├── .agents/plugins/marketplace.json
├── .github/workflows/validate.yml
├── docs/plugin-updates.md
├── plugins/
│   ├── prompt-compiler/
│   │   ├── .codex-plugin/plugin.json
│   │   └── skills/
│   │       ├── prompt-coach/
│   │       ├── prompt-compiler/
│   │       └── prompt-evaluator/
│   └── uiux-advisor/
│       ├── .codex-plugin/plugin.json
│       └── skills/
│           ├── build-design-system/
│           ├── build-data-visualization/
│           ├── build-interactive-graphics/
│           ├── compose-creative-ui/
│           ├── implement-ui-interaction/
│           ├── implement-ui-motion/
│           ├── uiux-advisor/
│           └── uiux-auditor/
├── tests/
│   ├── skill-routing.jsonl
│   ├── skill-routing-observed-2026-08-12.jsonl
│   ├── toolkit-search-cases.jsonl
│   └── uiux-search-cases.jsonl
└── scripts/
    ├── check_version_bumps.py
    ├── eval_routing.py
    ├── eval_toolkit_search.py
    ├── eval_uiux_search.py
    ├── update_plugins.ps1
    ├── update_plugins.sh
    └── validate_all.py
```

저장소와 marketplace는 하나지만 각 플러그인은 독립적으로 설치하고 버전을 관리한다. 각 스킬의 실행 지침과 필요한 resources는 해당 스킬 폴더에 둔다.

`prompt-compiler`가 플러그인의 기본 진입점이다. `@prompt-compiler` 또는 `$prompt-compiler`와 함께 작업을 요청하면 요청 충분성을 먼저 판단하고, 결과를 바꾸는 정보가 부족할 때만 질문한 뒤 같은 모델 실행 안에서 내부 실행 명세를 만들어 실제 수행·검증까지 이어간다. 컴파일된 프롬프트를 사용자가 복사해 다시 보낼 필요는 없다. 이 과정은 숨은 두 번째 모델 호출이나 스킬 간 자동 handoff가 아니다. 실행 없이 프롬프트 자체만 함께 만들 때는 `prompt-coach`, 기존 프롬프트의 평가·비교·회귀 진단에는 `prompt-evaluator`를 사용한다.

플러그인은 메시지를 제출하기 전에 입력창을 가로채는 전역 인터셉터가 아니다. `@prompt-compiler`는 플러그인 번들을 현재 요청의 컨텍스트로 불러오는 진입점이며, 실제 동작은 선택된 `prompt-compiler` 스킬의 같은 턴 워크플로로 수행된다.

현재 작업의 이후 요청에도 같은 점검·실행 흐름을 적용하도록 요청할 수 있다. 이 모드는 현재 대화의 작업 지침이며 새 작업까지 자동으로 유지되거나 스킬이 매 턴 다시 주입된다는 보장은 없다. 확인 질문에 답하면 대기 중인 원 요청과 합쳐 이어서 실행하고, “먼저 보여주고 승인 후 보내줘” 같은 요청은 preview와 실제 외부 행동을 별도 단계로 분리한다. 실행에 영향을 준 중요한 가정이나 capability 부족으로 남은 미완료 항목은 최종 결과에 구분해 밝힌다.

후속 요청은 진행·수정·대체·승인·취소로 분류하고, 확정된 제약과 권한을 유지한 채 변경된 입력에 영향받는 산출물과 검증만 갱신한다. 정정이나 대상 변경으로 오래된 가정·preview 승인·검증이 무효화되면 이전 성공을 재사용하지 않는다.

## 검증

```bash
python3 scripts/validate_all.py
python3 scripts/eval_routing.py validate
python3 plugins/prompt-compiler/skills/prompt-compiler/scripts/eval_orchestration.py validate
python3 plugins/prompt-compiler/skills/prompt-compiler/scripts/eval_orchestration.py score plugins/prompt-compiler/skills/prompt-compiler/evals/orchestration-observed-2026-08-12.jsonl
python3 scripts/eval_toolkit_search.py
python3 plugins/prompt-compiler/skills/prompt-coach/scripts/eval_harness.py validate
python3 plugins/prompt-compiler/skills/prompt-coach/scripts/eval_harness.py score plugins/prompt-compiler/skills/prompt-coach/evals/observed-results-2026-08-11.jsonl
python3 scripts/eval_uiux_search.py
python3 scripts/check_version_bumps.py --base <base-ref>
git diff --check
```

공통 검증기는 marketplace와 manifest 연결, 전체 스킬 메타데이터와 UI 자산, Python 구문, Prompt Compiler 오케스트레이션·구조 평가, Prompt Coach 정적 케이스와 독립 관찰 응답의 분리·채점, UI/UX 지식베이스 참조 무결성, 프론트엔드 도구 레지스트리 schema·역할·생태계·capability·surface·risk·fallback·출처 형식과 검색 회귀를 확인한다. 오케스트레이션 평가는 질문 수, 작업 단위 활성화, 질문 답변 후 이어가기, preview 승인 경계, 부분 완료 보고, 프롬프트·계획 노출, 결과 제공, 재전송 요구와 자동 연계·외부 행동 주장을 사용자에게 보인 transcript에서 판정한다. 별도 tool trace가 없으면 실제 외부 side effect 부재의 증거로 사용하지 않는다. 외부 문서 URL의 실제 생존 여부, 현재 API와 라이선스는 스킬 실행 시 공식 출처에서 별도로 확인한다.

프론트엔드 도구는 역할·생태계뿐 아니라 필요한 기능, 적용 surface, 도입 방식과 리스크 상한으로 검색할 수 있다. `--recommend`는 필터된 후보를 낮은 리스크, framework 직접 지원, 가벼운 도입 방식 순으로 정렬하며 보편적 품질 점수로 해석하지 않는다.

```bash
python3 plugins/uiux-advisor/skills/uiux-advisor/scripts/search_toolkits.py \
  --capability carousel --surface carousel --ecosystem react \
  --recommend --max-risk medium --top 3
```

라우팅 평가 데이터는 예상 스킬과 비적용 경계를 정의한다. 기대 라벨을 노출하지 않은 독립 관찰 snapshot도 통합 검증에서 점수화하며, 라우팅 사례가 바뀌면 새 관찰 결과를 함께 갱신해야 한다. 다른 실행에서 관찰한 선택 결과도 다음처럼 점수화할 수 있다.

```bash
python3 scripts/eval_routing.py score observed-routing.jsonl
```

GitHub Actions는 pull request와 `main` push에서 Ubuntu·Windows 환경의 통합 검증과 운영체제별 업데이트 스크립트 dry run을 실행한다. 플러그인에 배포되는 파일이 바뀌면 해당 manifest의 SemVer가 기준 커밋보다 증가했는지도 검사한다.

## GitHub marketplace 설치

```bash
codex plugin marketplace add HYEXE/codex-workflows --ref main
codex plugin add prompt-compiler@codex-workflows-kr
codex plugin add uiux-advisor@codex-workflows-kr
```

## 업데이트

저장소에 새 버전이 push돼도 각 PC의 Git marketplace snapshot과 설치 cache는 자동으로 바뀌지 않는다. 운영체제별 스크립트가 marketplace를 갱신하고 두 플러그인을 다시 설치한다.

macOS/Linux:

```bash
./scripts/update_plugins.sh
```

Windows PowerShell:

```powershell
pwsh -NoProfile -File .\scripts\update_plugins.ps1
```

실제 변경 없이 실행할 명령을 먼저 확인할 수 있다.

```bash
./scripts/update_plugins.sh --dry-run
```

최초 설정, CLI 경로 지정, launchd·cron·Windows 작업 스케줄러 자동화는 [플러그인 업데이트 가이드](docs/plugin-updates.md)를 참고한다. 설치 또는 업데이트 후에는 Codex를 재시작하거나 새 작업을 열어 변경 사항을 불러온다.

## 로컬 개발

GitHub에 push하기 전 로컬 소스를 별도로 검증하려면 저장소 루트를 marketplace로 등록할 수 있다. 같은 이름의 Git marketplace가 이미 등록돼 있다면 충돌을 피하기 위해 기존 source를 먼저 확인한다.

```bash
codex plugin marketplace add /absolute/path/to/codex-workflows
```

## 배포 상태와 권리

- `uiux-advisor`의 세부 출처는 `references/kb/SOURCE_REGISTRY.md`와 `sources.json`에 기록돼 있다.
- 코드, 자체 작성 콘텐츠, 제3자 자료 기반 콘텐츠의 라이선스와 재배포 가능성은 공개 배포 범위에 맞게 별도로 검토한다.
- 실제 배포 전에는 현재 커밋의 검증 결과, 버전, 지원 범위와 지식베이스 최신성을 다시 확인한다.
