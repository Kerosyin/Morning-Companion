param(
    [ValidateSet("start","stop","restart","status","logs","watch")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "data\logs"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
$OutLog = Join-Path $LogDir "bot.out.log"
$ErrLog = Join-Path $LogDir "bot.err.log"

function Get-BotProcess {
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match 'app\.main' -and $_.CommandLine -match [regex]::Escape($Root) }
}

function Start-Bot {
    if (Get-BotProcess) {
        Write-Host "[start] Бот уже запущен."
        return
    }
    $env:PYTHONUTF8 = "1"
    $env:PYTHONIOENCODING = "utf-8"
    $env:PYTHONUNBUFFERED = "1"
    Start-Process -FilePath "uv" -ArgumentList "run","python","-m","app.main" `
        -WorkingDirectory $Root `
        -RedirectStandardOutput $OutLog `
        -RedirectStandardError $ErrLog `
        -WindowStyle Hidden
    Write-Host "[start] Бот запущен. Логи: $LogDir"
    Start-Sleep 3
    Show-Status
}

function Stop-Bot {
    $procs = Get-BotProcess
    if (-not $procs) {
        Write-Host "[stop] Бот не запущен."
        return
    }
    $procs | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Write-Host "[stop] Бот остановлен."
}

function Restart-Bot {
    Write-Host "[restart] Перезапуск..."
    Stop-Bot
    Start-Sleep 2
    Start-Bot
}

function Show-Status {
    $procs = Get-BotProcess
    if ($procs) {
        Write-Host "[status] Бот РАБОТАЕТ (PID: $($procs.ProcessId -join ', '))"
    } else {
        Write-Host "[status] Бот НЕ запущен."
    }
}

function Show-Logs {
    if (Test-Path $ErrLog) {
        Write-Host "=== ERR ===" -ForegroundColor Yellow
        Get-Content $ErrLog
    }
    if (Test-Path $OutLog) {
        Write-Host "=== OUT ===" -ForegroundColor Yellow
        Get-Content $OutLog
    }
}

function Watch-Logs {
    $files = @($ErrLog, $OutLog) | Where-Object { Test-Path $_ }
    if (-not $files) {
        Write-Host "[watch] Логи ещё не созданы. Запустите бота: bot-start"
        return
    }
    Write-Host "[watch] Слежу за логами. Живая активность ниже. Для выхода нажмите Ctrl+C." -ForegroundColor Cyan
    Get-Content $files -Tail 10 -Wait
}

switch ($Action) {
    "start"   { Start-Bot }
    "stop"    { Stop-Bot }
    "restart" { Restart-Bot }
    "status"  { Show-Status }
    "logs"    { Show-Logs }
    "watch"   { Watch-Logs }
}