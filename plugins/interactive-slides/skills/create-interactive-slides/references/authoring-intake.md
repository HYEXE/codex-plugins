# 제작 입력과 모드 고정

스토리보드를 작성하거나 UI를 생성하기 전에 발표 계약을 선택한다.

## 필수 사전 확인

첫 요청에 다음 정보가 없다면 누락된 항목만 확인한다.

- 발표 목적과 청중이 얻어야 할 한 문장 결과
- 청중, 장소, 발표 시간과 예상 기기
- 원본 자료와 필수 근거 경계
- 발표 모드: `demo` 또는 `experience`
- 브랜드 자산 또는 하나의 시각 방향
- 오프라인, hosting과 browser 제약

결정되지 않은 항목만 질문한다. 모드가 없다면 slide 제작 전에 한 번의 짧은 선택 질문을 한다.

- `demo`: 발표자가 순서와 timing을 제어하며 replay와 skip을 제공하는 모드
- `experience`: 청중이 직접 탐색하고 조작하며 reset할 수 있는 모드

두 모드를 추측으로 모두 만들지 않는다. 납품 발표에 mode switch를 노출하지 않는다. 사용자가 명시적으로 요청한 경우에만 hybrid deck을 허용하고, 전역 runtime toggle을 추가하는 대신 storyboarding 단계에서 slide별 모드를 정한다.

## 제작 계약

선택된 모드를 brief, production proposal, design plan과 storyboard에 기록한다. 생성 문서에는 선언적으로 설정한다.

```html
<html lang="ko" data-presentation-mode="demo">
```

Experience deck은 `experience`를 사용한다. Starter는 시작할 때 이 값을 한 번 읽고 presentation chrome에서 제작 전용 mode control을 제거한다.

### Demo 모드

- slide 진행은 발표자가 제어한다.
- blocking scene은 `ready`, `running`, `complete` 상태를 가져야 한다.
- timer나 stale callback을 남기지 않는 replay와 skip을 제공한다.
- 핵심 의미는 정적 fallback에서도 보이게 한다.
- timing과 speaking cue는 presenter note에 기록한다.

### Experience 모드

- 주 interaction을 직접 보이고 별도 설명 없이 이해할 수 있게 한다.
- reset과 결정론적인 초기 상태를 제공한다.
- autoplay나 숨은 keyboard 지식을 요구하지 않는다.
- 청중이 탐색하는 동안에도 slide navigation을 유지한다.
- touch target과 mobile layout을 사용할 수 있게 유지한다.

## 인수 검사

Brief, proposal, design plan, storyboard와 document mode가 서로 다르거나 명시적인 hybrid 요구 없이 runtime mode toggle이 남아 있으면 생성된 deck을 거부한다.
