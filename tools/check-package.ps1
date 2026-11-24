<#
.SYNOPSIS
  Run every dev-bingfa package invariant and print a PASS / FAIL / SKIPPED table.

.DESCRIPTION
  Maintainer tool; not shipped to colleagues. Checks:
    1. basic-sync    tools\sync-basic.ps1 -CheckOnly passes (basic tier == master).
    2. rules-twin    <rules>\AGENTS.md is byte-identical to <rules>\CLAUDE.md.
    3. agent-files   exactly the three expected Claude agents (<plugin>\dev-bingfa\agents\*.md,
                     no other files there) and exactly the three expected Codex agents
                     (codex\agents\bingfa-<name>.toml, no other files there).
    4. agent-twin    each Codex TOML agent has only the keys name / description /
                     developer_instructions, name == file name, the same description as its
                     Claude agent, and developer_instructions == the Claude body except for the
                     whole lines listed in $AllowedDiffs (matched by SHA-256 of the trimmed line;
                     done by tools\check-agents.py).
                     Each Claude agent's frontmatter has only name / description.
                     Needs Python 3.11+ (tomllib); without it the row is SKIPPED.
    5. check-silence <plugin>\dev-bingfa-check\hooks\check_silence.py has the recorded
                     SHA-256 (the owner's original; it must never be edited).
    6. version       VERSION (e.g. 1.0) matches "version" in both plugin.json files (1.0.0).
    7. line-endings  every .sh is LF only, every .cmd is CRLF only
                     (under dev-bingfa\, excluding the third-party offline copy).
    8. json          every *.json under dev-bingfa\ (excluding the offline copy) parses.
    9. hooks-json    hooks.json has exactly SessionStart + PostToolUse, matcher "Write|Edit" on
                     PostToolUse only, one command hook each with timeout 10, `command` calls
                     run.sh and run.cmd with the right argument, and the exact `commandWindows`.
   10. marketplace   marketplace.json lists exactly dev-bingfa and dev-bingfa-check, and each
                     "source" folder has a plugin.json with the same name.
   11. commit-manual skills\commit\SKILL.md has `disable-model-invocation: true` and
                     skills\commit\agents\openai.yaml exists with `allow_implicit_invocation: false`.
   12. search-modules exactly the five expected web-search-modules\*.md, each non-empty and
                     starting with a "# " heading.
   13. hook-matrix   tools\test-hooks.py (runs hooks.json the way Claude Code and Codex do, with /
                     without / with too-old Python, malformed input, multi-file and 300-file
                     patches). SKIPPED when Python 3.8+ or Git's sh is missing.
  Exit code: 0 = all PASS, 1 = at least one FAIL, 2 = no FAIL but something SKIPPED.

  Windows PowerShell 5.1 compatible. This file is ASCII only: Chinese folder names
  are built from code points (same technique as sync-basic.ps1).

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\check-package.ps1
#>
$ErrorActionPreference = 'Stop'

# SHA-256 of the owner's original check_silence.py (recorded 2026-11-24).
$CheckSilenceSha = 'FF5640ACBCF50B74B90E5FADA003A48F7E52CDC0F8ADC05DD6775DE05C604C39'

# Whole lines allowed to differ between a Claude agent body and its Codex twin, as SHA-256
# (upper-case hex, UTF-8) of the trimmed line. Each hash must match exactly one line on its side.
# When a line is changed on purpose, the agent-twin FAIL detail prints the new hashes.
$AllowedDiffs = @(
    # "Before executing any WebSearch or WebFetch ..." / "Before running any web search ..." (module location)
    @{ agent = 'web-search-agent';
       claude = '1724276F97E456E405DF8369EEBAA4606D93EBF25C3EC46F7C8E88836879D9F7';
       codex  = 'A980497A79BD9C631D5314E18D2AE8681072CBAFE0525D90A159E506EFC71419' },
    # "DO NOT skip this step. DO NOT call WebSearch ..." / "... DO NOT run any web search ..."
    @{ agent = 'web-search-agent';
       claude = '0449BD187586A8C6C87902061CBEF6948F6A95D19648BC302C0B22A60826B224';
       codex  = 'FA3C96AD42D188523F11FF8078DCF92A3709AF584C89A5EAEE8B5D4D5D93A983' }
)
$AgentNames = @('explorer', 'implementer', 'web-search-agent')
$SearchModules = @('academic-papers.md', 'chinese-tech.md', 'general-web.md', 'github-debug.md', 'stackoverflow.md')

function Get-Cjk([int[]]$codes) { -join ($codes | ForEach-Object { [char]$_ }) }
$plugin  = Get-Cjk 0x5916, 0x639B              # <plugin>
$rules   = Get-Cjk 0x898F, 0x5247              # <rules>
$offline = Get-Cjk 0x96E2, 0x7DDA, 0x526F, 0x672C  # <offline copy>

$repo = Split-Path -Parent $PSScriptRoot
$pkg  = Join-Path $repo 'dev-bingfa'
$plug = Join-Path $pkg $plugin
$rows = New-Object System.Collections.ArrayList
function Add-Row($check, $result, $detail) {
    [void]$rows.Add([pscustomobject]@{ Check = $check; Result = $result; Detail = $detail })
}
function Get-Sha([string]$path) { (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
function Read-Utf8([string]$path) { [IO.File]::ReadAllText($path, (New-Object Text.UTF8Encoding $false)) }
function Same-Set($a, $b) { ((@($a) | Sort-Object) -join '|') -ceq ((@($b) | Sort-Object) -join '|') }

# Python 3.8+ (same rule as the hooks themselves)
$py = $null
foreach ($cand in @('py -3', 'python', 'python3')) {
    try {
        $exe, $pre = $cand -split ' '
        & $exe @pre -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $py = $cand; break }
    } catch { }   # candidate not installed: try the next one
}

# 1. basic-sync
try {
    $ps = Join-Path $PSHOME 'powershell.exe'
    $out = & $ps -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'sync-basic.ps1') -CheckOnly 2>&1 | Out-String
    $last = (($out -split "`r?`n") | Where-Object { $_ -match '^(PASS|FAIL|ERROR)' } | Select-Object -Last 1)
    if ($LASTEXITCODE -eq 0) { Add-Row 'basic-sync' 'PASS' $last } else { Add-Row 'basic-sync' 'FAIL' $last }
} catch { Add-Row 'basic-sync' 'FAIL' $_.Exception.Message }

# 2. rules-twin
try {
    $a = Get-Sha (Join-Path $pkg (Join-Path $rules 'AGENTS.md'))
    $c = Get-Sha (Join-Path $pkg (Join-Path $rules 'CLAUDE.md'))
    if ($a -eq $c) { Add-Row 'rules-twin' 'PASS' ('AGENTS.md == CLAUDE.md ' + $a.Substring(0, 12)) }
    else { Add-Row 'rules-twin' 'FAIL' ('AGENTS.md ' + $a.Substring(0, 12) + ' != CLAUDE.md ' + $c.Substring(0, 12)) }
} catch { Add-Row 'rules-twin' 'FAIL' $_.Exception.Message }

# 3. agent-files
try {
    $mdDir = Join-Path $plug 'dev-bingfa\agents'
    $tomlDir = Join-Path $pkg 'codex\agents'
    $gotMd = @(Get-ChildItem -LiteralPath $mdDir -File -Force | ForEach-Object { $_.Name } | Sort-Object)
    $gotToml = @(Get-ChildItem -LiteralPath $tomlDir -File -Force | ForEach-Object { $_.Name } | Sort-Object)
    $wantMd = @($AgentNames | ForEach-Object { "$_.md" } | Sort-Object)
    $wantToml = @($AgentNames | ForEach-Object { "bingfa-$_.toml" } | Sort-Object)
    $bad = @()
    if (-not (Same-Set $gotMd $wantMd)) { $bad += ('Claude agents: ' + ($gotMd -join ',')) }
    if (-not (Same-Set $gotToml $wantToml)) { $bad += ('Codex agents: ' + ($gotToml -join ',')) }
    if ($bad.Count -eq 0) { Add-Row 'agent-files' 'PASS' '3 Claude .md + 3 Codex .toml, nothing else' }
    else { Add-Row 'agent-files' 'FAIL' ($bad -join '; ') }
} catch { Add-Row 'agent-files' 'FAIL' $_.Exception.Message }

# 4. agent-twin (tools\check-agents.py; the lists go in as JSON on stdin; ASCII-only output)
if ($null -eq $py) {
    Add-Row 'agent-twin' 'SKIPPED' 'no Python 3.8+ found (tried py -3, python, python3)'
} else {
    try {
        $spec = ConvertTo-Json -Compress -Depth 4 @{
            allowed = @($AllowedDiffs | ForEach-Object { [pscustomobject]$_ }); names = @($AgentNames) }
        $exe, $pre = $py -split ' '
        $res = ($spec | & $exe @pre -I (Join-Path $PSScriptRoot 'check-agents.py') $pkg 2>&1 | Out-String).Trim()
        $parts = $res -split '\|', 2
        if ($parts.Count -eq 2 -and @('PASS', 'FAIL', 'SKIPPED') -contains $parts[0]) { Add-Row 'agent-twin' $parts[0] $parts[1] }
        else { Add-Row 'agent-twin' 'FAIL' ('helper output: ' + $res) }
    } catch { Add-Row 'agent-twin' 'FAIL' $_.Exception.Message }
}

# 5. check-silence
try {
    $h = Get-Sha (Join-Path $plug 'dev-bingfa-check\hooks\check_silence.py')
    if ($h -eq $CheckSilenceSha) { Add-Row 'check-silence' 'PASS' ('sha256 ' + $h.Substring(0, 12) + ' == recorded') }
    else { Add-Row 'check-silence' 'FAIL' ('sha256 ' + $h.Substring(0, 12) + ' != recorded ' + $CheckSilenceSha.Substring(0, 12)) }
} catch { Add-Row 'check-silence' 'FAIL' $_.Exception.Message }

# 6. version
try {
    $v = (Get-Content -LiteralPath (Join-Path $pkg 'VERSION') -Raw).Trim()
    $want = if (($v -split '\.').Count -eq 2) { "$v.0" } else { $v }
    $bad = @()
    foreach ($name in @('dev-bingfa', 'dev-bingfa-check')) {
        $pj = Join-Path $plug "$name\.claude-plugin\plugin.json"
        $got = (Read-Utf8 $pj | ConvertFrom-Json).version
        if ($got -ne $want) { $bad += "$name=$got" }
    }
    if ($bad.Count -eq 0) { Add-Row 'version' 'PASS' "VERSION $v -> both plugin.json $want" }
    else { Add-Row 'version' 'FAIL' ("VERSION $v wants $want; " + ($bad -join ', ')) }
} catch { Add-Row 'version' 'FAIL' $_.Exception.Message }

$skip = Join-Path $pkg $offline
$allFiles = @(Get-ChildItem -LiteralPath $pkg -Recurse -File -Force |
    Where-Object { -not $_.FullName.StartsWith($skip + '\') })

# 7. line-endings
try {
    $files = @($allFiles | Where-Object { @('.sh', '.cmd') -contains $_.Extension })
    $bad = @()
    foreach ($f in $files) {
        $b = [IO.File]::ReadAllBytes($f.FullName)
        $lf = 0; $crlf = 0
        for ($i = 0; $i -lt $b.Length; $i++) {
            if ($b[$i] -eq 10) { if ($i -gt 0 -and $b[$i - 1] -eq 13) { $crlf++ } else { $lf++ } }
        }
        $ok = if ($f.Extension -eq '.sh') { $crlf -eq 0 } else { $lf -eq 0 -and $crlf -gt 0 }
        if (-not $ok) { $bad += "$($f.Name) (LF=$lf CRLF=$crlf)" }
    }
    if ($files.Count -eq 0) { Add-Row 'line-endings' 'FAIL' 'no .sh / .cmd files found' }
    elseif ($bad.Count -eq 0) { Add-Row 'line-endings' 'PASS' "$($files.Count) file(s): .sh LF, .cmd CRLF" }
    else { Add-Row 'line-endings' 'FAIL' ($bad -join ', ') }
} catch { Add-Row 'line-endings' 'FAIL' $_.Exception.Message }

# 8. json
try {
    $files = @($allFiles | Where-Object { $_.Extension -eq '.json' })
    $bad = @()
    foreach ($f in $files) {
        try { Read-Utf8 $f.FullName | ConvertFrom-Json | Out-Null } catch { $bad += $f.Name }
    }
    if ($files.Count -eq 0) { Add-Row 'json' 'FAIL' 'no .json files found' }
    elseif ($bad.Count -eq 0) { Add-Row 'json' 'PASS' "$($files.Count) file(s) parse" }
    else { Add-Row 'json' 'FAIL' ('does not parse: ' + ($bad -join ', ')) }
} catch { Add-Row 'json' 'FAIL' $_.Exception.Message }

# 9. hooks-json
try {
    $hj = (Read-Utf8 (Join-Path $plug 'dev-bingfa-check\hooks\hooks.json') | ConvertFrom-Json).hooks
    $want = @{
        SessionStart = @{ matcher = $null; arg = 'session'; win = '"${CLAUDE_PLUGIN_ROOT}\hooks\run.cmd" session' }
        PostToolUse  = @{ matcher = 'Write|Edit'; arg = 'post'; win = '"${CLAUDE_PLUGIN_ROOT}\hooks\codex-post.cmd"' }
    }
    $bad = @()
    $events = @($hj.PSObject.Properties | ForEach-Object { $_.Name } | Sort-Object)
    if (-not (Same-Set $events @('PostToolUse', 'SessionStart'))) { $bad += ('events: ' + ($events -join ',')) }
    foreach ($ev in $want.Keys) {
        $groups = @($hj.$ev)
        if ($groups.Count -ne 1) { $bad += "$ev has $($groups.Count) groups"; continue }
        if ($groups[0].matcher -ne $want[$ev].matcher) { $bad += "$ev matcher '$($groups[0].matcher)'" }
        $hs = @($groups[0].hooks)
        if ($hs.Count -ne 1) { $bad += "$ev has $($hs.Count) hooks"; continue }
        $h = $hs[0]; $arg = $want[$ev].arg
        if ($h.type -ne 'command') { $bad += "$ev type '$($h.type)'" }
        if ($h.timeout -ne 10) { $bad += "$ev timeout $($h.timeout)" }
        if (-not $h.command.Contains('/hooks/run.sh" ' + $arg + "`n")) { $bad += "$ev command does not call run.sh $arg" }
        if (-not $h.command.Contains('/hooks/run.cmd" ' + $arg + "`n")) { $bad += "$ev command does not call run.cmd $arg" }
        if ($h.commandWindows -cne $want[$ev].win) { $bad += "$ev commandWindows '$($h.commandWindows)'" }
    }
    if ($bad.Count -eq 0) { Add-Row 'hooks-json' 'PASS' 'SessionStart + PostToolUse(Write|Edit), timeout 10, commands as expected' }
    else { Add-Row 'hooks-json' 'FAIL' ($bad -join '; ') }
} catch { Add-Row 'hooks-json' 'FAIL' $_.Exception.Message }

# 10. marketplace
try {
    $mp = Read-Utf8 (Join-Path $plug '.claude-plugin\marketplace.json') | ConvertFrom-Json
    $bad = @()
    $names = @($mp.plugins | ForEach-Object { $_.name } | Sort-Object)
    if (-not (Same-Set $names @('dev-bingfa', 'dev-bingfa-check'))) { $bad += ('plugins: ' + ($names -join ',')) }
    foreach ($p in @($mp.plugins)) {
        $pj = Join-Path (Join-Path $plug ($p.source -replace '/', '\')) '.claude-plugin\plugin.json'
        if (-not (Test-Path -LiteralPath $pj)) { $bad += "$($p.name): source '$($p.source)' has no plugin.json"; continue }
        $pn = (Read-Utf8 $pj | ConvertFrom-Json).name
        if ($pn -ne $p.name) { $bad += "$($p.name): source plugin.json name is '$pn'" }
    }
    if ($bad.Count -eq 0) { Add-Row 'marketplace' 'PASS' ('sources resolve: ' + ($names -join ', ')) }
    else { Add-Row 'marketplace' 'FAIL' ($bad -join '; ') }
} catch { Add-Row 'marketplace' 'FAIL' $_.Exception.Message }

# 11. commit-manual
try {
    $cdir = Join-Path $plug 'dev-bingfa\skills\commit'
    $bad = @()
    $skill = Read-Utf8 (Join-Path $cdir 'SKILL.md')
    $fm = ($skill -split '(?m)^---\s*$', 3)[1]
    if ($fm -notmatch '(?m)^disable-model-invocation:\s*true\s*$') { $bad += 'SKILL.md lacks disable-model-invocation: true' }
    $oy = Join-Path $cdir 'agents\openai.yaml'
    if (-not (Test-Path -LiteralPath $oy)) { $bad += 'agents\openai.yaml missing' }
    elseif ((Read-Utf8 $oy) -notmatch '(?m)^\s+allow_implicit_invocation:\s*false\s*$') { $bad += 'openai.yaml lacks allow_implicit_invocation: false' }
    if ($bad.Count -eq 0) { Add-Row 'commit-manual' 'PASS' 'disable-model-invocation: true + openai.yaml allow_implicit_invocation: false' }
    else { Add-Row 'commit-manual' 'FAIL' ($bad -join '; ') }
} catch { Add-Row 'commit-manual' 'FAIL' $_.Exception.Message }

# 12. search-modules
try {
    $mdir = Join-Path $plug 'dev-bingfa\web-search-modules'
    $got = @(Get-ChildItem -LiteralPath $mdir -File -Force | ForEach-Object { $_.Name } | Sort-Object)
    $bad = @()
    if (-not (Same-Set $got ($SearchModules | Sort-Object))) { $bad += ('files: ' + ($got -join ',')) }
    foreach ($n in $got) {
        $t = Read-Utf8 (Join-Path $mdir $n)
        if ($t.Trim().Length -eq 0 -or -not $t.StartsWith('# ')) { $bad += "$n empty or no '# ' heading" }
    }
    if ($bad.Count -eq 0) { Add-Row 'search-modules' 'PASS' "$($got.Count) module(s), each with a heading" }
    else { Add-Row 'search-modules' 'FAIL' ($bad -join '; ') }
} catch { Add-Row 'search-modules' 'FAIL' $_.Exception.Message }

# 13. hook-matrix
if ($null -eq $py) {
    Add-Row 'hook-matrix' 'SKIPPED' 'no Python 3.8+ found (tried py -3, python, python3)'
} else {
    try {
        $exe, $pre = $py -split ' '
        $out = & $exe @pre -I (Join-Path $PSScriptRoot 'test-hooks.py') 2>&1 | Out-String
        $code = $LASTEXITCODE
        $sum = (($out -split "`r?`n") | Where-Object { $_ -match '^SUMMARY\|' } | Select-Object -Last 1)
        $parts = "$sum" -split '\|', 3
        if ($parts.Count -eq 3 -and $parts[1] -eq 'PASS' -and $code -eq 0) { Add-Row 'hook-matrix' 'PASS' $parts[2] }
        elseif ($parts.Count -eq 3 -and $parts[1] -eq 'SKIPPED' -and $code -eq 2) { Add-Row 'hook-matrix' 'SKIPPED' $parts[2] }
        elseif ($parts.Count -eq 3) { Add-Row 'hook-matrix' 'FAIL' ($parts[2] + ' (run python tools\test-hooks.py for the table)') }
        else { Add-Row 'hook-matrix' 'FAIL' ("exit $code, no SUMMARY line") }
    } catch { Add-Row 'hook-matrix' 'FAIL' $_.Exception.Message }
}

$rows | Format-Table -AutoSize -Wrap | Out-String -Width 200 | Write-Host
$fail = @($rows | Where-Object { $_.Result -eq 'FAIL' }).Count
$skipped = @($rows | Where-Object { $_.Result -eq 'SKIPPED' }).Count
if ($fail -gt 0) { Write-Host "FAIL: $fail of $($rows.Count) check(s) failed."; exit 1 }
if ($skipped -gt 0) { Write-Host "INCOMPLETE: $skipped check(s) skipped, the rest passed."; exit 2 }
Write-Host "PASS: all $($rows.Count) check(s) passed."
exit 0
