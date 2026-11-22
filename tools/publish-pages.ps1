[CmdletBinding()]
param([string]$Gh='gh')
$ErrorActionPreference='Stop'
$repo='yuxuan6426/clipsignal'
function Invoke-GhRequired([string[]]$CommandArgs) {
    $result = & $Gh @CommandArgs
    if ($LASTEXITCODE -ne 0) { throw ('GitHub command failed: ' + ($CommandArgs -join ' ')) }
    $result
}
$private = Invoke-GhRequired @('api',"repos/$repo",'--jq','.private')
if (($private | Out-String).Trim() -ne 'false') {
    throw 'Pages is gated on the owner making the repository public.'
}
$source = & $Gh api "repos/$repo/pages" --jq .build_type
if ($LASTEXITCODE -ne 0) {
    Invoke-GhRequired @('api','--method','POST',"repos/$repo/pages",'-f','build_type=workflow') | Out-Null
} elseif (($source | Out-String).Trim() -ne 'workflow') {
    Invoke-GhRequired @('api','--method','PUT',"repos/$repo/pages",'-f','build_type=workflow') | Out-Null
}
Invoke-GhRequired @('workflow','run','pages.yml','--repo',$repo,'--ref','main')
Invoke-GhRequired @('api',"repos/$repo/pages",'--jq','.html_url')