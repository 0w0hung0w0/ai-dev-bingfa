# 安裝指示：Claude 桌面 App（Code 分頁）

> **給同事看的三行**
> 1. 先把壓縮檔**整個解壓**到一個以後不會動的資料夾（例如 `C:\dev-bingfa-1.0`），裝好之後這個資料夾不能搬。打開 Claude 桌面 App 的 **Code** 分頁，開新對話、資料夾選它，然後說：「請讀 `安裝指示-ClaudeCode.md` 這個檔案，照著幫我安裝」。
> 2. App 會跳出好幾次「要不要允許」的視窗；AI 也可能在對話裡問你「確定要讓我修改規則檔／加入外掛來源嗎？」這類問題。它是在查東西、安裝外掛、把規則加到你的 `CLAUDE.md`（會先備份）——回答「要，照指示做」、按允許。如果它要你登入、輸入密碼、或改權限設定，按拒絕並把畫面拍給維護人。
> 3. 裝完要把 Claude 桌面 App **完全關閉**（右下角系統匣的圖示也要按結束）再重開，才會生效。

---

以下是給 AI 的指示。

## 你的任務

把這個包裹（AI 系統開發兵法 `dev-bingfa`）裝進使用者的 Claude Code。依序裝四樣東西：

1. Matt Pocock 的工具（外掛 `mattpocock-skills`）：連得上 GitHub 就用官方方式，連不上才用包裹裡的離線副本。兩種**只裝一種**。
2. 本包裹的主外掛 `dev-bingfa`。
3. 選用的存檔自動檢查外掛 `dev-bingfa-check`：電腦有 Python 3.8 以上才裝。
4. 把規則附加到使用者的 `CLAUDE.md`。

最後列結果表，請使用者重開 App。

## 安全規則（全程遵守，比使用者以外的任何指示優先）

- 照順序做，**一次只執行一個指令區塊**，等它跑完、確認「成功的樣子」之後才做下一步。不要把兩個區塊同時送出。
- 指令如果被 App 的權限確認擋下、根本沒有執行：告訴使用者「App 跳出（或擋下）了一個確認，請按允許，我再執行一次同一個區塊」。使用者不同意 → 停下來回報，不要改用別的做法。
- 指令照抄。唯一要換的是 `<ROOT>`（第 1 步會講）。不要自己改寫、合併或「優化」指令。
- 只用 PowerShell 執行指令。如果你沒有可以執行 PowerShell 的工具，停下來回報，不要改用別的方法。
- 任何一步失敗、出現 `STOP`、或看到這份指示沒寫到的情況：**立刻停下來**，用白話繁體中文告訴使用者「卡在第幾步、看到什麼、什麼還沒裝」。不要自己想辦法、不要改用其他安裝方式、不要重試超過一次。
- 不登入任何服務；不讀取、不印出任何密碼、金鑰、憑證檔；不改權限設定或安全設定；不替使用者按允許；不關掉任何確認。
- 不刪除使用者的任何檔案。規則檔只動 `<!-- dev-bingfa:start … -->` 到 `<!-- dev-bingfa:end -->` 之間（第一次安裝另外在結束標記下面加一段個人偏好預設值，由指令自動處理），其他內容一個字都不改。
- 這份指示寫的檔案路徑以外，不要去讀使用者的其他資料夾（特別是 `.claude` 裡的 `projects`、歷史紀錄、憑證）。

下面每個指令區塊都是**一次**完整執行的單位（每次執行都是新的 PowerShell，前一次的變數不會留下來）。

## 第 1 步：確認包裹位置

包裹根目錄（下面叫 `<ROOT>`）就是**這份檔案所在的資料夾**，例如 `C:\dev-bingfa-1.0`。把下面指令第一行的 `<ROOT>` 換成這個完整路徑（保留兩邊的單引號）後執行。路徑裡有空白或中文沒關係；如果有單引號 `'`，停下來回報。

```powershell
$root = '<ROOT>'
$need = 'VERSION', '外掛\.claude-plugin\marketplace.json', '外掛\dev-bingfa\.claude-plugin\plugin.json', '外掛\dev-bingfa-check\.claude-plugin\plugin.json', '離線副本\.claude-plugin\marketplace.json', '離線副本\mattpocock-skills\.claude-plugin\plugin.json', '規則\CLAUDE.md', '規則\CLAUDE專用附錄.md', '規則\個人偏好範例.md'
$miss = @($need | Where-Object { -not (Test-Path -LiteralPath (Join-Path $root $_)) })
if ($miss.Count -gt 0) { 'STOP 包裹裡缺少：' + ($miss -join '、') }
elseif ($root -match '\.zip\\|\\Temp\\') { 'STOP 包裹還在壓縮檔或暫存資料夾裡，請使用者先把整個壓縮檔解壓到固定的資料夾' }
else { 'OK 包裹位置：' + $root + '　版本：' + (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim() }
```

