# Local launcher for the existing AhangBan project. No secrets are printed/copied.
# Run FROM the folder containing your existing .env, or pass -ProjectPath.
[CmdletBinding()]
param(
    [string]$ProjectPath = (Get-Location).Path,
    [switch]$Public,
    [switch]$Private,
    [switch]$NotMadeForKids,
    [switch]$ResumeOnly
)
$ErrorActionPreference = 'Stop'

if (($Public.IsPresent -and $Private.IsPresent) -or (-not $Public.IsPresent -and -not $Private.IsPresent)) {
    throw 'Choose exactly one: -Public or -Private. No upload has started.'
}
if (-not $NotMadeForKids.IsPresent) {
    throw 'Audience confirmation required: use -NotMadeForKids only if this video is NOT specifically made for children.'
}
$ProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$envFile = Join-Path $ProjectPath '.env'
if (-not (Test-Path -LiteralPath $envFile -PathType Leaf)) {
    throw 'Existing .env not found. Run from the AhangBan project folder, or pass -ProjectPath. Never send .env or credentials in chat.'
}
$node = (Get-Command node -ErrorAction Stop).Source
$major = & $node -p "Number(process.versions.node.split('.')[0])"
if ($LASTEXITCODE -ne 0 -or [int]$major -lt 22) {
    throw 'Node.js 22 or later is required (same as the existing dashboard).'
}
$work = Join-Path $ProjectPath 'rendered\youtube-publisher'
New-Item -ItemType Directory -Force -Path $work | Out-Null
$sourceRoot = 'https://github.com/Masoumiofficial/ahangban-youtube/raw/refs/heads/arena/d4ba4e0b-ahangban-youtube'
$files = @(
    @{
        Remote = 'tools/youtube-publisher.mjs'
        Name = 'youtube-publisher.mjs'
        Sha256 = '21c55224dcac409d8a13b8105e34709c996cd0429d3d2577abc35ca6108a227f'
    },
    @{
        Remote = 'tools/youtube-publish-job.json'
        Name = 'youtube-publish-job.json'
        Sha256 = 'e99c03622f40e0a1eabe61b89aeed5ae26d3ea65859dc926a1b478a36a310185'
    }
)
foreach ($entry in $files) {
    $destination = Join-Path $work $entry.Name
    $temporary = $destination + '.download'
    try {
        Invoke-WebRequest -UseBasicParsing -MaximumRedirection 10 -Uri ($sourceRoot + '/' + $entry.Remote) -OutFile $temporary
        $actual = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -ne $entry.Sha256) { throw 'Publisher download integrity check failed. Nothing will be uploaded.' }
        Move-Item -LiteralPath $temporary -Destination $destination -Force
    }
    finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}
$publisher = Join-Path $work 'youtube-publisher.mjs'
$job = Join-Path $work 'youtube-publish-job.json'
$visibility = '--private'
if ($Public.IsPresent) { $visibility = '--public' }
Write-Host 'Close the old dashboard window with Ctrl+C if it is still running.'
Write-Host 'A browser will ask for NEW Google upload permission. Choose the AhangBan owner account.'
Write-Host 'Do not send passwords, OAuth codes, tokens, or .env in chat.'
$extraArguments = @()
if ($ResumeOnly.IsPresent) { $extraArguments += '--resume-only' }
& $node "--env-file=$envFile" $publisher --job $job --project $ProjectPath $visibility --not-made-for-kids @extraArguments
if ($LASTEXITCODE -eq 2) { throw 'Upload status needs attention. Read the actual visibility/processing/thumbnail result above; do not create a duplicate upload.' }
if ($LASTEXITCODE -ne 0) { throw "Publisher stopped (exit $LASTEXITCODE). Share only its error code, not credentials." }
