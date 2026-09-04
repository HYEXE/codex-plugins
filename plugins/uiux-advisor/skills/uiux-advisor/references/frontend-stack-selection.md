# 프론트엔드 스택 선택

공식 문서 확인 기준일: 2026-09-04

이 문서는 인기 순위나 고정된 정답 스택을 제공하지 않는다. 현재 저장소, 사용자 과업과 운영 제약을 기준으로 필요한 계층만 선택하고, 구조화된 후보 정보는 `frontend-toolkit-registry.json`을 진실 원본으로 사용한다.

## 입력 계약

선택 전에 다음을 확인한다.

- 현재 framework, router, build tool, 상태 관리, form, schema, table과 test 도구
- SPA·MPA·SSR·SSG·streaming 중 필요한 rendering model
- SEO, 초기 응답, offline, 인증, 배포 runtime과 hosting 제약
- server data의 freshness·cache·mutation·revalidation 계약
- 공유 client state가 실제로 필요한 범위와 URL에 남겨야 하는 상태
- form 복잡도, server validation, progressive enhancement와 오류 복구
- 데이터 양, 정렬·필터·가상화·편집이 필요한 table 범위
- unit·component·browser·end-to-end 검증 책임
- 팀이 이미 운영할 수 있는 기술과 migration·rollback 비용

## 계층 모델

| 계층 | 먼저 답할 질문 | registry role |
| --- | --- | --- |
| application framework | content 중심인가, SPA인가, server 기능이 필요한가? | `application-framework` |
| build | framework가 build를 소유하는가, 별도 dev/build pipeline이 필요한가? | `build-tool` |
| routing | file route, data loader, typed search params가 필요한가? | `routing` |
| server state | cache, invalidation, mutation, offline·reconnect가 필요한가? | `server-state` |
| client state | component·URL·server state로 충분하지 않은 공유 상태인가? | `client-state` |
| form | field lifecycle, async validation, dirty·submit 상태가 복잡한가? | `form` |
| validation | client와 server 경계에서 같은 schema가 필요한가? | `validation` |
| data table | 정렬·필터·페이지·선택·가상화가 필요한가? | `data-table` |
| testing | 어떤 계층에서 어떤 사용자 위험을 검증할 것인가? | `testing` |

UI primitive, design system, motion, visualization과 interactive graphics는 기존 registry role을 이어서 사용한다.

## 선택 순서

1. 현재 package, lockfile, route 구조, rendering·deployment 설정과 테스트를 읽어 이미 해결된 계층을 표시한다.
2. 제품이 content 중심인지 application 중심인지, server rendering이나 server mutation이 실제로 필요한지 결정한다.
3. framework 제공 기능으로 routing, data loading, form action과 build를 충족할 수 있으면 겹치는 package를 추가하지 않는다.
4. server state와 client state를 분리한다. remote cache를 전역 store에 복제하거나 local interaction state를 query cache에 넣지 않는다.
5. 공유 가능한 상태는 URL, server, component local state 순으로 검토하고 전역 client store는 수명과 소유자가 분명할 때만 추가한다.
6. native form과 framework action으로 부족한 field lifecycle이 있을 때 form library를, 신뢰 경계 검증이 필요할 때 schema library를 별도로 선택한다.
7. semantic table로 충분한지 먼저 확인하고 headless data-table engine은 정렬·필터·페이지·가상화 상태가 실제로 복잡할 때 추가한다.
8. 기존 test runner를 유지하고, unit·component·browser E2E 사이의 검증 책임이 비어 있을 때만 새 도구를 추가한다.
9. 각 계층을 `search_toolkits.py --role <role> --ecosystem <ecosystem> --recommend --max-risk <risk>`로 검색한다. application framework를 처음 비교할 때는 risk 상한 없이 생태계에 정확히 맞는 후보를 확인한 뒤 허용 가능한 migration risk로 좁힌다.
10. framework가 form·state 같은 role로 검색되면 해당 내장 기능을 먼저 평가하라는 뜻이지, 현재 application에 그 framework를 추가하라는 뜻으로 해석하지 않는다.
11. 후보의 현재 공식 API, 설치 버전, SSR·hydration, browser 지원, license, bundle, migration과 제거 비용을 확인한다.

## 시작점별 경계

- React SPA: Vite와 React Router를 기본 비교점으로 삼고, typed route/search 계약이 핵심일 때 TanStack Router를 비교한다.
- React server application: Next.js 또는 React Router Framework Mode가 이미 제공하는 route·data 기능을 먼저 사용하고 중복 router와 client cache를 자동 추가하지 않는다.
- Vue: server·hybrid rendering이 필요하면 Nuxt, client SPA면 Vite와 Vue Router를 비교하고 Pinia는 공유 client state가 확인될 때만 추가한다.
- Svelte: 전체 application에는 SvelteKit의 route·load·form action을 먼저 검토하고 React 전용 package를 번역하지 않는다.
- Angular: Angular가 제공하는 routing, signals와 forms를 먼저 사용하고 같은 역할의 외부 layer를 중복하지 않는다.
- Content site: Astro의 server-first·islands 모델을 Next.js·Nuxt·SvelteKit과 콘텐츠 양, 개인화와 client interaction 예산으로 비교한다.
- Vanilla·Web Components: framework 없이 유지 가능한 수명과 복잡도인지 먼저 확인하고, 라이브러리 하나 때문에 application framework를 도입하지 않는다.

## 겹침과 충돌 검사

- Next.js App Router와 별도 React router가 같은 URL 소유권을 가지지 않게 한다.
- Nuxt·SvelteKit의 server data와 TanStack Query cache를 같은 진실 원본처럼 이중 관리하지 않는다.
- Redux Toolkit, Zustand, Pinia와 XState를 편의상 함께 추가하지 않고 각각의 소유 상태를 설명한다.
- form library의 client 오류와 server validation 오류를 하나의 field 계약으로 연결한다.
- Zod 같은 schema를 client bundle에 포함하기 전에 server-only 검증과 중복 여부를 확인한다.
- TanStack Table은 markup과 접근성을 대신하지 않으므로 caption, header association, keyboard와 responsive 대안을 별도로 구현한다.
- Vitest, Testing Library와 Playwright의 테스트 범위를 중복시키지 않고 실패를 가장 좁은 계층에서 진단한다.
- 전체 stack을 한 번에 교체하지 않는다. 독립적으로 검증하고 되돌릴 수 있는 migration 단위로 나눈다.

## Decision receipt

다음 형식으로 결과를 남긴다.

```text
결론과 신뢰도:
제품 과업과 rendering model:
현재 유지할 stack:
계층별 선택과 이유:
검토했지만 제외한 후보:
겹침·호환성 확인:
bundle·license·SSR·browser 영향:
migration과 rollback 단위:
실행한 검증:
미검증 항목과 다음 확인:
```

후보를 선택하지 않은 계층도 `기존 도구 유지`, `native 사용` 또는 `현재 필요 없음`으로 기록한다.
