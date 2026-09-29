param(
    [string]$HostName = "89.124.101.154",
    [string]$RemoteUser = "root",
    [string]$RemoteBackupDirectory = "/home/bigbrick/backups/morning-companion",
    [string]$KeyPath = (Join-Path $env:USERPROFILE ".ssh\id_ed25519"),
    [string]$DestinationDirectory = (
        Join-Path (Split-Path -Parent $PSScriptRoot) "secret\vps-backups"
    )
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $KeyPath -PathType Leaf)) {
    throw "SSH key was not found: $KeyPath"
}

New-Item -ItemType Directory -Force -Path $DestinationDirectory | Out-Null

$remoteCommand = @"
find '$RemoteBackupDirectory' -maxdepth 1 -type f -name 'morning-companion-*.tar.gz' -printf '%T@ %p\n' |
    sort -rn | head -n 1 | cut -d' ' -f2-
"@
$remoteArchive = (
    & ssh.exe -i $KeyPath -o BatchMode=yes -o PasswordAuthentication=no `
        "$RemoteUser@$HostName" $remoteCommand
).Trim()

if ($LASTEXITCODE -ne 0 -or -not $remoteArchive) {
    throw "Could not find a VPS backup archive."
}

$expectedPrefix = "$RemoteBackupDirectory/morning-companion-"
if (-not $remoteArchive.StartsWith($expectedPrefix) -or -not $remoteArchive.EndsWith(".tar.gz")) {
    throw "Unexpected remote backup path."
}

$destination = Join-Path $DestinationDirectory (Split-Path -Leaf $remoteArchive)
& scp.exe -i $KeyPath -o BatchMode=yes -o PasswordAuthentication=no `
    "${RemoteUser}@${HostName}:$remoteArchive" $destination
if ($LASTEXITCODE -ne 0) {
    throw "Could not download the VPS backup archive."
}

Get-ChildItem -LiteralPath $DestinationDirectory -Filter "morning-companion-*.tar.gz" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -Skip 3 |
    Remove-Item -Force

Write-Output "Downloaded $destination"
