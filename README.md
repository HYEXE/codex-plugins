# Codex Workflows

한국어 중심의 Codex 워크플로를 독립적인 skills-only 플러그인으로 관리하는 모노레포다.

## 포함 플러그인

| 플러그인 | 번들 스킬 | 용도 |
| --- | --- | --- |
| `prompt-compiler` | `prompt-coach`, `prompt-compiler`, `prompt-evaluator` | 필요한 경우 질문으로 니즈를 구체화해 정확한 프롬프트를 작성하고, 확정된 요청을 실행 구조로 컴파일·평가 |
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

`prompt-coach`는 질문을 통한 니즈 발견과 최종 프롬프트 작성, `prompt-compiler`는 확정된 요청의 실행, `prompt-evaluator`는 기존 프롬프트의 평가를 담당한다. 실제 실행까지 필요하면 현재 요청에 `$prompt-coach`와 `$prompt-compiler`를 함께 선택해야 하며, Coach가 Compiler를 자동 호출한다고 가정하지 않는다. Prompt Coach를 한 작업 동안 계속 사용하려면 Prompt Compiler 플러그인의 첫 번째 시작 프롬프트로 그 동작을 요청한다. 이 문장은 현재 작업의 대화 지침이지만 `prompt-coach` 본문이 이후 모든 턴에 자동으로 다시 선택된다는 보장은 아니다. 모든 새 작업이나 메시지 제출 전 입력창에 자동 적용되는 전역 인터셉터도 아니다.

## 검증

```bash
python3 scripts/validate_all.py
python3 scripts/eval_routing.py validate
python3 scripts/eval_toolkit_search.py
python3 plugins/prompt-compiler/skills/prompt-coach/scripts/eval_harness.py validate
python3 plugins/prompt-compiler/skills/prompt-coach/scripts/eval_harness.py score plugins/prompt-compiler/skills/prompt-coach/evals/observed-results-2026-08-11.jsonl
python3 scripts/eval_uiux_search.py
python3 scripts/check_version_bumps.py --base <base-ref>
git diff --check
```

공통 검증기는 marketplace와 manifest 연결, 전체 스킬 메타데이터와 UI 자산, Python 구문, Prompt Compiler 평가 도구, Prompt Coach 정적 케이스와 독립 관찰 응답의 분리·채점, UI/UX 지식베이스 참조 무결성, 프론트엔드 도구 레지스트리 schema·역할·생태계·capability·surface·risk·fallback·출처 형식과 검색 회귀를 확인한다. Prompt Coach 평가는 사용자에게 보인 transcript에서 질문 수, 출력 표지와 실행·자동 연계 주장을 판정한다. 별도 tool trace가 없으면 실제 외부 side effect 부재의 증거로 사용하지 않는다. 외부 문서 URL의 실제 생존 여부, 현재 API와 라이선스는 스킬 실행 시 공식 출처에서 별도로 확인한다.

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
