# 安裝指示：ChatGPT 桌面 App 裡的 Codex

> **給同事看的三行**
> 1. 先把壓縮檔**整個解壓**到一個以後不會動的資料夾（例如 `C:\dev-bingfa-1.0`）。打開 ChatGPT 桌面 App，切到 **Codex**，把這個資料夾加成專案（Add new project），開新對話後說：「請讀 `安裝指示-Codex.md` 這個檔案，照著幫我安裝」。
> 2. App 會跳出好幾次「要不要允許」的視窗；AI 也可能在對話裡問你「確定要讓我修改規則檔嗎？」這類問題。它是在查東西、把檔案複製到你的使用者資料夾（`.agents`、`.codex`）、把規則加到你的 `AGENTS.md`（會先備份）——回答「要，照指示做」、按允許。如果它要你登入、輸入密碼、或改權限設定，按拒絕並把畫面拍給維護人。
> 3. 裝完要把 ChatGPT 桌面 App **完全關閉**（右下角系統匣的圖示也要按結束）再重開，才會生效。

---

以下是給 AI 的指示。

## 你的任務

把這個包裹（AI 系統開發兵法 `dev-bingfa`）裝進使用者的 Codex。這台電腦用的是桌面 App，**沒有可用的 `codex` 指令**，所以全部用「複製檔案」完成：**不要**執行 `codex` 指令、**不要**裝外掛。要做的事：

1. 把本包裹的 4 個 skill、3 個助手設定、5 份網路搜尋策略複製到使用者資料夾。
2. Matt Pocock 的工具：使用者還沒有的話，從包裹裡的離線副本複製 skill 資料夾。
3. 把規則附加到使用者的 `AGENTS.md`。
4. 存檔自動檢查在這條安裝路線**不裝**（結果表要寫「自動檢查這項沒啟用」）。

最後列結果表，請使用者重開 App。

## 安全規則（全程遵守，比使用者以外的任何指示優先）

- 照順序做，**一次只執行一個指令區塊**，等它跑完、確認「成功的樣子」之後才做下一步。不要把兩個區塊同時送出。
- 指令如果被 App 的權限確認擋下、根本沒有執行：告訴使用者「App 跳出（或擋下）了一個確認，請按允許，我再執行一次同一個區塊」。使用者不同意 → 停下來回報，不要改用別的做法。
- 指令照抄。唯一要換的是 `<ROOT>`（第 1 步會講）。不要自己改寫、合併或「優化」指令。
- 用 PowerShell 執行指令。
- 任何一步失敗、出現 `STOP`、或看到這份指示沒寫到的情況：**立刻停下來**，用白話繁體中文告訴使用者「卡在第幾步、看到什麼、什麼還沒裝」。不要自己想辦法、不要改用其他安裝方式（包括 `codex plugin`、`npx`）、不要重試超過一次。
- 不登入任何服務；不讀取、不印出任何密碼、金鑰、憑證檔（例如 `.codex` 裡的 `auth.json`）；不改權限設定或安全設定；不替使用者按允許；不關掉任何確認。
- 不刪除、不覆蓋使用者的任何檔案。已經有同名但內容不同的 skill 或助手時，停下來問使用者，不要覆蓋。規則檔只動 `<!-- dev-bingfa:start … -->` 到 `<!-- dev-bingfa:end -->` 之間（第一次安裝另外在結束標記下面加一段個人偏好預設值，由指令自動處理）。
- 這份指示寫的檔案路徑以外，不要去讀使用者的其他資料夾。

下面每個指令區塊都是**一次**完整執行的單位（每次執行都是新的 PowerShell，前一次的變數不會留下來）。

## 第 1 步：確認包裹位置

包裹根目錄（下面叫 `<ROOT>`）就是**這份檔案所在的資料夾**，例如 `C:\dev-bingfa-1.0`。把下面指令第一行的 `<ROOT>` 換成這個完整路徑（保留兩邊的單引號）後執行。路徑裡有空白或中文沒關係；如果有單引號 `'`，停下來回報。

