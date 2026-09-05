# 리허설과 fallback

## 리허설 매트릭스

최소한 다음 경로를 실제 발표 순서로 확인한다.

| 경로 | 확인 내용 |
| --- | --- |
| first run | 처음 열었을 때 표지와 초기 focus가 안정적이다. |
| normal forward | 다음 키가 정적 슬라이드와 blocking 장면에서 올바르게 동작한다. |
| replay | 현재 장면이 결정적인 초기 상태로 돌아가 같은 결과를 낸다. |
| skip | 재생 중 timer를 취소하고 다음 슬라이드로 이동한다. |
| backward | 이전 슬라이드로 돌아왔을 때 오래된 callback이 실행되지 않는다. |
| mode switch | experience와 demo 전환이 현재 장면 실행을 취소한다. |
| outline and hash | 목차와 URL 이동이 현재 장면을 정리한다. |
| offline | 원격 자산 없이 핵심 내용을 읽고 진행할 수 있다. |
| reduced motion | 같은 phase와 결과를 짧은 delay 또는 즉시 상태로 제공한다. |
| scene failure | 정적 요약과 다음 이동이 남는다. |

## Fallback 계층

1. `semantic summary`: JavaScript와 자산이 없어도 제목, 요약, 근거 경계를 읽을 수 있다.
2. `static visual`: animation 대신 단계 목록, 비교 표, poster 또는 도식이 남는다.
3. `manual control`: autoplay가 실패해도 단계 버튼이나 다음 슬라이드 이동을 사용할 수 있다.
4. `presenter recovery`: replay, skip, outline과 직접 hash 이동으로 발표를 이어간다.

원격 image, video, iframe과 API는 기본 발표의 필수 경로로 두지 않는다. 꼭 필요하면 로컬 poster와 실패 문구를 함께 제공하고 외부 연결이 실패해도 Deck Controller를 막지 않는다.

## Rehearsal Receipt 기록

복잡한 시연을 완료할 때 다음을 짧게 보고한다.

```text
mode tested:
slides and blocking scenes:
normal forward:
replay and skip:
navigation cleanup:
keyboard and touch:
reduced motion:
offline assets:
scene failure fallback:
browser and viewport:
unverified combinations:
```

실행하지 않은 경로는 `미검증`으로 남긴다. 정적 validator 통과를 실제 브라우저 시연 성공으로 표현하지 않는다.
