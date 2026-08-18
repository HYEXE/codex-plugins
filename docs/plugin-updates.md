# 플러그인 업데이트

`codex-plugins`의 Git marketplace와 설치된 플러그인은 각 사용자 PC에 snapshot과 cache로 저장된다. 저장소에 새 커밋을 push해도 설치본은 자동으로 바뀌지 않으므로, marketplace를 갱신한 뒤 두 플러그인을 다시 설치해야 한다. 아래 업데이트 스크립트는 주로 `main` nightly 채널을 위한 것이다.

업데이트 스크립트는 다음 명령을 순서대로 실행한다.

```text
codex plugin marketplace upgrade codex-plugins-kr
codex plugin add prompt-compiler@codex-plugins-kr
codex plugin add uiux-advisor@codex-plugins-kr
```

## 준비

Codex CLI가 설치돼 있어야 하며, marketplace는 PC마다 최초 한 번 등록해야 한다.

업데이트 스크립트를 사용하려면 저장소를 한 번 clone한다. Git marketplace 등록은 스크립트를 실행할 사용자 작업 복사본을 만들지 않는다.

```bash
git clone https://github.com/HYEXE/codex-plugins.git
cd codex-plugins
```

재현 가능한 stable 설치는 게시된 immutable repository tag를 사용한다.

```bash
codex plugin marketplace add HYEXE/codex-plugins --ref codex-plugins-vX.Y.Z
```

다음 릴리스를 확인하는 nightly 설치는 `main`을 사용한다.

```bash
codex plugin marketplace add HYEXE/codex-plugins --ref main
```

stable marketplace는 `upgrade`만으로 다음 stable tag로 이동하지 않는다. 새 릴리스로 올릴 때는 기존 marketplace 이름과 설치 상태를 확인한 뒤 marketplace를 제거하고 새 tag로 다시 등록한 다음 플러그인을 재설치한다.

```bash
codex plugin marketplace list
codex plugin marketplace remove codex-plugins-kr
codex plugin marketplace add HYEXE/codex-plugins --ref codex-plugins-vX.Y.Z
codex plugin add prompt-compiler@codex-plugins-kr
codex plugin add uiux-advisor@codex-plugins-kr
```

제거와 재등록은 로컬 Codex marketplace 설정을 바꾸므로 의도한 이름과 tag를 확인한 뒤 실행한다.

등록 상태는 다음 명령으로 확인한다.

```bash
codex plugin marketplace list
codex plugin list
```

## macOS와 Linux

저장소 루트에서 실행한다.

```bash
./scripts/update_plugins.sh
```

실행 권한이 없다면 다음 명령을 사용한다.

```bash
bash scripts/update_plugins.sh
```

실제 변경 없이 명령만 확인하려면 `--dry-run`을 사용한다.

```bash
./scripts/update_plugins.sh --dry-run
```

스케줄러에서 Codex CLI를 찾지 못하면 절대 경로를 지정한다.

```bash
CODEX_BIN=/absolute/path/to/codex ./scripts/update_plugins.sh
```

## Windows

PowerShell 7에서는 다음과 같이 실행한다.

```powershell
pwsh -NoProfile -File .\scripts\update_plugins.ps1
```

Windows PowerShell에서는 다음과 같이 실행한다.

```powershell
powershell.exe -NoProfile -File .\scripts\update_plugins.ps1
```

Dry run과 Codex CLI 절대 경로도 지원한다.

```powershell
pwsh -NoProfile -File .\scripts\update_plugins.ps1 -DryRun
pwsh -NoProfile -File .\scripts\update_plugins.ps1 -CodexPath "C:\absolute\path\to\codex.exe"
```

로컬 실행 정책이 스크립트를 차단하면 조직 정책을 우회하지 말고 관리자에게 허용된 실행 방법을 확인한다.

## 주기 자동화

자동 업데이트는 이후 이 저장소에 push되는 코드를 해당 PC가 신뢰하고 설치한다는 의미다. 저장소 접근 권한, 브랜치 보호와 업데이트 주기를 검토한 뒤 설정한다.

### macOS: launchd

`~/Library/LaunchAgents/com.hyexe.codex-plugins-update.plist`를 만들고 아래의 절대 경로를 현재 환경에 맞게 바꾼다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.hyexe.codex-plugins-update</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>/ABSOLUTE/PATH/codex-plugins/scripts/update_plugins.sh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>CODEX_BIN</key>
    <string>/ABSOLUTE/PATH/TO/codex</string>
  </dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>2</integer>
    <key>Hour</key>
    <integer>9</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>/tmp/codex-plugins-update.log</string>
  <key>StandardErrorPath</key>
  <string>/tmp/codex-plugins-update-error.log</string>
</dict>
</plist>
```

등록하고 즉시 한 번 실행한다.

```bash
launchctl bootstrap "gui/$(id -u)" ~/Library/LaunchAgents/com.hyexe.codex-plugins-update.plist
launchctl kickstart -k "gui/$(id -u)/com.hyexe.codex-plugins-update"
```

### Linux: cron

`crontab -e`에서 저장소와 Codex CLI의 절대 경로를 사용한다. 다음 예시는 매주 월요일 오전 9시에 실행한다.

```cron
0 9 * * 1 CODEX_BIN=/absolute/path/to/codex /absolute/path/to/codex-plugins/scripts/update_plugins.sh >> /tmp/codex-plugins-update.log 2>&1
```

### Windows: 작업 스케줄러

관리할 사용자 계정의 PowerShell에서 절대 저장소 경로를 지정한다. 다음 예시는 매주 월요일 오전 9시에 실행한다.

```powershell
$Repo = "C:\absolute\path\to\codex-plugins"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -File `"$Repo\scripts\update_plugins.ps1`""
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am
Register-ScheduledTask -TaskName "CodexPluginsUpdate" -Action $Action -Trigger $Trigger -Description "Update Codex Plugins"
```

처음에는 각 스크립트의 dry run을 실행하고, 스케줄러가 사용하는 계정과 환경에서 로그가 남는지 확인한다.

## 릴리스 운영

- 플러그인 코드를 변경할 때는 각 `.codex-plugin/plugin.json`의 버전을 증가시킨다.
- push 전 `python3 scripts/validate_all.py`를 실행한다.
- 업데이트 스크립트가 성공해도 기존 작업은 이전 스킬 snapshot을 사용할 수 있으므로 Codex를 재시작하거나 새 작업을 연다.
- 자동 업데이트 실패는 저장소 접근, 네트워크, Codex 로그인, CLI 경로와 스크립트 로그 순서로 확인한다.
