# Intent Frame

Intent Frame은 사용자가 실제로 달성하려는 것을 간결한 의미 구조로 표현한 내부 IR이다.

재작성된 프롬프트가 아니며 기본적으로 사용자에게 노출하지 않는다.

## 필드

필요한 필드만 사용한다.

### `primary_outcome`

사용자가 원하는 최종 상태.

좋은 예:
- "3개의 정책 대안을 의사결정 가능한 수준으로 비교한다."
- "UI를 변경하지 않고 대소문자 검색 버그를 수정한다."

나쁜 예:
- "분석한다."
- "도움을 준다."

### `deliverables`

사용자가 실제로 기대하는 산출물.

예:
- 답변
- 비교표
- 이메일 초안
- 수정된 코드
- 테스트 결과
- spreadsheet
- slide deck
- calendar event

### `use_context`

사용 목적이 결과 내용에 영향을 줄 때만 기록한다.

예:
- 팀장 브리핑
- vendor 선정
- production merge review
- 과제 제출

구체적으로 보이기 위해 사용 맥락을 임의로 만들지 않는다.

### `inputs`

사용자가 제공했거나 접근을 허용한 자료.

예:
- text
- file
- URL
- repository
- connected email/calendar/docs
- dataset

### `hard_constraints`

반드시 유지해야 하는 조건.

예:
- "UI는 변경하지 마."
- "정부 원문 우선."
- "500자 이내."
- "초안만 작성하고 보내지는 마."

### `soft_preferences`

정확성이나 hard constraint보다 우선하지 않는 선호.

예:
- 간결하게
- 공식적인 문체
- 시각적으로
- 기존 dependency 우선

### `scope`

포함/제외 범위, 기간, 지역, 관할, 파일, module, entity 등.

### `permission_boundary`

사용자가 명시적으로 허용한 가장 강한 action 수준.

예:
- `read`
- `analyze`
- `draft`
- 특정 artifact `edit`
- 특정 수신자에게 `send`
- 특정 calendar event `create`

낮은 권한에서 더 높은 권한을 추론하지 않는다.

### `evidence_expectation`

필요할 때만 사용한다.

예:
- 외부 근거 불필요
- 제공된 자료만 사용
- 현재 사실 검증 필요
- primary source 우선
- citation 필요

### `output_contract`

언어, 문체, 구조, file type, schema, 길이, dimension 등.

### `uncertainty`

실행에 영향을 주는 미해결 정보만 기록한다.

분류:
- `blocking`
- `resolvable_from_context_or_tools`
- `safe_to_assume`
- `non_material`

## Intent Fidelity Test

유효한 Intent Frame이라면 합리적인 사용자가 다음과 같이 말할 수 있어야 한다.

> "맞아. 내가 요청한 게 그거야."

새로운 business requirement, 권한, audience, deadline, deliverable을 임의로 추가했다면 제거한다.
