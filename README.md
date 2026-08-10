# Codex Workflows

한국어 중심의 Codex 워크플로를 독립적인 skills-only 플러그인으로 관리하는 모노레포다.

## 포함 플러그인

| 플러그인 | 번들 스킬 | 용도 |
| --- | --- | --- |
| `prompt-compiler` | `prompt-compiler`, `prompt-evaluator` | 요청을 안전한 최소 실행 구조로 컴파일하고 프롬프트 품질과 회귀 위험을 평가 |
| `uiux-advisor` | `uiux-advisor`, `uiux-auditor` | 근거 기반 UI/UX 설명·명세·계획과 화면·흐름 감사 |

## 구조

```text
codex-workflows/
├── .agents/plugins/marketplace.json
├── plugins/
│   ├── prompt-compiler/
│   │   ├── .codex-plugin/plugin.json
│   │   └── skills/
│   │       ├── prompt-compiler/
│   │       └── prompt-evaluator/
│   └── uiux-advisor/
│       ├── .codex-plugin/plugin.json
│       └── skills/
│           ├── uiux-advisor/
│           └── uiux-auditor/
└── scripts/validate_all.py
```

저장소와 marketplace는 하나지만 각 플러그인은 독립적으로 설치하고 버전을 관리한다. 각 스킬의 실행 지침과 필요한 resources는 해당 스킬 폴더에 둔다.

## 검증

```bash
python3 scripts/validate_all.py
git diff --check
```

공통 검증기는 marketplace와 manifest 연결, 전체 스킬 메타데이터와 UI 자산, Python 구문, Prompt Compiler 평가 도구, UI/UX 지식베이스와 대표 검색을 확인한다.

## GitHub marketplace 설치

```bash
codex plugin marketplace add HYEXE/codex-workflows --ref main
codex plugin add prompt-compiler@codex-workflows-kr
codex plugin add uiux-advisor@codex-workflows-kr
```

## 업데이트

저장소에 새 버전이 push된 뒤 각 사용 환경에서 Git marketplace snapshot을 갱신하고 플러그인을 다시 설치한다.

```bash
codex plugin marketplace upgrade codex-workflows-kr
codex plugin add prompt-compiler@codex-workflows-kr
codex plugin add uiux-advisor@codex-workflows-kr
```

설치 또는 업데이트 후에는 새 Codex 작업에서 동작을 확인한다.

## 로컬 개발

GitHub에 push하기 전 로컬 소스를 별도로 검증하려면 저장소 루트를 marketplace로 등록할 수 있다. 같은 이름의 Git marketplace가 이미 등록돼 있다면 충돌을 피하기 위해 기존 source를 먼저 확인한다.

```bash
codex plugin marketplace add /absolute/path/to/codex-workflows
```

## 배포 상태와 권리

- `uiux-advisor`의 세부 출처는 `references/kb/SOURCE_REGISTRY.md`와 `sources.json`에 기록돼 있다.
- 코드, 자체 작성 콘텐츠, 제3자 자료 기반 콘텐츠의 라이선스와 재배포 가능성은 공개 배포 범위에 맞게 별도로 검토한다.
- 실제 배포 전에는 현재 커밋의 검증 결과, 버전, 지원 범위와 지식베이스 최신성을 다시 확인한다.