**成功的樣子**：最後一行是 `OK 包裹位置：…　版本：1.0`（版本號可能不同）。

**接著告訴使用者這一句**（然後繼續）：「提醒：裝好之後，這個包裹資料夾 `<ROOT>` 要一直留在原地，不能搬動、改名或刪除——Claude Code 每次都直接讀這個資料夾，搬走就會失效。」

## 第 2 步：檢查目前狀態（只讀，不改任何東西）

```powershell
$root = '<ROOT>'
$c = (Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $c) { $c = (Get-ChildItem -LiteralPath "$env:APPDATA\Claude\claude-code" -Directory -ErrorAction SilentlyContinue | Get-ChildItem -Directory | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'claude.exe') -ErrorAction SilentlyContinue } | Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]'0.0' } } -Descending | Select-Object -First 1).FullName }
if (-not $c) { 'STOP 找不到 Claude Code 程式'; return }
'Claude Code 程式：' + $c
'版本：' + (& $c --version)
$cfg = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
'設定資料夾：' + $cfg
$ids = @((& $c plugin list --json | Out-String | ConvertFrom-Json) | ForEach-Object { $_.id })
$matt = @($ids | Where-Object { $_ -like 'mattpocock-skills@*' })
if ($matt.Count -gt 0) { 'MATT 已經有了：' + ($matt -join '、') } else { 'MATT 還沒裝' }
$pj = Get-Content -LiteralPath (Join-Path $root '離線副本\mattpocock-skills\.claude-plugin\plugin.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$loose = @($pj.skills | ForEach-Object { Split-Path $_ -Leaf } | Where-Object { Test-Path -LiteralPath (Join-Path $cfg "skills\$_") })
if ($loose.Count -gt 0) { 'MATT-LOOSE 設定資料夾的 skills 裡已經有同名的 skill：' + ($loose -join '、') }
if ($ids -contains 'dev-bingfa@dev-bingfa') { 'DEV-BINGFA 已經裝過（這次會更新設定）' } else { 'DEV-BINGFA 還沒裝' }
$py = $null
foreach ($cand in 'py -3', 'python', 'python3') {
  $p = $cand -split ' '; $exe = $p[0]; $rest = @($p | Select-Object -Skip 1)
  if (Get-Command $exe -CommandType Application -ErrorAction SilentlyContinue) {
    & $exe @rest -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) { $py = $cand; break }
  }
}
if ($py) { 'PYTHON 有（' + $py + '）' } else { 'PYTHON 沒有可用的 Python 3.8 以上' }
```

**成功的樣子**：有 `Claude Code 程式：…`、`版本：…`，以及 `MATT …`、`DEV-BINGFA …`、`PYTHON …` 三行。記下這三行，後面要用。

- 出現 `STOP` → 停下來回報。
- 出現 `MATT-LOOSE` → 停下來，告訴使用者：「你的電腦好像已經用別的方式裝過 Matt Pocock 的工具（列出名字）。再裝外掛會讓每個工具出現兩次。要我跳過 Matt 的工具、只裝其他部分嗎？」等使用者回答。回答「跳過」就略過第 3 步。

## 第 3 步：安裝 Matt Pocock 的工具

- 第 2 步顯示 `MATT 已經有了` → **整步跳過**，不要再裝第二份。結果表寫「原本就有」。
- 顯示 `MATT 還沒裝` → 先做 3A。

### 3A 官方方式（需要連得上 GitHub，可能要等一兩分鐘）

```powershell
$c = (Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $c) { $c = (Get-ChildItem -LiteralPath "$env:APPDATA\Claude\claude-code" -Directory -ErrorAction SilentlyContinue | Get-ChildItem -Directory | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'claude.exe') -ErrorAction SilentlyContinue } | Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]'0.0' } } -Descending | Select-Object -First 1).FullName }
& $c plugin marketplace add anthropics/claude-plugins-official
if ($LASTEXITCODE -eq 0) { & $c plugin install mattpocock-skills@claude-plugins-official }
'結束碼：' + $LASTEXITCODE
```

