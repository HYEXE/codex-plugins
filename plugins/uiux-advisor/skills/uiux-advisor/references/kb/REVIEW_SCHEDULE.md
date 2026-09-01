# UI/UX 지식과 toolkit 재검토 일정

이 일정은 같은 snapshot date에 집중된 freshness 만료를 실제 검토 작업으로 분산한다. 날짜만 미루지 않으며 source를 다시 확인하고 필요한 내용을 반영한 경우에만 `snapshot_date` 또는 `checked_on`을 갱신한다.

## 현재 freshness 경계

| 대상 | 현재 기준일 | warning 시작 | error 시작 |
| --- | --- | --- | --- |
| time-sensitive guide 6개 | 2026-08-06 | 2026-11-05 | 2027-02-03 |
| stable guide 44개 | 2026-08-06 | 2027-08-07 | 2028-08-06 |
| toolkit 38개 | 2026-08-11~18 | 2027-02-08부터 | 2027-08-12부터 |

검증기는 freshness budget을 초과한 항목을 계속 warning 또는 error로 처리한다. 이 문서는 budget을 늘리기 위한 근거가 아니다.

## Time-sensitive guide

| 목표일 | 대상 | 검토 초점 |
| --- | --- | --- |
| 2026-09-30 | `uiux-playbook-005`, `uiux-playbook-019` | 인간-AI 경험, system status와 loading 관례 |
| 2026-10-15 | `uiux-playbook-034`, `uiux-playbook-043` | reduced motion, 제품·과업 metric |
| 2026-10-30 | `uiux-playbook-044`, `uiux-playbook-050` | experimentation 근거 품질, web performance 기준 |

## Frontend toolkit registry

하나의 toolkit이 여러 role을 가질 수 있으므로 각 batch는 해당 role의 중복 항목을 한 번만 검토한다.

| 목표일 | role batch |
| --- | --- |
| 2026-10-30 | `motion`, `interaction` |
| 2026-11-30 | `data-visualization`, `creative-ui` |
| 2026-12-31 | `interactive-graphics`, `primitive` |
| 2027-01-31 | `design-system`, `documentation`, `testing` |

## Stable guide

아래 batch에서는 해당 category의 `time_sensitive: false` record만 검토한다.

| 목표일 | category batch |
| --- | --- |
| 2026-12-15 | 전략·윤리, 리서치·발견 |
| 2027-02-15 | 정보구조·콘텐츠, 컴포넌트·패턴 |
| 2027-04-15 | 상호작용·흐름, 시각·반응형 |
| 2027-06-15 | 접근성·포용, 검증·지표, 시스템·전달 |

## 완료 증거

각 batch는 다음 조건을 만족해야 완료된다.

1. 사용된 source URL과 공식 문서의 현재 내용을 다시 확인한다.
2. 변경된 지침, toolkit status, license 또는 fallback을 record와 Markdown에 반영한다.
3. 실제 검토일만 `snapshot_date` 또는 `checked_on`에 기록한다.
4. 변경이 없더라도 확인한 source와 결론을 commit 또는 Pull Request 검증 기록에 남긴다.
5. `python3 plugins/uiux-advisor/.codex-plugin/validators/validate_content.py`와 `python3 scripts/validate_all.py`를 실행한다.