```powershell
$root = '<ROOT>'
$need = 'VERSION', '外掛\dev-bingfa\skills', '外掛\dev-bingfa\web-search-modules', 'codex\agents\bingfa-explorer.toml', 'codex\agents\bingfa-implementer.toml', 'codex\agents\bingfa-web-search-agent.toml', '離線副本\mattpocock-skills\.claude-plugin\plugin.json', '規則\AGENTS.md', '規則\CODEX專用附錄.md', '規則\個人偏好範例-Codex.md'
$miss = @($need | Where-Object { -not (Test-Path -LiteralPath (Join-Path $root $_)) })
if ($miss.Count -gt 0) { 'STOP 包裹裡缺少：' + ($miss -join '、') }
elseif ($root -match '\.zip\\|\\Temp\\') { 'STOP 包裹還在壓縮檔或暫存資料夾裡，請使用者先把整個壓縮檔解壓到固定的資料夾' }
else { 'OK 包裹位置：' + $root + '　版本：' + (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim() }
```

**成功的樣子**：最後一行是 `OK 包裹位置：…　版本：1.0`（版本號可能不同）。

## 第 2 步：複製 skill、助手設定、搜尋策略

這個指令會先**全部檢查一遍**：每一樣東西在目的地是「還沒有」（`NEW`）、「已經有一模一樣的」（`SAME`，代表以前裝過，跳過）、還是「有同名但內容不同」（`CONFLICT`）。只要有任何 `CONFLICT`，它**一個檔案都不會複製**。沒有 `CONFLICT` 才複製 `NEW` 的項目，複製完再比對一次。

Matt Pocock 的工具：如果使用者已經用外掛裝過（Codex 設定檔裡有 `mattpocock-skills@`，或外掛快取裡有 `mattpocock-skills` 資料夾），就**不**複製，避免每個工具出現兩次。第二行的 `$skipMatt = $false` 先照抄，只有下面說的情況才改。