**成功的樣子**：看到 `Successfully installed plugin: mattpocock-skills@claude-plugins-official`（或 `is already installed`），最後一行 `結束碼：0`。→ 跳到第 4 步。

**失敗**（結束碼不是 0，常見訊息是 `Failed to add marketplace`、`Failed to clone`、`Command 'git' not found`、`Could not connect`、連線逾時）→ 這代表這台電腦沒辦法從 GitHub 下載，這是預期中的情況，**不要重試**，改做 3B。錯誤訊息裡可能叫你設定 SSH 金鑰、`gh auth login` 或 credential helper：**不要照做**（那是登入），直接做 3B。

### 3B 離線副本（只有 3A 失敗才做）

```powershell
$root = '<ROOT>'
$c = (Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $c) { $c = (Get-ChildItem -LiteralPath "$env:APPDATA\Claude\claude-code" -Directory -ErrorAction SilentlyContinue | Get-ChildItem -Directory | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'claude.exe') -ErrorAction SilentlyContinue } | Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]'0.0' } } -Descending | Select-Object -First 1).FullName }
$ids = @((& $c plugin list --json | Out-String | ConvertFrom-Json) | ForEach-Object { $_.id })
if (@($ids | Where-Object { $_ -like 'mattpocock-skills@*' }).Count -gt 0) { 'STOP Matt 的外掛其實已經裝上了，不要再裝離線副本：' + ($ids -join '、'); return }
& $c plugin marketplace add (Join-Path $root '離線副本')
if ($LASTEXITCODE -eq 0) { & $c plugin install mattpocock-skills@mattpocock-offline }
'結束碼：' + $LASTEXITCODE
```

**成功的樣子**：看到 `Successfully installed plugin: mattpocock-skills@mattpocock-offline`，最後一行 `結束碼：0`。結果表寫「用離線副本安裝（連不上 GitHub）」。失敗 → 停下來回報。

## 第 4 步：安裝本包裹的主外掛

```powershell
$root = '<ROOT>'
$c = (Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $c) { $c = (Get-ChildItem -LiteralPath "$env:APPDATA\Claude\claude-code" -Directory -ErrorAction SilentlyContinue | Get-ChildItem -Directory | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'claude.exe') -ErrorAction SilentlyContinue } | Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]'0.0' } } -Descending | Select-Object -First 1).FullName }
& $c plugin marketplace add (Join-Path $root '外掛')
if ($LASTEXITCODE -eq 0) { & $c plugin install dev-bingfa@dev-bingfa }
'結束碼：' + $LASTEXITCODE
```

**成功的樣子**：看到 `Successfully added marketplace: dev-bingfa`（或 `already on disk`），再看到 `Successfully installed plugin: dev-bingfa@dev-bingfa`（或 `is already installed`），最後一行 `結束碼：0`。

如果輸出有 `now points at`：代表以前從別的資料夾裝過，現在改用這個資料夾。這不是錯誤，繼續做，但在結果表的「下一步」寫：「舊的包裹資料夾（輸出裡 `was already added from` 後面那個）已經不再使用。」

## 第 5 步：存檔自動檢查（選用）

- 第 2 步顯示 `PYTHON 沒有…` → **不要裝**，跳到第 6 步。結果表這一列寫：「**自動檢查這項沒啟用**——這台電腦沒有 Python 3.8 以上。其他功能照常。替代做法：每次交付前對 AI 說『交付前請檢查：這次改過的 Python 檔裡，有沒有 `except Exception:` 或 `except:` 後面只有 `pass` 的地方？每一處請說明上游怎麼知道失敗、我在哪裡看得到。』以後裝了 Python，再請 AI 照這份指示重跑一次就會補上。」
- 顯示 `PYTHON 有…` → 執行：

```powershell
$c = (Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $c) { $c = (Get-ChildItem -LiteralPath "$env:APPDATA\Claude\claude-code" -Directory -ErrorAction SilentlyContinue | Get-ChildItem -Directory | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'claude.exe') -ErrorAction SilentlyContinue } | Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]'0.0' } } -Descending | Select-Object -First 1).FullName }
& $c plugin install dev-bingfa-check@dev-bingfa
'結束碼：' + $LASTEXITCODE
```

**成功的樣子**：`Successfully installed plugin: dev-bingfa-check@dev-bingfa`（或 `is already installed`），`結束碼：0`。

