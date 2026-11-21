[CmdletBinding(DefaultParameterSetName='Check')]
param(
    [Parameter(ParameterSetName='Check')][switch]$Check,
    [Parameter(Mandatory,ParameterSetName='Apply')][switch]$Apply,
    [ValidateSet('core','media','edit','leads','wechat','publish','outreach','all')][string]$Flow='core',
    [string]$Python=$env:CLIPSIGNAL_PYTHON,
    [string]$Conda=$env:CONDA_EXE,
    [string]$JianyingRoot=$env:CLIPSIGNAL_JIANYING_ROOT,
    [string]$Gcc=$env:CLIPSIGNAL_GCC
)
$ErrorActionPreference = 'Stop'
$local = Join-Path $PSScriptRoot '.local'
$checks = New-Object 'System.Collections.Generic.List[object]'
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Find-App([string[]]$Candidates) {
    foreach ($candidate in $Candidates) {
        if (-not $candidate) { continue }
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return (Resolve-Path -LiteralPath $candidate).Path }
        $app = Get-Command -Name $candidate -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($app -and $app.Source -notmatch '\\WindowsApps\\python(?:3)?\.exe$') { return $app.Source }
    }
}
function Probe([string]$Executable, [string[]]$Arguments) {
    $local:ErrorActionPreference = 'Continue'
    $previousUtf8 = $env:PYTHONUTF8
    try {
        $env:PYTHONUTF8 = '1'
        & $Executable @Arguments 2>&1 | Out-Null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false } finally {
        $env:PYTHONUTF8 = $previousUtf8
    }

}
function Add-Check([string]$Id,[string]$State,[string]$Action) {
    $checks.Add([pscustomobject]@{id=$Id;state=$State;action=$Action})
}
function Test-Tool([string]$Id,[string]$Executable,[string[]]$Arguments,[string]$Install) {
    if (-not $Executable) { Add-Check $Id 'missing' $Install }
    elseif (Probe $Executable $Arguments) { Add-Check $Id 'ready' '' }
    else { Add-Check $Id 'broken' ('Inspect the installed ' + $Id + ' executable.') }
}
function Save-Local([string]$Path,[string]$Content) {
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($Path))
    [IO.File]::WriteAllText($Path,$Content,$utf8)
}
$node = Find-App @('node.exe','node')
$pwsh = Find-App @('pwsh.exe','pwsh')
$bash = Find-App @((Join-Path $env:ProgramFiles 'Git/bin/bash.exe'))
$condaLocations = @($env:USERPROFILE,$env:LOCALAPPDATA,$env:ProgramData) | ForEach-Object { Join-Path $_ 'miniconda3/Scripts/conda.exe' }
$condaExe = Find-App (@($Conda,'conda.exe') + $condaLocations)
$managedPython = Join-Path $local 'envs/wechat/python.exe'
$pythonExe = Find-App @($Python,$managedPython,'python.exe')
Test-Tool 'git-bash' $bash @('--version') 'Install Git for Windows.'
Test-Tool 'pwsh' $pwsh @('-NoProfile','-Command','if ($PSVersionTable.PSVersion.Major -lt 7) {exit 1}') 'Install PowerShell 7.'
Test-Tool 'conda' $condaExe @('--version') 'Install Miniconda or supply -Conda.'
Test-Tool 'node' $node @('-e',"if(typeof require('node:util').parseEnv!=='function')process.exit(1)") 'Install a supported Node.js release.'
if ($Flow -in @('media','edit','all')) {
    if ($env:CLIPSIGNAL_MEDIA_ROOT -and (Test-Path -LiteralPath (Join-Path $env:CLIPSIGNAL_MEDIA_ROOT 'scripts/da.py'))) {
        Add-Check 'media-runtime' 'unverified' 'Run the upstream status command and an authorized Agent Plan sample.'
    } else { Add-Check 'media-runtime' 'missing' 'Install douyin-agent and set CLIPSIGNAL_MEDIA_ROOT.' }
    Add-Check 'agent-plan' 'needs-auth' 'Verify the recipient account using an authorized sample.'
}
if ($Flow -in @('edit','all')) {
    $dev = Join-Path ([Environment]::GetEnvironmentVariable('ProgramFiles(x86)')) 'Dev-Cpp/MinGW64/bin/gcc.exe'
    $gccExe = Find-App @($Gcc,'gcc.exe',$dev)
    if ($gccExe) {
        $target = (& $gccExe -dumpmachine 2>$null | Out-String).Trim()
        if ($LASTEXITCODE -eq 0 -and $target -eq 'x86_64-w64-mingw32') { Add-Check 'gcc' 'ready' '' }
        else { Add-Check 'gcc' 'broken' 'Provide the x64 MinGW GCC executable.' }
    } else { Add-Check 'gcc' 'missing' 'Install Dev-C++ with x64 MinGW GCC or set CLIPSIGNAL_GCC.' }
    if (-not $JianyingRoot) { $JianyingRoot = Join-Path $env:LOCALAPPDATA 'JianyingDraftCollab' }
    $run = Join-Path $JianyingRoot 'run.ps1'
    if (-not (Test-Path -LiteralPath $run -PathType Leaf)) {
        Add-Check 'jianying' 'missing' 'Install the Jianying draft runtime or supply -JianyingRoot.'
    } else {
        $shell = Find-App @($pwsh,'powershell.exe')
        $previousPreference = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $report = (& $shell -NoProfile -File $run draft doctor 2>$null | Out-String) | ConvertFrom-Json
            if ($report.status -eq 'ready' -or $report.state -eq 'ready') { Add-Check 'jianying' 'ready' '' }
            else { Add-Check 'jianying' 'broken' 'Run the upstream native probe for this installation.' }
        } catch { Add-Check 'jianying' 'broken' 'Run the upstream draft doctor for this installation.' }
        finally { $ErrorActionPreference = $previousPreference }
    }
}
if ($Flow -in @('leads','publish','all')) { Add-Check 'chrome' 'needs-auth' 'Verify Chrome plugin access to the target page.' }
if ($Flow -in @('leads','all')) { Add-Check 'bocha' 'needs-auth' 'Configure BOCHA_API_KEY and verify one authorized search.' }
if ($Flow -in @('outreach','all')) {
    Add-Check 'gmail' 'needs-auth' 'Verify the recipient Gmail account.'
    Add-Check 'cloudbat' 'needs-auth' 'Configure YUNFU_MCP_TOKEN and verify the account and line.'
}
if ($Flow -in @('wechat','all')) {
    $imports = 'import sys; assert sys.version_info[:2] == (3, 13); import fastapi, uvicorn, mcp, httpx, pydantic, win32gui, comtypes, psutil'
    if ($Apply -and -not $Python -and $condaExe -and -not (Test-Path -LiteralPath $managedPython)) {
        if (Probe $condaExe @('create','--yes','--override-channels','-c','conda-forge','--prefix',(Split-Path -Parent $managedPython),'python=3.13','pip')) {
            if (Test-Path -LiteralPath $managedPython) { $pythonExe = $managedPython }
        }
    }
    if ($Apply -and $pythonExe -eq $managedPython -and -not (Probe $pythonExe @('-c',$imports))) {
        [void](Probe $pythonExe @('-m','pip','install','-r',(Join-Path $PSScriptRoot 'modules/wechat/requirements.txt')))
    }
    if (-not $pythonExe) { Add-Check 'wechat' 'missing' 'Run -Apply -Flow wechat with Miniconda or pass a prepared -Python.' }
    elseif (Probe $pythonExe @('-c',$imports)) { Add-Check 'wechat' 'ready' '' }
    else { Add-Check 'wechat' 'broken' 'Use the project Python 3.13 environment with the Workbench requirements.' }
}
$result = [pscustomobject]@{schemaVersion=1;flow=$Flow;checks=@($checks.ToArray())}
$json = $result | ConvertTo-Json -Depth 6
if ($Apply) {
    $state = if (@($checks | Where-Object state -ne 'ready').Count) { 'needs-auth' } else { 'ready' }
    if (@($checks | Where-Object { $_.state -in @('missing','broken') }).Count) { $state = 'blocked' }
    Save-Local (Join-Path $local 'config/setup.json') $json
    Save-Local (Join-Path $local 'runs/workspace.json') (@{state=$state} | ConvertTo-Json -Compress)
}
$json
