# Language Policy

Prompt Compiler v3.2-ko는 **한국어 semantic layer + 영어 canonical machine layer**를 사용한다.

## 목적

이 구조는 다음 두 목표를 동시에 만족시키기 위해 사용한다.

1. 한국어 사용자와 유지보수자가 Skill의 의미·규칙·예시를 자연스럽게 읽고 수정할 수 있게 한다.
2. schema, eval, script, tool routing에서 사용하는 기계 식별자는 안정적으로 유지한다.

## 한국어로 작성하는 영역

- `SKILL.md`의 자연어 지침
- `references/`의 설명과 판단 규칙
- README와 CHANGELOG의 설명
- 사용자 예시
- 사람이 읽는 eval 설명
- 사용자에게 보여주는 계획, 진단, 가정, 제한사항

## 영어로 유지하는 영역

### Canonical field names

예:
- `primary_outcome`
- `deliverables`
- `permission_boundary`
- `profile`
- `success_check`
- `depends_on`

### Enum / profile IDs

예:
- `direct`
- `research`
- `analysis`
- `writing`
- `coding`
- `artifact`
- `external_action`

### Permission IDs

- `read`
- `analyze`
- `draft`
- `edit`
- `send`
- `destructive`

### Evaluation labels

예:
- `pass_through`
- `single_node`
- `task_graph`
- `freshness`
- `sources`
- `artifact_exists`
- `action_result`

### Machine interfaces

- JSON Schema
- JSON/JSONL key
- script identifier
- CLI subcommand
- protocol/tool이 정확히 요구하는 identifier

## 작성 스타일

권장:

```text
권한 경계(permission boundary)를 확인한다.

사용자가 허용한 최대 `permission_level`을 넘지 않는다.
```

비권장:

```text
First 사용자의 intent를 extract한 다음 permission boundary를 check한다.
```

자연어 문장은 한국어로 완결하고, 정확한 machine identifier가 필요한 위치에서만 영어 canonical term을 사용한다.

## 새로운 identifier 추가 규칙

새 machine identifier를 추가할 때:

1. 영어 `snake_case` 또는 기존 protocol 형식을 사용한다.
2. 하나의 의미에 하나의 canonical identifier만 둔다.
3. README/reference에서는 처음 등장할 때 한국어 설명을 붙인다.
4. 기존 identifier를 번역 alias로 중복 생성하지 않는다.
5. enum 변경 시 schema와 eval harness를 함께 변경한다.

## Localization regression 방지

`evals/cases.jsonl`, schema, grader의 machine vocabulary는 번역 과정에서 바꾸지 않는다.

`machine-interface.sha256.json`과 `scripts/validate_localization.py`는 machine-critical 파일이 의도치 않게 변경되는 것을 감지한다.
