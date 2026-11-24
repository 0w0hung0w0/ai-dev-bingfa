# 證據 05：Claude Code 完整版外掛

日期：2026-11-24。Claude Code 版本：`2.1.330`。所有安裝測試都在**隔離的設定資料夾**裡做（`CLAUDE_CONFIG_DIR` 指到 `.scratch/dev-bingfa/research/sandbox/card05/claude-home`），沒有登入、沒有動到真正的 `~/.claude`。

測試留下的原始輸出都在 `.scratch/dev-bingfa/research/sandbox/card05/`：
`validate-final.txt`、`install.txt`、`hook-matrix.txt`、`agent-diff.txt`、`before.txt`、`after.txt`，以及測試工具 `run_hook.py`。

---

## 1. 外掛裡有什麼

外掛目錄（marketplace）：`dev-bingfa/外掛/`，裡面兩個外掛。

**`dev-bingfa`（主外掛）**

| 東西 | 叫法（工具實際顯示的名字） |
|---|---|
| skill：既有專案探勘 | `dev-bingfa:brownfield-recon` |
| skill：影響範圍檢查 | `dev-bingfa:blast-radius` |
| skill：接縫對帳 | `dev-bingfa:seam-audit` |
| skill：提交 | `dev-bingfa:commit`（在對話裡打 `/dev-bingfa:commit`） |
| 助手：讀碼調查 | `dev-bingfa:explorer` |
| 助手：照計畫實作 | `dev-bingfa:implementer` |
| 助手：網路搜尋 | `dev-bingfa:web-search-agent` |
| 搜尋策略（網路搜尋助手會讀） | `web-search-modules/` 五個檔，簡體中文原文，一字未改 |
| 說明 | `README.md` |

`web-search-modules/` 放在外掛根目錄，**不在** `agents/` 底下，所以 Claude Code 不會把它們誤當成助手（下面的檢查結果只列出 3 個助手可以證明）。

**`dev-bingfa-check`（選用外掛，存檔時自動檢查）**

| 檔案 | 作用 |
|---|---|
| `hooks/hooks.json` | 兩個時機：開對話時（`SessionStart`）、AI 寫檔或改檔後（`PostToolUse`，`Write|Edit`），逾時 10 秒 |
| `hooks/run.sh` | 給 macOS、Linux、Windows Git Bash 用的「找 Python」小程式 |
| `hooks/run.cmd` | 給沒裝 Git 的 Windows（Claude Code 改用 PowerShell 跑）用的同一個小程式 |
| `hooks/check_silence.py` | 真正做檢查的腳本，**和來源一模一樣**（`cmp` 比對相同） |
| `hooks/no-python.json` | 沒有 Python 時要顯示的「這項沒啟用」訊息 |
| `README.md` | 白話說明：檢查什麼、怎麼看它有沒有在動 |

---

## 2. 每個助手和來源比，改了什麼、為什麼

完整比對在 `agent-diff.txt`（忽略換行符號差異）。

| 助手 | 改了什麼 | 為什麼 |
|---|---|---|
| `explorer` | 拿掉 `model: opus` 這一行 | 模型名稱在這個包裹裡算「個人偏好」；拿掉後助手跟著對話用的模型走。官方文件沒有說拿掉會壞掉 |
| `implementer` | 拿掉 `model: opus` | 同上 |
| `web-search-agent` | ① 拿掉 `model: opus` | 同上 |
| | ② 取日期：原本叫它跑 `date +%Y-%m-%d`（Windows PowerShell 沒有這個指令），改成「先用對話裡已有的今天日期；沒有才跑 `Get-Date -Format yyyy-MM-dd`（Windows）或 `date +%Y-%m-%d`（Mac/Linux/Git Bash）」 | 同事多半用 Windows |
| | ③ 搜尋策略的位置：原本寫死 `~/.claude/agents/web-search-modules/`，改成 `${CLAUDE_PLUGIN_ROOT}/web-search-modules/`，並加一句備案：如果看到的還是 `${CLAUDE_PLUGIN_ROOT}` 字樣，就用 Glob 找 `**/dev-bingfa/web-search-modules/*.md` | 裝成外掛後，檔案不在 `~/.claude/agents/` |

外掛會忽略的欄位（`permissionMode`、`hooks`、`mcpServers`、`initialPrompt`）：三個來源檔**本來就沒有**，所以拿掉後沒有少任何限制。來源也沒有 `tools:` 欄位，行為不變。

