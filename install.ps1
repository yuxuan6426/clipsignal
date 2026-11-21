[CmdletBinding()]
param(
    [ValidateSet('core','media','edit','leads','wechat','publish','outreach','all')][string]$Flow='core',
    [switch]$UserSkill,
    [string]$SkillHome
)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$encoding = New-Object System.Text.UTF8Encoding($false)
$entry = Join-Path $root '.agents/skills/clipsignal/SKILL.md'
$delivery = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $root 'delivery.json') | ConvertFrom-Json
if ($delivery.name -ne 'clipsignal' -or $delivery.schema_version -ne 1 -or
    '.agents/skills/clipsignal/SKILL.md' -notin $delivery.files -or 'setup.ps1' -notin $delivery.files) {
    throw 'This checkout does not contain the ClipSignal delivery manifest.'
}
foreach ($file in $delivery.files) {
    if ($file -notmatch '^[a-zA-Z0-9_.-]+(?:/[a-zA-Z0-9_.-]+)*$' -or
        ($file -split '/' | Where-Object { $_ -in @('.','..','.git','.local') }) -or
        -not (Test-Path -LiteralPath (Join-Path $root $file) -PathType Leaf)) {
        throw ('Invalid or missing release file: ' + $file)
    }
}
$report = & (Join-Path $root 'setup.ps1') -Check -Flow $Flow | Out-String | ConvertFrom-Json
$launcher = $null
if ($UserSkill) {
    if (-not $SkillHome) { $SkillHome = Join-Path $env:USERPROFILE '.agents/skills' }
    $folder = Join-Path ([IO.Path]::GetFullPath($SkillHome)) 'clipsignal'
    $launcher = Join-Path $folder 'SKILL.md'
    $body = @(
        '---', 'name: clipsignal',
        'description: "Load the installed ClipSignal trade research and content workflows."', '---', '',
        '# ClipSignal', '',
        ('<!-- clipsignal-workspace: ' + ($root | ConvertTo-Json -Compress) + ' -->'),
        ('Use ClipSignal checkout at ' + ($root | ConvertTo-Json -Compress) + ' as the working directory.'),
        ('Read and follow the complete project entry at ' + ($entry | ConvertTo-Json -Compress) + '.'),
        'Keep relative paths, companion skills, and tool execution anchored to that checkout.'
    ) -join "`n"
    if (Test-Path -LiteralPath $folder) {
        if (-not (Test-Path -LiteralPath $launcher -PathType Leaf) -or
            [IO.File]::ReadAllText($launcher).TrimEnd() -cne $body.TrimEnd()) {
            throw 'A different ClipSignal skill is already present. Use the project skill directly.'
        }
    } else {
        [void][IO.Directory]::CreateDirectory($folder)
        [IO.File]::WriteAllText($launcher, $body + "`n", $encoding)
    }
}
$receipt = [pscustomobject]@{
    workspace = $root
    entry = $entry
    version = $delivery.version
    userSkill = $launcher
    preflight = $report
}
$target = Join-Path $root '.local/config/install.json'
[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
$json = $receipt | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($target, $json, $encoding)
$json
