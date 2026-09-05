# 언어 정책

Interactive Slides는 **한국어 semantic layer와 영어 canonical machine layer**를 함께 사용한다.

## 목적

- 한국어 사용자와 유지보수자가 제작 판단, 안전 경계와 검증 기준을 자연스럽게 읽을 수 있게 한다.
- schema, validator, HTML·CSS·JavaScript와 eval이 사용하는 식별자는 번역으로 흔들리지 않게 유지한다.

## 한국어로 작성하는 영역

- `SKILL.md`의 자연어 실행 지침
- `references/`의 설명, 판단 규칙과 품질 기준
- template에서 사용자와 검토자가 읽는 안내 문장
- proposal, design plan과 검증 결과를 설명하는 사용자 메시지
- 사람이 읽는 접근성, fallback, 근거 경계와 리허설 설명

## 영어로 유지하는 영역

- 파일명과 경로
- JSON·frontmatter·HTML attribute의 field name
- `demo`, `experience`, `hybrid`, `ready` 같은 enum과 상태 ID
- `timeline`, `diagram`, `code-walkthrough`, `before-after` 같은 scene type
- 함수, class, CSS selector와 JavaScript identifier
- CLI command, option과 validator가 파싱하는 고정 heading
- schema, eval fixture와 자동화 계약에 포함된 canonical value

영어 canonical term이 필요한 문장에서는 한국어 설명을 완결한 뒤 정확한 식별자를 backtick으로 표시한다. 자연어 지침 전체를 영어로 작성하거나 하나의 식별자에 번역 alias를 추가하지 않는다.

## 변경 규칙

1. 자연어 문서를 번역해도 canonical field, enum과 parser-bound heading은 바꾸지 않는다.
2. machine identifier를 추가하면 처음 등장하는 reference에서 한국어 의미를 설명한다.
3. template의 안내 문구를 바꿀 때 proposal·design-plan validator와 forward fixture를 함께 실행한다.
4. 영어 자연어 단락을 새로 추가해야 한다면 외부 protocol 원문처럼 영어가 필수인 이유를 문서에 남긴다.