**為什麼用 `${CLAUDE_PLUGIN_ROOT}` 而不是把五個策略檔直接貼進助手：** 官方文件 `https://code.claude.com/docs/en/plugins-reference.md` 的「Where each variable resolves」表寫明 “Skill, command, and agent content | Anywhere in the Markdown body”，也就是助手內文裡的 `${CLAUDE_PLUGIN_ROOT}` 會在載入時被換成外掛的實際路徑。這樣可以維持原本「只讀需要的那幾份」的設計，不用每次都把五份全部塞給助手。風險是：這件事**只有文件根據、沒有實測**（要真的開對話派助手才看得到，需要登入），所以另外加了 Glob 備案那一句。

---

## 3. 檢查與安裝的指令和結果

（指令都用完整路徑執行 `claude.exe`，並先設定 `CLAUDE_CONFIG_DIR` 到隔離資料夾。）

### 3.1 `claude plugin validate`（三個都通過，沒有警告）

```
> claude plugin validate "...\dev-bingfa\外掛"
✔ Validation passed

> claude plugin validate "...\dev-bingfa\外掛\dev-bingfa"
  ❯ skills: dev-bingfa:blast-radius
  ❯ skills: dev-bingfa:brownfield-recon
  ❯ skills: dev-bingfa:commit
  ❯ skills: dev-bingfa:seam-audit
  ❯ agents: dev-bingfa:explorer
  ❯ agents: dev-bingfa:implementer
  ❯ agents: dev-bingfa:web-search-agent
✔ Validation passed

> claude plugin validate "...\dev-bingfa\外掛\dev-bingfa-check"
  ❯ hooks: SessionStart command "…"
  ❯ hooks: PostToolUse Write|Edit command "…"
✔ Validation passed
```

先前的警告（缺 marketplace `description`、缺 `author`）已經消失：兩個 `plugin.json` 加了 `"author": {"name": "AI 系統開發兵法 維護人"}`（沒有 email），marketplace 加了 `description`。

另外有兩項「**投稿到 Anthropic 官方外掛目錄**才需要」的提醒：缺 `LICENSE`、缺圖示。這個包裹不公開發布，所以沒有處理；它們不影響安裝結果（輸出寫明 “These plugin directory checks do not change the result below”）。

### 3.2 安裝與清單（`install.txt`）

```
> claude plugin marketplace add "...\dev-bingfa\外掛"
✔ Successfully added marketplace: dev-bingfa (declared in user settings)
> claude plugin install dev-bingfa@dev-bingfa
✔ Successfully installed plugin: dev-bingfa@dev-bingfa (scope: user)
> claude plugin install dev-bingfa-check@dev-bingfa
✔ Successfully installed plugin: dev-bingfa-check@dev-bingfa (scope: user)
> claude plugin list
  ❯ dev-bingfa-check@dev-bingfa   Version: 1.0.0   Status: ✔ enabled
  ❯ dev-bingfa@dev-bingfa         Version: 1.0.0   Status: ✔ enabled
> claude plugin details dev-bingfa@dev-bingfa
  Skills (4)  blast-radius, brownfield-recon, commit, seam-audit
  Agents (3)  explorer, implementer, web-search-agent
  Hooks (0)
> claude plugin details dev-bingfa-check@dev-bingfa
  Hooks (2)  SessionStart, PostToolUse
```

注意：`plugin list` 顯示 `Read from: ...\dev-bingfa\外掛\dev-bingfa`——從本機資料夾裝的外掛是**直接讀那個資料夾**。所以同事裝完之後不能搬動或刪掉解壓出來的包裹（`包裹地圖.md` 已經寫了這點）。