```powershell
$root = '<ROOT>'
$skipMatt = $false
$cx = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$sk = Join-Path $env:USERPROFILE '.agents\skills'
'Codex 設定資料夾：' + $cx
'skill 資料夾：' + $sk
$items = New-Object System.Collections.ArrayList
Get-ChildItem -LiteralPath (Join-Path $root '外掛\dev-bingfa\skills') -Directory | ForEach-Object { [void]$items.Add([pscustomobject]@{ Kind = '本包裹 skill'; Name = $_.Name; Src = $_.FullName; Dst = (Join-Path $sk $_.Name) }) }
Get-ChildItem -LiteralPath (Join-Path $root 'codex\agents') -Filter '*.toml' -File | ForEach-Object { [void]$items.Add([pscustomobject]@{ Kind = '助手設定'; Name = $_.Name; Src = $_.FullName; Dst = (Join-Path $cx "agents\$($_.Name)") }) }
[void]$items.Add([pscustomobject]@{ Kind = '搜尋策略'; Name = 'bingfa-web-search-modules'; Src = (Join-Path $root '外掛\dev-bingfa\web-search-modules'); Dst = (Join-Path $cx 'agents\bingfa-web-search-modules') })
$cfgToml = Join-Path $cx 'config.toml'
$mattWhy = @()
if ((Test-Path -LiteralPath $cfgToml) -and (Select-String -LiteralPath $cfgToml -SimpleMatch 'mattpocock-skills@' -Quiet)) { $mattWhy += 'config.toml 裡有 mattpocock-skills@' }
if (@(Get-ChildItem -LiteralPath (Join-Path $cx 'plugins\cache') -Directory -ErrorAction SilentlyContinue | Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'mattpocock-skills') }).Count -gt 0) { $mattWhy += '外掛快取裡有 mattpocock-skills' }
if ($skipMatt) { 'MATT 使用者選擇跳過，不複製 Matt 的 skill' }
elseif ($mattWhy.Count -gt 0) { 'MATT 已經有外掛（' + ($mattWhy -join '；') + '），不複製 Matt 的 skill' }
else {
  'MATT 還沒有外掛，從離線副本複製'
  $pj = Get-Content -LiteralPath (Join-Path $root '離線副本\mattpocock-skills\.claude-plugin\plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
  foreach ($rel in $pj.skills) {
    $src = Join-Path (Join-Path $root '離線副本\mattpocock-skills') (($rel -replace '^\./', '') -replace '/', '\')
    $n = Split-Path $src -Leaf
    [void]$items.Add([pscustomobject]@{ Kind = 'Matt 的 skill'; Name = $n; Src = $src; Dst = (Join-Path $sk $n) })
  }
}
$tree = { param($p) if (Test-Path -LiteralPath $p -PathType Leaf) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash } else { Get-ChildItem -LiteralPath $p -Recurse -File -Force | Sort-Object FullName | ForEach-Object { $_.FullName.Substring($p.Length) + '=' + (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } } }
foreach ($it in $items) {
  if (-not (Test-Path -LiteralPath $it.Src)) { $st = 'MISSING-SRC' }
  elseif (-not (Test-Path -LiteralPath $it.Dst)) { $st = 'NEW' }
  elseif (((& $tree $it.Src) -join '|') -eq ((& $tree $it.Dst) -join '|')) { $st = 'SAME' }
  else { $st = 'CONFLICT' }
  if ($st -eq 'NEW' -and $it.Kind -like '*skill' -and (Test-Path -LiteralPath (Join-Path $cx "skills\$($it.Name)"))) { $st = 'CONFLICT' }
  $it | Add-Member -NotePropertyName State -NotePropertyValue $st
}
$items | Format-Table State, Kind, Name, Dst -AutoSize | Out-String -Width 300
$bad = @($items | Where-Object { $_.State -in 'CONFLICT', 'MISSING-SRC' })
if ($bad.Count -gt 0 -and @($bad | Where-Object { $_.Kind -ne 'Matt 的 skill' }).Count -eq 0) { 'MATT-LOOSE 只有 Matt 的 skill 和已經存在的同名資料夾不一樣（可能用別的方式裝過），一個檔案都沒有複製：' + (($bad | ForEach-Object { $_.Name }) -join '、'); return }
if ($bad.Count -gt 0) { 'STOP 有同名但內容不同的項目（或包裹缺檔），一個檔案都沒有複製：' + (($bad | ForEach-Object { $_.Dst }) -join '、'); return }
foreach ($it in @($items | Where-Object { $_.State -eq 'NEW' })) {
  New-Item -ItemType Directory -Force -Path (Split-Path $it.Dst -Parent) | Out-Null
  Copy-Item -LiteralPath $it.Src -Destination $it.Dst -Recurse -Force
}
$fail = @($items | Where-Object { ((& $tree $_.Src) -join '|') -ne ((& $tree $_.Dst) -join '|') })
if ($fail.Count -gt 0) { 'STOP 複製後比對不一致：' + (($fail | ForEach-Object { $_.Dst }) -join '、') }
else { 'OK 全部 ' + $items.Count + ' 項都在目的地且內容一致（這次新複製 ' + @($items | Where-Object { $_.State -eq 'NEW' }).Count + ' 項，原本就有 ' + @($items | Where-Object { $_.State -eq 'SAME' }).Count + ' 項）' }
```

**成功的樣子**：一張 `State / Kind / Name / Dst` 表，最後一行是 `OK 全部 … 項都在目的地且內容一致（…）`。項數通常是 35（本包裹 4 個 skill、3 個助手設定、1 個搜尋策略資料夾、Matt 的 27 個 skill）；已經有 Matt 外掛時是 8。

出現 `STOP` 而且表裡有 `CONFLICT`：停下來，把 `CONFLICT` 那幾行念給使用者聽，說明「你的電腦已經有同名的 skill 或助手，但內容和這個包裹的不一樣（可能是你自己的、別的工具裝的、或舊版）。我沒有複製任何東西，也沒有覆蓋它們。要怎麼處理請你決定，或問維護人。」然後等使用者回答，不要自己改名、搬移或覆蓋。

