<#
.SYNOPSIS
  Copy the master skills and common rules into dev-bingfa/<basic>/, then verify
  by SHA-256 that every copy equals its master.

.DESCRIPTION
  Invariant guarded here: the skills and AGENTS.md inside <basic>/ are always
  byte-identical to their masters:
    <plugin>/dev-bingfa/skills/<name>/**  ->  <basic>/.agents/skills/<name>/**  (whole folder,
                                            hidden files included, e.g. agents/openai.yaml)
    <rules>/AGENTS.md                    ->  <basic>/AGENTS.md
  (<plugin>, <rules>, <basic> = the package's plugin, rules and basic-tier
  folders, whose real names are Chinese; see the code points below.)
  Any file under <basic>/.agents/skills/ that has no master is reported as EXTRA.
  Exit code: 0 = all OK, 1 = at least one DIFF / MISSING / EXTRA.

  Windows PowerShell 5.1 compatible, no external dependencies. Chinese folder
  names are built from code points so this file parses correctly whether or
  not it is saved with a UTF-8 BOM.

.PARAMETER CheckOnly
  Verify only; do not copy anything.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\sync-basic.ps1
  powershell -ExecutionPolicy Bypass -File tools\sync-basic.ps1 -CheckOnly
#>
param([switch]$CheckOnly)

$ErrorActionPreference = 'Stop'

function Get-Cjk([int[]]$codes) { -join ($codes | ForEach-Object { [char]$_ }) }
$plugin = Get-Cjk 0x5916, 0x639B      # <plugin>
$rules  = Get-Cjk 0x898F, 0x5247      # <rules>
$basic  = Get-Cjk 0x57FA, 0x672C, 0x7248  # <basic>

$repo      = Split-Path -Parent $PSScriptRoot
$pkg       = Join-Path $repo 'dev-bingfa'
$skillsSrc = Join-Path $pkg (Join-Path $plugin 'dev-bingfa\skills')
$basicDir  = Join-Path $pkg $basic
$skillsDst = Join-Path $basicDir '.agents\skills'

foreach ($p in @($skillsSrc, (Join-Path $pkg $rules))) {
    if (-not (Test-Path -LiteralPath $p)) {
        Write-Host "ERROR: master folder not found: $p"
        exit 1
    }
}

# Build the master -> copy pairs.
$pairs = @()
foreach ($f in Get-ChildItem -LiteralPath $skillsSrc -Recurse -File -Force) {
    $rel = $f.FullName.Substring($skillsSrc.Length).TrimStart('\')
    $pairs += [pscustomobject]@{ Src = $f.FullName; Dst = (Join-Path $skillsDst $rel) }
}
$pairs += [pscustomobject]@{
    Src = (Join-Path $pkg (Join-Path $rules 'AGENTS.md'))
    Dst = (Join-Path $basicDir 'AGENTS.md')
}

if (-not $CheckOnly) {
    foreach ($p in $pairs) {
        $dir = Split-Path -Parent $p.Dst
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        Copy-Item -LiteralPath $p.Src -Destination $p.Dst -Force
    }
    Write-Host "Copied $($pairs.Count) file(s) into $basicDir"
}

function Get-Sha([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
}

$rows = @()
foreach ($p in $pairs) {
    $hs = Get-Sha $p.Src
    $hd = Get-Sha $p.Dst
    $status = if ($null -eq $hd) { 'MISSING' } elseif ($hs -eq $hd) { 'OK' } else { 'DIFF' }
    $rows += [pscustomobject]@{
        Status = $status
        Copy   = $p.Dst.Substring($pkg.Length).TrimStart('\')
        SHA256 = if ($hd) { $hd.Substring(0, 12) } else { '-' }
    }
}

# Files in the copy that have no master (e.g. a skill deleted from the master).
if (Test-Path -LiteralPath $skillsDst) {
    $expected = @{}
    foreach ($p in $pairs) { $expected[$p.Dst.ToLowerInvariant()] = $true }
    foreach ($f in Get-ChildItem -LiteralPath $skillsDst -Recurse -File -Force) {
        if (-not $expected.ContainsKey($f.FullName.ToLowerInvariant())) {
            $rows += [pscustomobject]@{
                Status = 'EXTRA'
                Copy   = $f.FullName.Substring($pkg.Length).TrimStart('\')
                SHA256 = (Get-Sha $f.FullName).Substring(0, 12)
            }
        }
    }
}

$rows | Format-Table -AutoSize | Out-String -Width 200 | Write-Host

$bad = @($rows | Where-Object { $_.Status -ne 'OK' })
if ($bad.Count -gt 0) {
    Write-Host "FAIL: $($bad.Count) of $($rows.Count) file(s) not equal to master."
    exit 1
}
Write-Host "PASS: all $($rows.Count) file(s) equal to master."
exit 0