寫入位置都在隔離資料夾：`claude-home\settings.json`（`enabledPlugins`、`extraKnownMarketplaces`）、`claude-home\plugins\`。

---

## 4. 存檔檢查：有 Python／沒有 Python

### 4.1 怎麼設計

- Windows 上 Claude Code 跑 hook 用的程式**不一定一樣**：有裝 Git 就用 Git Bash，沒裝就用 PowerShell（官方文件 hooks 頁：“Git Bash on Windows, or PowerShell when Git Bash isn't installed”；setup 頁：Git for Windows 是選配）。Mac/Linux 用 `sh`。
- 所以 `hooks.json` 裡的指令寫成**同一段在兩種環境都能跑**：前半段 sh 看得懂、跑 `run.sh` 後就結束；PowerShell 把前半段當註解（`<# … #>`），改跑後半段的 `run.cmd`。不需要 Node，也不用 PowerShell 腳本檔（避開公司電腦常見的腳本執行限制）。
- `run.sh`／`run.cmd` 依序試 `python3`、`python`、`py -3`（`run.cmd` 先試 `py -3`），**真的執行一次 `-c "import sys"` 成功才算有 Python**。Windows 內建那個「叫你去 Microsoft Store 安裝」的假 python 會回傳失敗，所以不會被誤認。
- 沒有 Python 時：
  - 存檔後的檢查 → **安靜跳過、回傳成功**，不會每次存檔都跳錯誤。
  - 開對話時 → 輸出 `no-python.json`：`systemMessage`（官方文件：“Warning message shown to the user”）顯示
    「dev-bingfa-check：存檔自動檢查「這項沒啟用」——這台電腦找不到 Python。其他功能照常可用；要啟用請先安裝 Python 3，再重開 Claude Code。」
    同時用 `additionalContext` 告訴 AI，請它在第一次回覆時用白話跟使用者說「存檔自動檢查這項沒啟用」。兩條路一起走，萬一其中一條沒顯示，另一條還在。
  - 訊息內容用 `\uXXXX` 寫成純英數字元，避免 Windows 中文編碼（cp950）造成亂碼。

### 4.2 測試方法

`run_hook.py` 模仿 Claude Code：讀 `hooks.json` 的指令、把 `${CLAUDE_PLUGIN_ROOT}` 換成外掛路徑（sh 用正斜線，PowerShell 用反斜線，照官方文件說法），然後
- **sh 路線**：`C:\Program Files\Git\usr\bin\sh.exe -c <指令>`
- **PowerShell 路線**：`powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand <指令>`（旗標取自 `claude.exe` 內 PowerShell 的預設參數）

並從 stdin 餵入真實格式的 PostToolUse JSON（`tool_name: Write`、`tool_input.file_path`、`tool_response.filePath`，照官方文件範例）。

「沒有 Python」的 PATH：只留 `System32`、Windows PowerShell、Git 的 `usr\bin`（為了 `sh`），再加上一個 `stubbin\` 資料夾，裡面放**模擬的** Microsoft Store 假 python（印出同樣的訊息、回傳 9009）。故意不放 `C:\Windows`（`py.exe` 在那裡）、`WindowsApps` 和真正的 Python。

真正的 Store 假 python 也實際跑過一次確認它會失敗：
```
> ...\WindowsApps\python3.7.exe -c "import sys"
Python was not found but can be installed from the Microsoft Store: ms-windows-store://pdp/?productid=9NJ46SX7X90P
stub exit=49
```
（無法把真的假 python 複製到測試資料夾——系統拒絕存取——所以 PATH 測試用的是模擬版。）

### 4.3 結果（`hook-matrix.txt`）

| 路線 | 情況 | 結束碼 | 看到什麼 |
|---|---|---|---|
| sh | 有 Python，`bad.py`（含 `except Exception: pass`） | **2** | 「⚠️ 靜默失敗檢查：bad.py 的 第 5 行 有「廣泛捕捉例外後什麼都不做」…」 |
| sh | 有 Python，`good.py`（乾淨） | **0** | 沒有輸出 |
| sh | 有 Python，開對話 | 0 | 沒有輸出（安靜＝正常） |
| sh | **沒 Python**，`bad.py` | 0 | 沒有輸出（不吵） |
| sh | **沒 Python**，`good.py` | 0 | 沒有輸出 |
| sh | **沒 Python**，開對話 | 0 | 印出「這項沒啟用」的 JSON |
| PowerShell | 有 Python，`bad.py` | **2** | 同一段中文警告 |
| PowerShell | 有 Python，`good.py` | **0** | 沒有正式輸出 |
| PowerShell | 有 Python，開對話 | 0 | 沒有正式輸出 |
| PowerShell | **沒 Python**，`bad.py` / `good.py` | 0 | 沒有正式輸出 |
| PowerShell | **沒 Python**，開對話 | 0 | 印出「這項沒啟用」的 JSON |

有 Python 時 `bad.py` 的完整警告（sh 路線）：

```
⚠️ 靜默失敗檢查：bad.py 的 第 5 行 有「廣泛捕捉例外後什麼都不做」。

    5: except Exception:

請針對每一處說明：
  1. 這裡吞掉例外之後，上游怎麼知道這一步失敗了？
  2. 使用者在哪裡看得到？（寫進 log 不算）
