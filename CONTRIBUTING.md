# 기여 안내

Codex Plugins에 관심을 가져 주셔서 감사합니다. 이 저장소는 플러그인 콘텐츠를 코드처럼 검증하고, 배포되는 변경을 재현 가능한 버전과 평가 결과로 관리합니다.

## 시작하기

1. 저장소를 fork하거나 작업 브랜치를 만들어 주세요.
2. 변경하려는 플러그인의 `README.md`, `CHANGELOG.md`, `.codex-plugin/plugin.json`, `quality-gates.json`을 먼저 확인해 주세요.
3. 관련 코드, 평가 fixture, validator를 함께 수정해 주세요.
4. 아래 검증을 실행하고 실제 결과를 Pull Request에 기록해 주세요.

```bash
python3 scripts/validate_all.py
python3 -m unittest discover -s tests -p "test_*.py"
python3 scripts/live_eval.py validate
git diff --check
```

Shell 스크립트를 변경했다면 ShellCheck를, PowerShell 스크립트를 변경했다면 Windows 또는 PowerShell 환경의 dry run을 추가로 확인해 주세요.

## 플러그인 변경 규칙

- 플러그인에 배포되는 파일이 바뀌면 해당 `.codex-plugin/plugin.json`의 SemVer를 올려 주세요.
- 사용자에게 보이는 동작이 바뀌면 해당 플러그인의 `CHANGELOG.md`를 갱신해 주세요.
- routing 또는 orchestration fixture가 바뀌면 observation과 metadata hash를 함께 갱신해 주세요.
- 새 플러그인별 검증 규칙은 중앙 validator에 하드코딩하지 말고 `.codex-plugin/quality-gates.json`에 선언해 주세요.
- API 키, 로그인 cache, 실제 transcript의 민감정보와 개인 로컬 경로를 커밋하지 마세요.

## 커밋과 Pull Request

커밋과 Pull Request 제목은 가능한 경우 Conventional Commits 형식을 사용해 주세요.

```text
<type>(<scope>): <변경 결과>
```

Pull Request에는 변경 이유, 사용자 영향, 실행한 검증, 미실행 검증과 알려진 제한사항을 적어 주세요. 플러그인 동작을 바꾸는 변경은 관련 평가 사례와 함께 제출해 주세요.

## 보안 문제

보안 취약점은 공개 issue에 작성하지 마세요. [보안 정책](SECURITY.md)의 비공개 신고 절차를 이용해 주세요.

## 라이선스

기여한 코드와 콘텐츠는 저장소의 [Apache License 2.0](LICENSE)에 따라 배포되는 데 동의한 것으로 간주합니다. 제3자 자료를 복사하거나 각색했다면 출처와 재배포 조건을 명확히 기록해 주세요.