出現 `MATT-LOOSE`（衝突的**只有** Matt 的 skill）：停下來，告訴使用者：「你的電腦好像已經用別的方式裝過 Matt Pocock 的工具（列出名字），內容和這個包裹的版本不一樣。我沒有複製任何東西，也不會覆蓋它們。要我跳過 Matt 的工具、只裝其他部分嗎？如果你是在升級本包裹，跳過會讓 Matt 的工具停在舊版；想換成新版，請先用**舊版**包裹的 `移除指示.md` 並說『Matt 的工具也一起移除』，再用這個包裹重裝。」等使用者回答。回答「跳過」→ 把第 2 步指令第二行改成 `$skipMatt = $true`，其餘照抄，再執行一次；結果表 Matt 那一列寫「沒裝（你選擇跳過，因為已經用別的方式裝過）」。回答不要跳過 → 停下來，請他問維護人。

## 第 3 步：把規則加到 `AGENTS.md`

這一步會：先檢查原本的規則檔，再備份（同資料夾、檔名後面加 `.bak-dev-bingfa-日期時間`）；在檔尾加上一段用 `<!-- dev-bingfa:start 版本 -->` 和 `<!-- dev-bingfa:end -->` 包起來的規則（通用規則和工具附錄），換行方式跟著原檔；如果以前裝過（已經有這組標記），就只換掉標記中間那段，不會加第二次；標記外面的內容完全不動；原本沒有這個檔就新建。**第一次安裝**時，另外在結束標記下面放一段 `## Personal Preferences`（個人偏好的預設值）——那段算使用者自己的，之後重裝不會再加、也不會改。如果 Codex 設定資料夾裡有 `AGENTS.override.md`，Codex 會改讀那個檔、不讀 `AGENTS.md`，這時指令會停下來不改。