...
```

沒有 Python 時開對話的輸出（解碼後）：
```
systemMessage: dev-bingfa-check：存檔自動檢查「這項沒啟用」——這台電腦找不到 Python。其他功能照常可用；要啟用請先安裝 Python 3，再重開 Claude Code。
```

**PowerShell 路線的小瑕疵：** 每次執行，PowerShell 都會在錯誤輸出多吐一段 `#< CLIXML <Objs …progress…>`（PowerShell 啟動時「準備模組」的進度訊息，在指令開始前就發生，指令裡關掉進度也擋不到）。結束碼 0 時 Claude Code 不看錯誤輸出，沒影響；結束碼 2 時，AI 收到的警告後面會多一段這種雜訊，中文警告本身完整可讀。Claude Code 實際怎麼呼叫 PowerShell 跑 hook、會不會自己濾掉這段，沒有驗證。

### 4.4 Mac／Linux 會怎樣

走 `run.sh`（用 `sh run.sh`，所以不需要執行權限，解壓 zip 掉了權限也沒關係）。Mac 通常有 `python3`；沒有的話（新 Mac 的 `python3` 可能是「要你安裝開發工具」的替身，會回傳失敗）就顯示「這項沒啟用」。**這條路只在 Windows 的 Git Bash `sh` 上模擬過，沒有在真的 Mac/Linux 上跑。**

---

## 5. `~/.claude` 沒有被改到

做之前與做完之後，各列一次 `~/.claude` 底下**只有這幾處**的檔名、大小、修改時間：`agents/`、`hooks/`、`commands/`、`skills/`、`CLAUDE.md`、`settings.json`（其他資料夾沒有列、也沒有讀）。

```
> diff before.txt after.txt
before/after IDENTICAL (54 entries)
```

兩份清單在 `sandbox/card05/before.txt`、`after.txt`，內容完全相同（54 筆）。

---

## 6. 沒有驗證的事（老實列出）

1. **真的在對話裡觸發 hook**：沒有。隔離資料夾沒登入，不能開對話；依指示不登入。上面的 hook 測試是「照 Claude Code 的方式自己執行同一段指令」，不是 Claude Code 本身觸發的。留給任務卡 12（乾淨環境實裝）驗證：
   - 開對話時「這項沒啟用」是不是真的顯示在畫面上（`systemMessage` 在 `SessionStart` 的顯示方式，文件沒有逐字寫明）。
   - Windows 有 Git／沒 Git 兩種情況下，Claude Code 是不是真的照文件選 Git Bash／PowerShell，以及那段「兩用指令」在 Claude Code 裡跑起來和模擬一致。
   - PowerShell 路線的 CLIXML 雜訊在實際環境會不會出現。
2. **助手內文的 `${CLAUDE_PLUGIN_ROOT}` 會被換成路徑**：只有官方文件根據，沒實測（要派出助手才看得到）。已加 Glob 備案。
3. **拿掉 `model:` 後助手跟著對話模型走**：文件的一般規則，沒實測。
4. **三個助手實際被派工、`/dev-bingfa:commit` 實際執行**：沒有（要登入）。本卡只證明它們出現在清單裡。
5. **Mac／Linux**：沒實機測。
6. **Codex**：`dev-bingfa-check` 的 `hooks/hooks.json` 若被 Codex 載入，行為未測（研究 01b 已記錄 Codex 自訂 hook 在這台電腦跑不起來）。
7. **路徑有空白**：測試路徑含中文、沒有空白；兩條路線都有加引號，但沒有用含空白的路徑實測。

## 7. 其他附帶說明

- 刪掉了 `dev-bingfa-check/hooks/.gitkeep`（資料夾已經有檔案，不需要了）。`dev-bingfa/agents/.gitkeep` 保留沒動。
- `run.cmd` 用 `call` 呼叫 Python：如果某人的 `python` 是 `.bat`/`.cmd` 轉接檔（例如 pyenv-win），沒有 `call` 會讓整個小程式中途結束；加了就沒這問題。
- 沒有 commit、沒有 `git add`。沒有動 `skills/`、`規則/`、`離線副本/`。

---

## 審查後修正（2026-11-24，依 `審查-05-06-07.md`）

原始輸出：`.scratch/dev-bingfa/research/sandbox/review-050607/fix/`（`test-hooks-after.txt`、`test-hooks-before.txt`、`mutate-rerun.txt`）。`check_silence.py` 仍沒動（SHA-256 `FF5640AC…4C39`）。

