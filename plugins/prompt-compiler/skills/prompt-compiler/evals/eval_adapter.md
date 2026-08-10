# Controlled Eval Adapter

controlled evaluation에서만 사용한다.

`cases.jsonl`의 한 case를 입력받아 Prompt Compiler v3.2-ko의 decision rule을 적용하되 private chain-of-thought를 노출하지 않는다.

`compiler-trace.schema.json`과 정확히 일치하는 JSON object 하나만 반환한다.

해석:
- `decomposition`: `pass_through`, `single_node`, `task_graph` 중 어떤 구조가 필요한가
- `node_count`: semantic execution node 수. private reasoning이나 문단 수는 포함하지 않음
- `profiles`: 실제로 필요한 canonical profile ID
- `permission_level`: 사용자의 요청이 허용하는 가장 강한 action 수준
- `asks_question`: 정확한 실행이 막혀 clarification이 필요한가
- `freshness`: `not_required`, `required`, `connected_private`
- `connected_data`: authorized private/connected data가 필요한가
- `artifact_planned`: native file/artifact가 최종 deliverable인가
- `external_write_planned`: send/create/update/delete side effect가 허용되었는가
- `verification`: 필요한 canonical verification label

JSON 밖의 설명은 출력하지 않는다.