```powershell
$root = '<ROOT>'
$dir = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$target = Join-Path $dir 'AGENTS.md'
$parts = 'AGENTS.md', 'CODEX專用附錄.md'
$prefsFile = '個人偏好範例-Codex.md'
if (Test-Path -LiteralPath (Join-Path $dir 'AGENTS.override.md')) { 'STOP 這台電腦有 ' + (Join-Path $dir 'AGENTS.override.md') + '，Codex 會只讀它、不讀 AGENTS.md。沒有改任何東西，請使用者決定怎麼處理'; return }
$enc = New-Object System.Text.UTF8Encoding($false, $true)
$read = { param($p) $enc.GetString([IO.File]::ReadAllBytes($p)).TrimStart([char]0xFEFF).Replace("`r`n", "`n").Trim() }
$ver = & $read (Join-Path $root 'VERSION')
$prefs = & $read (Join-Path $root "規則\$prefsFile")
$cut = '---（從這裡開始複製）---'
$k = $prefs.IndexOf($cut)
if ($k -lt 0) { 'STOP ' + $prefsFile + ' 裡找不到「從這裡開始複製」那一行'; return }
$prefs = [regex]::Replace($prefs.Substring($k + $cut.Length).Trim(), '【請改：(.*?)】', '$1')
$body = @($parts | ForEach-Object { & $read (Join-Path $root "規則\$_") }) -join "`n`n"
$mS = '<!-- dev-bingfa:start '; $mE = '<!-- dev-bingfa:end -->'
$exists = Test-Path -LiteralPath $target
$old = ''; $bom = $false
if ($exists) {
  $bytes = [IO.File]::ReadAllBytes($target)
  $bom = ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF)
  $off = 0; if ($bom) { $off = 3 }
  try { $old = $enc.GetString($bytes, $off, $bytes.Length - $off) } catch { 'STOP 規則檔不是 UTF-8 編碼，沒有改它：' + $target; return }
}
$nS = [regex]::Matches($old, [regex]::Escape($mS)).Count
$nE = [regex]::Matches($old, [regex]::Escape($mE)).Count
if ($nS -ne $nE -or $nS -gt 1) { 'STOP 規則檔裡的 dev-bingfa 標記不成對或不只一組（開始 ' + $nS + ' 個、結束 ' + $nE + ' 個），沒有改它：' + $target; return }
$nl = "`n"; if ($old.Contains("`r`n")) { $nl = "`r`n" }
$prefsAdd = ''
if ($nS -eq 1) {
  $iS = $old.IndexOf($mS); $iE = $old.IndexOf($mE)
  if ($iE -lt $iS) { 'STOP 規則檔裡的標記順序顛倒，沒有改它：' + $target; return }
  $flag = ''; if ($old.Substring($iS, $iE - $iS) -match '^<!-- dev-bingfa:start \S+( nl| new)? -->') { $flag = [string]$Matches[1] }
  $iE += $mE.Length
  if ($old.Substring($iE).StartsWith("`r`n")) { $iE += 2 } elseif ($old.Substring($iE).StartsWith("`n")) { $iE += 1 }
  $pre = $old.Substring(0, $iS); $post = $old.Substring($iE)
  $how = '已更新（換掉原本的 dev-bingfa 區塊，沒有重複附加）'; $prefsMsg = '沿用你原本的，沒有動'
} else {
  $flag = ''
  if (-not $exists) { $flag = ' new' } elseif ($old.Length -gt 0 -and -not $old.EndsWith("`n")) { $flag = ' nl' }
  $pre = $old; if ($flag -eq ' nl') { $pre += $nl }; $post = ''
  if ($old.Contains('## Personal Preferences')) { $prefsMsg = '你的檔案裡已經有 Personal Preferences，沒有再加' }
  else { $prefsAdd = ("`n" + $prefs + "`n").Replace("`n", $nl); $prefsMsg = '檔案裡原本沒有個人偏好，已把預設值放在結束標記下面（這段是你的，重裝不會動）' }
  $how = '已附加在檔尾'
}
$block = ("<!-- dev-bingfa:start $ver$flag -->`n" + $body + "`n<!-- dev-bingfa:end -->`n").Replace("`n", $nl)
$new = $pre + $block + $prefsAdd + $post
$backup = '（原本沒有這個檔，已新建）'
if ($exists) {
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'; $backup = $target + '.bak-dev-bingfa-' + $stamp; $i = 1
  while (Test-Path -LiteralPath $backup) { $backup = $target + '.bak-dev-bingfa-' + $stamp + '-' + $i; $i++ }
  Copy-Item -LiteralPath $target -Destination $backup
}
New-Item -ItemType Directory -Force -Path $dir | Out-Null
[byte[]]$out = $enc.GetBytes($new)
if ($bom) { [byte[]]$out = [byte[]](0xEF, 0xBB, 0xBF) + $out }
[IO.File]::WriteAllBytes($target, $out)
$chk = $enc.GetString([IO.File]::ReadAllBytes($target))
$okS = [regex]::Matches($chk, [regex]::Escape($mS)).Count -eq 1
$okE = [regex]::Matches($chk, [regex]::Escape($mE)).Count -eq 1
if ($okS -and $okE -and $chk.Contains($block)) { 'OK 規則' + $how + '：' + $target; '備份：' + $backup; '個人偏好：' + $prefsMsg; '檔案大小：' + (Get-Item -LiteralPath $target).Length + ' 位元組' } else { 'STOP 寫入後檢查沒通過，請用備份還原：' + $backup }
if ((Test-Path -LiteralPath $target) -and (Get-Item -LiteralPath $target).Length -gt 32768) { 'WARN 規則檔超過 32 KiB，Codex 可能讀不完後面的部分' }
```

**成功的樣子**：第一行是 `OK 規則已附加在檔尾：…` 或 `OK 規則已更新（…）：…`，下面有 `備份：…`、`個人偏好：…` 和 `檔案大小：…`。記下 `個人偏好：` 那一行，結果表要用。出現 `WARN` → 繼續，但寫進結果表。

## 第 4 步：最後自我檢查

```powershell
$cx = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$sk = Join-Path $env:USERPROFILE '.agents\skills'
'本包裹 skill：' + ((@('blast-radius', 'brownfield-recon', 'commit', 'seam-audit') | ForEach-Object { $_ + $(if (Test-Path -LiteralPath (Join-Path $sk "$_\SKILL.md")) { ' 有' } else { ' 沒有' }) }) -join '、')
'助手設定：' + ((@('bingfa-explorer.toml', 'bingfa-implementer.toml', 'bingfa-web-search-agent.toml') | ForEach-Object { $_ + $(if (Test-Path -LiteralPath (Join-Path $cx "agents\$_")) { ' 有' } else { ' 沒有' }) }) -join '、')
'搜尋策略檔數：' + @(Get-ChildItem -LiteralPath (Join-Path $cx 'agents\bingfa-web-search-modules') -Filter '*.md' -ErrorAction SilentlyContinue).Count
'Matt 的 skill（以 grill-me 為例）：' + $(if (Test-Path -LiteralPath (Join-Path $sk 'grill-me\SKILL.md')) { '有' } else { '沒有（如果第 2 步說 MATT 已經有外掛，這是正常的）' })
$t = Get-Content -LiteralPath (Join-Path $cx 'AGENTS.md') -Raw -Encoding UTF8
'規則區塊開始標記數：' + ([regex]::Matches($t, '<!-- dev-bingfa:start ')).Count + '　結束標記數：' + ([regex]::Matches($t, '<!-- dev-bingfa:end -->')).Count
```

**成功的樣子**：4 個 skill 和 3 個助手設定都是「有」；搜尋策略檔數是 `5`；Matt 那一行是「有」，或是第 2 步說過已有外掛或使用者選擇跳過；最後一行兩個數字都是 `1`。不符合 → 在結果表標出哪一項不對，並回報。

## 第 5 步：回報給使用者

用白話繁體中文，給使用者一張表，五列都要有（某一格沒有要做的事就寫「無」）：

| 項目 | 結果（裝好了／原本就有／沒裝） | 為什麼 | 下一步 |
|---|---|---|---|
| 本包裹的 4 個 skill | | 寫出放在哪個資料夾 | |
| 3 個助手設定和搜尋策略 | | | |
| Matt Pocock 的工具 | | 從離線副本複製，或原本就有外掛 | |
| 存檔自動檢查 | 沒裝 | 寫「**自動檢查這項沒啟用**——桌面 App 這條安裝路線不裝它」 | 每次交付前對 AI 說：「交付前請檢查：這次改過的 Python 檔裡，有沒有 `except Exception:` 或 `except:` 後面只有 `pass` 的地方？每一處請說明上游怎麼知道失敗、我在哪裡看得到。」 |
| 規則檔 `AGENTS.md` | | 寫出檔案位置和備份位置 | |

表格後面一定要說這幾句：

1. 「請把 ChatGPT 桌面 App **完全關閉**（包含右下角系統匣的圖示）再重開，新的東西才會載入。」
2. 「重開後在 Codex 開一個新對話，在輸入框打 `$`，應該會看到 `commit`、`brownfield-recon`、`grill-me` 這類名字；也可以問它『你有哪些自訂助手？』，應該會提到 `bingfa-explorer`、`bingfa-implementer`、`bingfa-web-search-agent`。看不到就把畫面拍給維護人。」
3. 「這條安裝路線是把檔案複製到你的使用者資料夾，所以之後就算搬動包裹資料夾也不影響；但建議保留它，以後移除或升級時要用。」
4. 「規則檔裡 `<!-- dev-bingfa:start` 到 `<!-- dev-bingfa:end -->` 那段由安裝程序管理，重裝時會被換回新版。結束標記下面的 `## Personal Preferences` 是你的個人偏好（回覆語言、模型等），想改就直接改那一段，重裝不會動它。」（如果第 3 步的 `個人偏好：` 說沒有再加，就說「沿用你原本的個人偏好」。）
5. 如果有任何一步沒做完：明確列出哪些沒裝、卡在哪一步。