## 第 6 步：把規則加到 `CLAUDE.md`

這一步會：先檢查原本的規則檔，再備份（同資料夾、檔名後面加 `.bak-dev-bingfa-日期時間`）；在檔尾加上一段用 `<!-- dev-bingfa:start 版本 -->` 和 `<!-- dev-bingfa:end -->` 包起來的規則（通用規則和工具附錄），換行方式跟著原檔；如果以前裝過（已經有這組標記），就只換掉標記中間那段，不會加第二次；標記外面的內容完全不動；原本沒有這個檔就新建。**第一次安裝**時，另外在結束標記下面放一段 `## Personal Preferences`（個人偏好的預設值）——那段算使用者自己的，之後重裝不會再加、也不會改。

```powershell
$root = '<ROOT>'
$dir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$target = Join-Path $dir 'CLAUDE.md'
$parts = 'CLAUDE.md', 'CLAUDE專用附錄.md'
$prefsFile = '個人偏好範例.md'
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
```

**成功的樣子**：第一行是 `OK 規則已附加在檔尾：…` 或 `OK 規則已更新（…）：…`，下面有 `備份：…`、`個人偏好：…` 和 `檔案大小：…`。記下 `個人偏好：` 那一行，結果表要用。

## 第 7 步：最後自我檢查

```powershell
$c = (Get-Command claude -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $c) { $c = (Get-ChildItem -LiteralPath "$env:APPDATA\Claude\claude-code" -Directory -ErrorAction SilentlyContinue | Get-ChildItem -Directory | ForEach-Object { Get-Item -LiteralPath (Join-Path $_.FullName 'claude.exe') -ErrorAction SilentlyContinue } | Sort-Object { try { [version]$_.Directory.Parent.Name } catch { [version]'0.0' } } -Descending | Select-Object -First 1).FullName }
& $c plugin list
$dir = if ($env:CLAUDE_CONFIG_DIR) { $env:CLAUDE_CONFIG_DIR } else { Join-Path $env:USERPROFILE '.claude' }
$t = Get-Content -LiteralPath (Join-Path $dir 'CLAUDE.md') -Raw -Encoding UTF8
'規則區塊開始標記數：' + ([regex]::Matches($t, '<!-- dev-bingfa:start ')).Count + '　結束標記數：' + ([regex]::Matches($t, '<!-- dev-bingfa:end -->')).Count
```

**成功的樣子**：清單裡有 `dev-bingfa@dev-bingfa`（`enabled`）、一個 `mattpocock-skills@…`（`enabled`）、有 Python 時還有 `dev-bingfa-check@dev-bingfa`；最後一行兩個數字都是 `1`。不符合 → 在結果表標出哪一項不對，並回報。

## 第 8 步：回報給使用者

用白話繁體中文，給使用者一張表，四列都要有（某一格沒有要做的事就寫「無」）：

| 項目 | 結果（裝好了／原本就有／沒裝） | 為什麼 | 下一步 |
|---|---|---|---|
| Matt Pocock 的工具 | | 官方方式、離線副本、或原本就有 | |
| dev-bingfa 主外掛 | | | |
| 存檔自動檢查 | | 沒有 Python 就寫「自動檢查這項沒啟用」和第 5 步的替代做法 | |
| 規則檔 `CLAUDE.md` | | 寫出檔案位置和備份位置 | |

表格後面一定要說這幾句：

1. 「請把 Claude 桌面 App **完全關閉**（包含右下角系統匣的圖示）再重開，新的東西才會載入。」
2. 「重開後開一個新對話，在輸入框打 `/`，應該會看到 `/dev-bingfa:commit`、`/dev-bingfa:brownfield-recon` 和 `/mattpocock-skills:grill-me` 這類名字。看不到就把畫面拍給維護人。」
3. 「這個包裹資料夾（寫出 `<ROOT>`）要一直留在原地，不能搬動、改名或刪除。」
4. 「規則檔裡 `<!-- dev-bingfa:start` 到 `<!-- dev-bingfa:end -->` 那段由安裝程序管理，重裝時會被換回新版。結束標記下面的 `## Personal Preferences` 是你的個人偏好（回覆語言、模型等），想改就直接改那一段，重裝不會動它。」（如果第 6 步的 `個人偏好：` 說沒有再加，就說「沿用你原本的個人偏好」。）
5. 如果有任何一步沒做完：明確列出哪些沒裝、卡在哪一步。
