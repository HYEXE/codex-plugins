# Codex Workflows

한국어 중심의 Codex·ChatGPT 워크플로를 독립적인 skills-only 플러그인으로 관리하는 모노레포다.

## 포함 플러그인

| 플러그인          | 번들 스킬          | 용도                                                                   |
| ----------------- | ------------------ | ---------------------------------------------------------------------- |
| `prompt-compiler` | `prompt-compiler`  | 자연어 요청을 의도·권한·제약을 보존한 최소 실행 구조로 컴파일하고 검증 |
| `uiux-advisor`    | `uiux-advisor`     | 공개 표준과 다중 출처를 활용한 한국어 UI/UX 설명·리뷰·명세·검증 계획   |

## 구조

```text
codex-workflows/
├── .agents/plugins/marketplace.json
├── plugins/
│   ├── prompt-compiler/
│   │   ├── .codex-plugin/plugin.json
│   │   └── skills/prompt-compiler/
│   └── uiux-advisor/
│       ├── .codex-plugin/plugin.json
│       └── skills/uiux-advisor/
└── scripts/validate_all.py
```

저장소와 marketplace는 하나지만 각 플러그인은 독립적으로 설치하고 버전을 관리한다. 스킬 원본은 각 플러그인의 `skills/` 아래에 한 번만 둔다.

## 검증

```bash
python3 scripts/validate_all.py
```

공통 검증기는 marketplace와 manifest 연결, 스킬 메타데이터, Python 구문, 각 패키지의 자체 검증과 대표 검색을 확인한다.

## 로컬 marketplace 사용

저장소 루트에서 marketplace를 등록한 뒤 필요한 플러그인을 설치한다.

```bash
codex plugin marketplace add .
codex plugin add prompt-compiler@codex-workflows-kr
codex plugin add uiux-advisor@codex-workflows-kr
```

설치 또는 업데이트 후에는 새 Codex 작업에서 동작을 확인한다.

## 배포 상태와 권리

- 현재 구성은 로컬 개발과 비공개 검증을 우선한다.
- `uiux-advisor`의 세부 출처는 `references/kb/SOURCE_REGISTRY.md`와 `sources.json`에 기록돼 있다.
- 코드, 자체 작성 콘텐츠, 제3자 자료 기반 콘텐츠의 라이선스는 공개 배포 전에 분리해 확정해야 한다.
- 이 저장소를 공개하거나 원격으로 push·배포하는 작업은 별도 승인 범위다.