| 審查項目 | 修了什麼 |
|---|---|
| S1 舊版 Python 安靜失效 | `run.sh`、`run.cmd` 找 Python 時改成真的檢查版本：`-c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"`。Python 2、3.7 以前都當成「沒有 Python」：存檔時安靜跳過，開對話時出現「這項沒啟用」提示 |
| S3 備案搜尋樣式找不到 | 網路搜尋助手的備案改成在 `plugins/cache/` 底下找 `**/web-search-modules/*.md`，並寫明檔案放在版本子資料夾裡（Codex 版同步改，見證據 06） |
| S6 搬動資料夾寫太輕 | `包裹地圖.md` 改成：裝完就**不能**搬動、改名或刪掉解壓後的資料夾，否則 Claude Code 馬上載入失敗（審查實測 `failed to load: cache-miss`）；Codex 上的後果未實測 |
| Nit 1 README 寫的順序和程式不同 | `dev-bingfa-check/README.md` 分開寫兩種順序：`run.sh` 是 `python3` → `python` → `py -3`；`run.cmd` 是 `py -3` → `python` → `python3`；並寫明要 3.8 以上 |
| Nit 2 explorer「只讀不改」 | 主外掛 README 改成「原則上只讀不改（這是寫在指示裡的要求，不是技術上的限制）」 |
| Nit 3 多餘的 `.gitkeep` | 刪掉 `外掛/dev-bingfa/agents/.gitkeep`（推翻第 7 節「保留沒動」） |
| Nit 4 PowerShell 半段沒有備案 | PowerShell 那半段改成先用代入的路徑，沒有代入時改用 `$env:CLAUDE_PLUGIN_ROOT`；結束碼不變。sh 半段沒改（sh 跑到 `exit $?` 就結束，不會讀到後面）。更正審查的一句話：整段指令用 `bash -n` 檢查**本來就**會在 PowerShell 那行 `&` 報語法錯（修改前也一樣），但 sh 是讀一行跑一行，跑到 `exit` 就停，所以不影響；矩陣的 sh 路線全部通過 |
| Nit 5 輸入有 BOM 就不檢查 | `post_check.py` 改用 `utf-8-sig` 解碼 |
| S2（同一支 `post_check.py`） | 見證據 06 |

### 測試矩陣（`tools/test-hooks.py`，已移進 `tools/`）

自己在系統暫存資料夾建一份外掛複本，路徑含空白和中文（`…\路徑 測試 空白\my plugin\dev-bingfa-check`、專案在 `…\專案 資料夾`），跑完就刪。五條路線：`claude-sh`、`claude-ps`、`claude-ps-env`（不代入路徑，只靠環境變數）、`codex-cmd`、`codex-sh`。三種 Python：有、沒有（模擬 Microsoft Store 假 python）、太舊（假 python 回報 2.7，執行腳本時印 SyntaxError）。

- 修改後：`SUMMARY|PASS|98 cases, 0 failed; 300-file patch: 300.md=0.13s, 300.py=0.16s`
- 對修改前的複本（審查留下的 `空白 中文 路徑` 那份）跑同一支：`SUMMARY|FAIL|98 cases, 25 failed; 300-file patch: 300.md=12.13s, 300.py=12.11s`。失敗的就是 S1（舊版 Python：沒提示、還漏出 SyntaxError）、S2（太慢）、Nit 4（沒代入路徑時抓不到、沒提示）、Nit 5（BOM）。

### `claude plugin validate`（Claude Code 2.1.330，完整路徑 `claude.exe`，`CLAUDE_CONFIG_DIR` 指到沙盒）

```
外掛（marketplace）      √ Validation passed
外掛\dev-bingfa          √ Validation passed   agents: dev-bingfa:explorer / dev-bingfa:implementer / dev-bingfa:web-search-agent；skills 4 個
外掛\dev-bingfa-check    √ Validation passed   hooks: SessionStart、PostToolUse Write|Edit
```

只有「投稿官方目錄才需要」的提醒（沒有 LICENSE、沒有圖示），不影響結果。

### 仍未驗證

- 真的在 Claude Code 對話裡觸發 hook（要登入）；Claude Code 執行 hook 時有沒有設定 `CLAUDE_PLUGIN_ROOT` 環境變數（PowerShell 備案靠它；文件這麼寫，沒實測）。
- 真的 Python 2／3.7（矩陣用的是模擬的假 python）。