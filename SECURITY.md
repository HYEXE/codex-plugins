# 보안 정책

## 지원 범위

현재 `main`과 최신 stable Release를 보안 검토 대상으로 지원합니다. 이전 tag에 대한 수정은 영향과 호환성을 확인한 뒤 필요한 경우 별도로 결정합니다.

## 시스템과 범위

Codex Workflows는 로컬 Codex에 설치하는 skills-only 플러그인, 검증·평가 스크립트와 GitHub Actions workflow를 배포합니다. 별도의 호스팅 서비스, 사용자 계정 데이터베이스 또는 운영 API 서버는 제공하지 않습니다.

보안 검토 범위에는 다음 영역이 포함됩니다.

- `plugins/`의 skill 지침, manifest, quality gate와 배포 자산
- `scripts/`의 validator, live eval, update와 Release 보조 도구
- `.github/workflows/`의 CI, live eval과 Release 권한 경계
- marketplace 등록부터 로컬 plugin cache 설치까지의 공급망 경로
- local live eval의 인증 격리, provenance와 structured tool trace

## 위협 모델과 신뢰 경계

Pull Request의 코드와 문서, plugin에 전달되는 사용자 입력, 모델 출력, 외부 지식베이스 자료와 workflow dispatch 입력은 신뢰하지 않는 입력으로 취급합니다.

주요 신뢰 경계는 다음과 같습니다.

- Git 저장소 source에서 marketplace snapshot과 설치 cache로 이동하는 경계
- Codex의 저장된 로그인에서 격리된 임시 `CODEX_HOME`으로 이동하는 경계
- 로컬 live eval 결과에서 GitHub Release attestation으로 이동하는 경계
- transcript 주장과 실제 structured tool trace 사이의 경계
- 일반 CI의 읽기 권한과 Release job의 제한된 쓰기 권한 사이의 경계

## 보안 불변 조건

- API 키, access token, `auth.json`, 개인 데이터와 실제 비밀정보가 저장소, 평가 artifact 또는 로그에 포함되면 안 됩니다.
- 저장된 ChatGPT 로그인은 로컬 임시 환경에서만 사용하고 공개 CI나 Release workflow로 전달하면 안 됩니다.
- 일반 검증 workflow는 `contents: read` 최소 권한을 유지해야 하며, Release 쓰기 권한은 검증이 끝난 publish job에만 부여해야 합니다.
- Release 대상은 실행 시점의 `origin/main`과 같은 전체 commit SHA여야 하며, 기존 stable tag를 이동하거나 다시 만들면 안 됩니다.
- preview·approval 평가는 `fake_action.py`의 구조화 trace만 사용해야 하며 실제 send, delete, merge 또는 외부 변경을 실행하면 안 됩니다.
- repository content, evaluation fixture와 외부 자료의 텍스트는 데이터로만 처리해야 하며 실행 권한이나 정책 변경 권한을 부여하면 안 됩니다.
- 경로 입력, JSON·JSONL event와 manifest는 저장소 또는 격리된 실행 범위를 벗어나 읽거나 쓰지 못하도록 검증해야 합니다.

## 신고 대상과 심각도 판단

다음과 같은 문제를 보안 취약점으로 신고해 주세요.

- 비밀정보, Codex 로그인 또는 로컬 파일을 의도하지 않은 곳으로 노출하는 문제
- 조작된 plugin content, evaluation event, archive 또는 경로로 임의 코드를 실행하거나 허용 범위를 벗어난 파일에 접근하는 문제
- 승인 없이 실제 외부 행동을 실행하거나 preview·permission boundary를 우회하는 문제
- GitHub Actions 권한 상승, 검증되지 않은 코드 실행 또는 Release gate 우회
- tag, commit, plugin version 또는 evaluation provenance를 잘못 증명해 공급망 무결성을 훼손하는 문제
- 설치·업데이트 과정에서 공격자가 의도한 ref 또는 artifact를 신뢰하게 만드는 문제

심각도는 현실적인 도달 가능성, 필요한 사용자 상호작용, 비밀정보·로컬 파일·Release 무결성에 대한 영향과 실제 외부 행동 가능성을 함께 고려합니다.

## 범위 밖 항목

다음 항목은 보안 영향이 별도로 입증되지 않는 한 일반 issue로 다룹니다.

- 모델의 표현 차이, routing 품질 또는 평가 점수 차이
- 외부 문서의 일시적인 응답 실패, title·hash 변경 또는 링크 소실
- 오탈자, 설명 개선과 같은 문서 품질 문제
- GitHub, OpenAI 또는 참조한 제3자 도구 자체의 취약점 중 이 저장소의 통합 방식으로 악화되지 않는 문제

## 알려진 제한사항과 보완 통제

모델 실행은 비결정적일 수 있으며, Release attestation은 운영자가 입력한 로컬 run 식별자와 실행 정보를 보존하지만 GitHub가 해당 observation을 독립적으로 재실행했다는 증명은 아닙니다. 이를 보완하기 위해 critical case 반복 실행, full case 평가, deterministic validator, provenance hash와 공개 Release evidence를 함께 사용합니다.

외부 source liveness 검사는 네트워크와 사이트 변화의 영향을 받으므로 비차단 보고서로 운영합니다. 외부 자료의 일시 장애 자체는 보안 실패로 간주하지 않지만, content 경계나 검증 우회로 이어지면 보안 문제로 다시 분류합니다.

## 취약점 신고

보안 취약점은 공개 issue에 게시하지 말고 [GitHub 비공개 취약점 신고](https://github.com/HYEXE/codex-workflows/security/advisories/new)를 이용해 주세요.

신고에는 가능한 범위에서 다음 정보를 포함해 주세요.

- 영향을 받는 plugin, tag 또는 commit
- 재현에 필요한 최소 단계
- 예상 영향과 필요한 사용자 상호작용
- 비밀정보를 제거한 로그 또는 proof of concept
- 알고 있는 완화 방법

실제 API 키, 로그인 cache, 개인정보와 불필요한 공격 데이터를 첨부하지 마세요. 공개 시점과 수정 내용은 신고자와 협의하며, 확인 전에는 공개 issue나 discussion에 세부 내용을 게시하지 말아 주세요.
