[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Marketplace = $env:CODEX_PLUGINS_MARKETPLACE,
    [string]$CodexPath = $env:CODEX_BIN
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Marketplace)) {
    $Marketplace = "codex-plugins-kr"
}

if ([string]::IsNullOrWhiteSpace($CodexPath)) {
    $CodexPath = "codex"
}

$Plugins = @("prompt-compiler", "uiux-advisor")

if (-not $DryRun -and -not (Get-Command $CodexPath -ErrorAction SilentlyContinue)) {
    throw "Codex CLI를 찾을 수 없습니다: $CodexPath. -CodexPath 또는 CODEX_BIN으로 실행 경로를 지정하세요."
}

function Invoke-CodexCommand {
    param([Parameter(Mandatory = $true)][string[]]$Arguments)

    Write-Host ("+ {0} {1}" -f $CodexPath, ($Arguments -join " "))
    if ($DryRun) {
        return
    }

    & $CodexPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Codex 명령이 종료 코드 $LASTEXITCODE 로 실패했습니다: $($Arguments -join ' ')"
    }
}

Invoke-CodexCommand -Arguments @("plugin", "marketplace", "upgrade", $Marketplace)
foreach ($Plugin in $Plugins) {
    Invoke-CodexCommand -Arguments @("plugin", "add", "${Plugin}@${Marketplace}")
}

if ($DryRun) {
    Write-Host "Dry run 완료: 실제 marketplace와 플러그인은 변경되지 않았습니다."
}
else {
    Write-Host "업데이트 완료: Codex를 재시작하거나 새 작업을 열어 변경 사항을 불러오세요."
}
