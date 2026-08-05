param(
    [ValidateSet("start","stop","restart","status","logs","watch","version","bump","release")]
    [string]$Action = "status",
    [string]$Level = "patch",
    [string]$Notes = ""
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

function Get-Version {
    $line = (Get-Content (Join-Path $Root "pyproject.toml") | Where-Object { $_ -match '^version\s*=' } | Select-Object -First 1)
    if ($line -match 'version\s*=\s*"([^"]+)"') {
        return $Matches[1]
    }
    return $null
}

function Show-Version {
    $v = Get-Version
    if ($v) {
        Write-Host "[version] $v"
        $tag = git -C $Root tag --points-at HEAD 2>$null
        if ($tag) { Write-Host "[version] Текущий тег: $tag" } else { Write-Host "[version] Тега на этом коммите нет" }
    } else {
        Write-Host "[version] Версия не найдена в pyproject.toml"
    }
}

function Bump-Version {
    param([string]$Part = "patch")
    $pyproject = Join-Path $Root "pyproject.toml"
    $v = Get-Version
    if (-not $v) { Write-Host "[bump] Версия не найдена."; return }

    $parts = $v.Split(".")
    if ($parts.Count -ne 3) { Write-Host "[bump] Неверный формат версии: $v"; return }

    switch ($Part.ToLower()) {
        "major" { $parts[0] = [int]$parts[0] + 1; $parts[1] = 0; $parts[2] = 0 }
        "minor" { $parts[1] = [int]$parts[1] + 1; $parts[2] = 0 }
        "patch" { $parts[2] = [int]$parts[2] + 1 }
        default { Write-Host "[bump] Уровень должен быть major|minor|patch"; return }
    }
    $new = $parts -join "."

    $content = Get-Content $pyproject -Encoding UTF8
    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match '^version\s*=') {
            $content[$i] = 'version = "' + $new + '"'
        }
    }
    Set-Content -Path $pyproject -Value $content -Encoding UTF8
    Write-Host "[bump] $v -> $new"
}

function New-Release {
    param([string]$Part = "patch", [string]$Notes = "")

    $gh = @(
        (Get-Command gh.exe -ErrorAction SilentlyContinue).Source,
        "C:\Program Files\GitHub CLI\gh.exe",
        "$env:ProgramFiles\GitHub CLI\gh.exe"
    ) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
    if (-not $gh) { Write-Host "[release] gh не найден. Установите GitHub CLI."; return }

    $env:GITHUB_TOKEN = $null
    Write-Host "[release] Проверяю авторизацию gh..."
    $auth = & $gh auth status 2>&1 | Out-String
    if ($auth -notmatch "Logged in" -and $auth -notmatch "^  X") {
        Write-Host "[release] gh не авторизован. Выполните gh auth login."; return
    }

    $dirty = git -C $Root status --porcelain
    if ($dirty) {
        Write-Host "[release] Рабочее дерево не чистое. Закоммитьте изменения сперва:"
        Write-Host $dirty
        return
    }

    Bump-Version -Part $Part
    $ver = Get-Version
    $tag = "v$ver"

    git -C $Root add pyproject.toml
    git -C $Root commit -m "Выпуск $tag"
    git -C $Root push

    if (& $gh tag --list $tag) {
        Write-Host "[release] Тег $tag уже существует."
    } else {
        git -C $Root tag -a $tag -m "Release $tag"
        git -C $Root push origin $tag
    }
    Write-Host "[release] Создаю GitHub release $tag..."
    if ($Notes) {
        & $gh release create $tag --title $tag --notes $Notes
    } else {
        & $gh release create $tag --title $tag --generate-notes
    }
    Write-Host "[release] Готово: https://github.com/Kerosyin/Morning-Companion/releases/tag/$tag"
}

switch ($Action) {
    "start"   { Start-Bot }
    "stop"    { Stop-Bot }
    "restart" { Restart-Bot }
    "status"  { Show-Status }
    "logs"    { Show-Logs }
    "watch"   { Watch-Logs }
    "version" { Show-Version }
    "bump"    { Bump-Version -Part $Level }
    "release" { New-Release -Part $Level -Notes $Notes }
}