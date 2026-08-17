---
name: implement-ui-motion
description: 기존 프론트엔드에서 시간·공간 변화의 표현 자체가 주된 결과물인 모션과 마이크로인터랙션을 설계하고 CSS, Web Animations API, View Transition API, Anime.js, Motion 또는 GSAP 중 가장 단순한 기술로 구현·검증한다. 사용자가 애니메이션 적용, 버튼·카드의 시각 피드백, 페이지·레이아웃 전환, 스크롤·타임라인·SVG 모션, 라이브러리 선택, reduced-motion 또는 모션 성능 수정을 요청할 때 사용한다. 키보드·포커스·터치·제스처 입력은 implement-ui-interaction을, 요청·작업의 비동기 상태 정확성은 implement-async-ui-state를, 화면 구성은 compose-creative-ui를, 원칙·명세는 uiux-advisor를, 감사는 uiux-auditor를 사용한다.
---

# UI Motion Implementer

상태 변화와 인과관계를 설명하는 모션을 기존 제품 코드에 구현한다. 장식의 양보다 과업 명료성, 중단 가능성, 입력 연속성, 모션 감소 설정과 실제 렌더링 성능을 우선한다.

## 시작 절차

1. 저장소 지침과 변경 상태를 확인하고 대상 화면, 프레임워크, 렌더링 방식, 스타일 도구, 패키지 관리자, 브라우저 범위와 기존 모션 의존성을 읽는다.
2. 현재 동작을 실행하거나 코드로 확인한다. 관찰하지 않은 전이와 프레임 성능을 사실처럼 단정하지 않는다.
3. 구현 전에 다음 모션 계약을 짧게 고정한다.

   ```text
   사용자 목적:
   트리거와 시작·종료 상태:
   지속시간·지연·이징:
   중단·취소·역재생:
   애니메이션 중 입력·포커스:
   reduced-motion 대안:
   완료·실패 판정:
   ```

4. `../uiux-advisor/scripts/search_toolkits.py --role motion --ecosystem <ecosystem>`으로 구조화 후보를 확인한다.
5. `references/motion-toolkit-selection.md`를 읽고 현재 요구를 충족하는 가장 단순한 기술을 선택한다.
6. 구현과 검증 세부 기준이 필요하면 `references/motion-contract-and-qa.md`를 읽는다.

## 기술 선택 규칙

- 단순한 hover, focus, 표시·숨김과 한두 속성 전이는 CSS를 우선한다.
- JavaScript 재생 제어가 필요하지만 의존성 없이 해결되면 Web Animations API를 사용한다.
- 문서·라우트·레이아웃 상태 사이 전이가 핵심이면 지원 범위를 확인한 뒤 View Transition API를 검토한다.
- 여러 대상, 타임라인, SVG, stagger 또는 세밀한 시퀀스가 필요하면 Anime.js를 검토한다.
- React·Vue 중심의 선언형 모션, layout, gesture, spring이 핵심이면 Motion을 검토한다.
- 복잡한 스크롤 연동, 긴 타임라인과 정밀 제어가 실제 요구일 때 GSAP을 검토한다.
- 이미 설치된 적합한 도구가 있으면 새 라이브러리를 추가하지 않는다. 새 의존성은 현재 공식 문서, 잠금 파일, 라이선스, 번들·런타임 비용과 유지보수 상태를 확인한 뒤 추가한다.

사용자가 특정 라이브러리를 지목해도 더 단순한 네이티브 구현이 충분하거나 현재 프레임워크와 맞지 않으면 그 근거와 트레이드오프를 먼저 설명한다.

## 구현 규칙

- `transform`과 `opacity`만을 기계적으로 고집하지 말고 실제 레이아웃·페인트·합성 비용을 측정한다.
- 컴포넌트 해제, 라우트 변경, 빠른 반복 입력과 개발 모드 재실행에서 animation, listener, timer, observer를 정리한다.
- 열기와 닫기, 전진과 후진, 재진입, 중간 취소를 각각 처리한다.
- 애니메이션 완료 이벤트에만 핵심 상태 변경을 묶지 않는다. 모션이 생략되거나 취소돼도 최종 상태가 정확해야 한다.
- 포커스 이동, 키보드, pointer와 touch 입력을 모션이 가로막지 않게 한다.
- `prefers-reduced-motion`에서는 단순히 duration을 0으로 바꾸기보다 공간 이동, parallax, 자동 반복과 깜빡임을 제거하거나 의미 있는 정적 전이로 대체한다.
- SSR·hydration 환경에서는 서버와 첫 클라이언트 렌더의 구조가 달라지지 않게 한다.
- 스타일과 애니메이션 값을 기존 token·CSS variable·컴포넌트 상태와 연결한다.
- 기존 duration·easing token과 제품 선례를 우선한다. 근거가 없으면 새 수치를 보편 규칙처럼 확정하지 말고 조정 가능한 초기 가설로 표시한 뒤 실제 입력·성능 검증으로 조정한다.

## 검증

1. 프로젝트의 관련 테스트, 타입 검사와 린트를 실행한다.
2. 실제 브라우저에서 정상 완료, 빠른 반복, 중간 취소, 역방향, 뒤로 가기와 화면 크기 변화를 확인한다.
3. 키보드와 포커스 순서, 입력 가능 상태와 `prefers-reduced-motion: reduce`를 확인한다.
4. 모션 전후의 layout shift, long task, 과도한 paint와 낮은 성능 환경을 범위에 맞게 측정한다.
5. 새 패키지를 추가했다면 잠금 파일, 번들 변화, 라이선스와 사용하지 않는 import를 검토한다.
6. 구현한 기술, 선택 이유, reduced-motion 동작, 실행한 검증과 미검증 환경을 보고한다.

## 경계

- 모션이 필요한지와 제품 원칙만 결정하는 요청은 `uiux-advisor`로 보낸다.
- 기존 화면의 과도한 모션이나 접근성 문제만 찾는 요청은 `uiux-auditor`로 보낸다.
- 차트의 데이터 의미와 시각 인코딩이 중심이면 `build-data-visualization`을 사용한다.
- 여러 component가 공유하는 motion token과 공개 API를 시스템화하면 `build-design-system`을 함께 적용한다.
- hover·press·열기·닫기의 시간·공간 변화와 시각 피드백이 주목적이면 이 스킬을 사용한다.
- keyboard, focus, touch, gesture 인식과 widget 계약이 주목적이면 `implement-ui-interaction`을 사용한다. 시각 반응도 복잡하면 두 스킬의 계약을 함께 적용한다.
- 요청·stream·background job의 중복·취소·재시도와 상태 계약이 주목적이면 `implement-async-ui-state`를 사용한다.
- 랜딩 페이지의 배경·카드·텍스트 효과를 레지스트리에서 조합하는 작업은 `compose-creative-ui`를 사용하되, 복잡한 모션 구현이 생기면 이 스킬의 계약을 함께 적용한다.
