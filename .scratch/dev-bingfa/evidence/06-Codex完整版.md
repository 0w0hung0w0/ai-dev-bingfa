# 證據 06：Codex 完整版

日期：2026-11-24。`codex-cli 0.140.0`、`2.1.330 (Claude Code)`、Windows 10、Python 3.12。
全程用隔離設定：`CODEX_HOME` = `.scratch/dev-bingfa/research/sandbox/card06/codex-home`，`CLAUDE_CONFIG_DIR` = `.../card06/claude-home`。沒有登入、沒有提供任何憑證、沒有 commit、沒有 `git add`，沒有動 `~/.claude`、`~/.codex`、`~/.agents`、`C:\ProgramData\OpenAI`。

原始輸出都在 `.scratch/dev-bingfa/research/sandbox/card06/`：`prompt-input-1.json`／`-2.json`／`-3.json`、`exec-1.err`、`exec-2.err`、`codex-hook-matrix.txt`、`claude-hook-recheck.txt`、`claude-validate-check.txt`、`agent-diff.txt`，測試工具 `run_codex_hook.py`、`agent_diff.py`。

---

## 1. 這張卡新增／修改了哪些檔案

| 檔案 | 動作 | 為什麼 |
|---|---|---|
| `dev-bingfa/codex/agents/bingfa-explorer.toml` | 新增 | Codex 版讀碼調查助手 |
| `dev-bingfa/codex/agents/bingfa-implementer.toml` | 新增 | Codex 版實作助手 |
| `dev-bingfa/codex/agents/bingfa-web-search-agent.toml` | 新增 | Codex 版網路搜尋助手 |
| `dev-bingfa/codex/agents/.gitkeep` | 刪除 | 資料夾已有檔案，不需要了 |
| `dev-bingfa/codex/README.md` | 新增 | 白話說明與對照表 |
| `dev-bingfa/外掛/dev-bingfa/skills/commit/agents/openai.yaml` | 新增 | Codex 的「只能手動叫」設定（第 3 節）。Claude Code 不讀這個檔 |
| `dev-bingfa/外掛/dev-bingfa-check/hooks/hooks.json` | 修改 | ① 拿掉最上層 `description`（Codex 因為它拒絕整個檔案）② 每個 hook 加 `commandWindows`（只有 Codex 在 Windows 上會用）。`command` 一字未改 |
| `dev-bingfa/外掛/dev-bingfa-check/hooks/codex_post.py` | 新增 | Codex 專用轉接：把 `apply_patch` 的輸入轉成 `check_silence.py` 看得懂的樣子 |
| `dev-bingfa/外掛/dev-bingfa-check/hooks/codex-post.cmd` | 新增（CRLF） | Codex 在 Windows 跑 `codex_post.py` 的小程式（找 Python 的方式和 `run.cmd` 相同） |
| `.gitattributes`（repo 根） | 新增 | 換行符號規則（第 6 節） |

`check_silence.py`、`run.sh`、`run.cmd`、`no-python.json`、所有 `SKILL.md`、`規則/`、`離線副本/` 都沒有動。

被拿掉的 `description` 原文（給維護人參考）：「dev-bingfa-check：存檔後檢查「廣泛捕捉例外後什麼都不做」；沒有 Python 時在對話開頭提示「這項沒啟用」。同一行指令在 sh/Git Bash 與 PowerShell 都能跑（前半給 sh，<# #> 之後給 PowerShell）。」Claude Code 文件說這個欄位是選填，只是說明文字。

---

## 2. 助手（3 個）

### 2.1 內容和 Claude Code 版比

`agent_diff.py` 的結果（`agent-diff.txt`）：

```
===== explorer.md  vs  bingfa-explorer.toml
description 相同： True
內文差異行數： 0
===== implementer.md  vs  bingfa-implementer.toml
description 相同： True
內文差異行數： 0
===== web-search-agent.md  vs  bingfa-web-search-agent.toml
description 相同： True
內文差異行數： 4
```

網路搜尋助手只改了兩行：
- 「先讀策略檔」那一行：`${CLAUDE_PLUGIN_ROOT}` 在 Codex 的助手檔裡不會被換成路徑，所以改寫成 Codex 安裝外掛後的固定位置 `<Codex home>/plugins/cache/dev-bingfa/dev-bingfa/<版本>/web-search-modules/`，並保留「找不到就搜 `**/dev-bingfa/web-search-modules/*.md`」的備案；Claude 專用的工具名 `Read`、`Glob`、`WebSearch`、`WebFetch` 改成一般說法。
- 「不准跳過」那一行：同樣換掉工具名，**另外加了一句**「完全找不到策略檔時要在回報裡說出來」。這句原版沒有，是我加的（避免默默跳過）。

沒有寫 `model` 欄位（個人偏好）。必填三欄都有：

```
> python -c "import tomllib ..."
bingfa-explorer.toml ['description', 'developer_instructions', 'name'] bingfa-explorer
bingfa-implementer.toml ['description', 'developer_instructions', 'name'] bingfa-implementer
bingfa-web-search-agent.toml ['description', 'developer_instructions', 'name'] bingfa-web-search-agent
```

### 2.2 Codex 讀不讀得到（`exec-1.err`）

在 `$CODEX_HOME/agents/` 放：三個正式助手、一個故意缺欄位的 `broken-top.toml`、子資料夾裡另一個壞檔 `nested/broken-nested.toml`、以及子資料夾 `web-search-modules/` 裡 5 個 `.md`。執行 `codex exec --skip-git-repo-check hi`（未登入，會在連線時 401）：

```
warning: Ignoring malformed agent role definition: agent role file at ...\codex-home\agents\broken-top.toml must define `developer_instructions`
warning: Ignoring malformed agent role definition: agent role file at ...\codex-home\agents\nested\broken-nested.toml must define `developer_instructions`
```

結論：
- Codex 會讀這個資料夾，**連子資料夾也會讀**；壞檔會被點名，三個正式助手沒有任何警告（＝格式通過）。這是間接證據，Codex 沒有不登入就能列出助手清單的指令。
- 子資料夾裡的 `.md` 沒有引起任何警告，Codex 能容忍非 TOML 檔。但我們**沒有**用這條路（見 2.3）。

### 2.3 搜尋策略檔放哪裡

`codex plugin add dev-bingfa@dev-bingfa` 會把整個外掛（包括 `web-search-modules/`）複製到快取：

```
<CODEX_HOME>\plugins\cache\dev-bingfa\dev-bingfa\1.0.0\web-search-modules\academic-papers.md
<CODEX_HOME>\plugins\cache\dev-bingfa\dev-bingfa\1.0.0\web-search-modules\chinese-tech.md
<CODEX_HOME>\plugins\cache\dev-bingfa\dev-bingfa\1.0.0\web-search-modules\general-web.md
<CODEX_HOME>\plugins\cache\dev-bingfa\dev-bingfa\1.0.0\web-search-modules\github-debug.md
<CODEX_HOME>\plugins\cache\dev-bingfa\dev-bingfa\1.0.0\web-search-modules\stackoverflow.md
```

所以助手直接讀這個位置，repo 裡**不需要再存一份**，也就不需要加「兩份內容相同」的檢查。代價：沒裝 `dev-bingfa` 外掛、只複製助手檔的人，網路搜尋助手會找不到策略檔（指示裡已要求它說出來）。助手真的會不會去讀、讀不讀得到：要派工才知道，**未實測**。

---

## 3. skill 與 `commit` 的「只能手動叫」

### 3.1 裝外掛

```
> codex plugin marketplace add "<專案>\dev-bingfa\外掛"
Added marketplace `dev-bingfa` from \\?\C:\...\dev-bingfa\外掛.
> codex plugin add dev-bingfa@dev-bingfa
Added plugin `dev-bingfa` from marketplace `dev-bingfa`.
Installed plugin root: ...\card06\codex-home\plugins\cache\dev-bingfa\dev-bingfa\1.0.0
> codex plugin add dev-bingfa-check@dev-bingfa
Added plugin `dev-bingfa-check` from marketplace `dev-bingfa`.
> codex plugin list
dev-bingfa@dev-bingfa        installed, enabled  1.0.0
dev-bingfa-check@dev-bingfa  installed, enabled  1.0.0
```

### 3.2 AI 看得到哪些 skill（`codex debug prompt-input "hi"`，不需登入）

| 時間點 | 清單裡的 dev-bingfa skill |
|---|---|
| 加 `openai.yaml` 之前（`prompt-input-1.json`） | `dev-bingfa:blast-radius`、`dev-bingfa:brownfield-recon`、`dev-bingfa:commit`、`dev-bingfa:seam-audit` |
| 加 `openai.yaml` 之後（`prompt-input-2.json`） | `dev-bingfa:blast-radius`、`dev-bingfa:brownfield-recon`、`dev-bingfa:seam-audit` |

- 證明一：Codex **不理會** Claude 的 `disable-model-invocation: true`——沒加 `openai.yaml` 時 `commit` 照樣在 AI 可自動選用的清單裡。
- 證明二：官方文件（`https://learn.chatgpt.com/docs/build-skills`）寫 `agents/openai.yaml` 的 `policy.allow_implicit_invocation`「When `false`, Codex won't implicitly invoke the skill based on user prompt; explicit `$skill` invocation still works.」加上後 `commit` 從清單消失。
- Claude Code 不受影響：`claude plugin validate` 照樣通過，`claude plugin details` 仍是 `Skills (4) blast-radius, brownfield-recon, commit, seam-audit`、`Agents (3)`。
- **未實測**：使用者手動打 `$dev-bingfa:commit`（或從 `/skills` 選）還叫不叫得起來——要登入開 TUI。文件說可以。

使用者的叫法（官方文件，未實測）：打 `$` 跳出清單選，或 `/skills`。

### 3.3 規則檔（`prompt-input-3.json`）

把 `規則/AGENTS.md` 複製成 `$CODEX_HOME/AGENTS.md`，再跑 `codex debug prompt-input`：通用規則 71 行（長度超過 25 字的行）**全部**出現在 AI 收到的指示裡，第一行 `# Common Rules` 也在。檔案 8,702 位元組，低於 Codex 預設 32 KiB 上限。

整台電腦：`~/.codex/AGENTS.md`（有設 `CODEX_HOME` 時是那個資料夾）。單一專案：專案根目錄的 `AGENTS.md`（研究 01b 第 7 題已實測讀取順序）。個人偏好：`規則/個人偏好範例.md` 已寫「Codex：`~/.codex/AGENTS.md`，接在通用規則之後」，本卡沒有新增規則內容。

---

## 4. 存檔檢查（`dev-bingfa-check`）在 Codex

### 4.1 查到的事實

| 問題 | 答案 | 來源 |
|---|---|---|
| Codex 寫檔工具叫什麼 | `apply_patch`；matcher 寫 `Edit`、`Write` 也會對到它，但輸入裡的 `tool_name` 仍是 `apply_patch` | `https://learn.chatgpt.com/docs/hooks`（matcher 段） |
| 改了哪個檔放在哪 | 沒有 `file_path`。整段修補內容在 `tool_input.command`（`*** Begin Patch` / `*** Update File: 路徑` …） | 同上；原始碼 `codex-rs/hooks/src/events/post_tool_use.rs` 註解「Shell-like tools pass `{ "command": ... }` as `tool_input`」 |
| `check_silence.py` 直接用找得到檔案嗎 | **找不到**，而且 `tool_response` 若是字串會讓它當掉（見 4.3 對照） | 本機實測 |
| exit 2 | PostToolUse exit 2＋stderr＝把警告餵回 AI；stderr 空的會被當失敗 | `post_tool_use.rs` |
| Windows 上怎麼執行 | 有 `commandWindows` 就用它；`${CLAUDE_PLUGIN_ROOT}` 由 Codex 自己做文字替換；用 `%COMSPEC%`（cmd.exe）`/C` 執行 | `codex-rs/hooks/src/engine/discovery.rs`、`command_runner.rs`（GitHub main 分支，**不一定等於 0.140.0**） |
| Claude Code 會不會用 `commandWindows` | 不會。Claude Code hook 文件沒有這個欄位；`claude.exe` 內的 `commandWindows` 字串只出現在「登入憑證小程式」設定 | `https://code.claude.com/docs/en/hooks.md`；搜尋 `claude.exe` 字串 |

### 4.2 原本的 `hooks.json` 在 Codex 根本沒被載入（`exec-1.err`）

```
warning: failed to parse plugin hooks config ...\dev-bingfa-check\1.0.0\hooks\hooks.json: unknown field `description`, expected `hooks` at line 2 column 15
```

拿掉 `description` 後再跑一次（`exec-2.err`），這行警告消失。就算載入了，原本的 `command` 是 sh／PowerShell 兩用寫法，cmd.exe 看不懂，所以另加 `commandWindows`：

- `SessionStart` → `"${CLAUDE_PLUGIN_ROOT}\hooks\run.cmd" session`（沿用原本的 `run.cmd`）
- `PostToolUse` → `"${CLAUDE_PLUGIN_ROOT}\hooks\codex-post.cmd"` → `codex_post.py` → 對每個新增／修改的 `.py` 檔各叫一次**原封不動**的 `check_silence.py`

### 4.3 模擬測試（`codex-hook-matrix.txt`）

`run_codex_hook.py` 照 Codex 原始碼的方式：取 `commandWindows`、替換 `${CLAUDE_PLUGIN_ROOT}` 為快取路徑、`cmd.exe /C "<指令>"`，從 stdin 餵 Codex 格式的 PostToolUse JSON（`tool_name: apply_patch`、`tool_input.command` 放修補內容、`tool_response` 為字串）。「沒 Python」沿用卡 05 的做法（PATH 只留 System32 和模擬的 Microsoft Store 假 python）。

| 情況 | 結束碼 | 看到什麼 |
|---|---|---|
| 有 Python，修改 `src/bad.py` | **2** | `⚠️ 靜默失敗檢查：bad.py 的 第 4 行 有「廣泛捕捉例外後什麼都不做」。`（完整中文警告） |
| 有 Python，新增 `src/good.py` | 0 | 沒有輸出 |
| 有 Python，一次改多檔（新增 good.py、改 txt、刪 gone.py、old.py 改名成 bad.py） | **2** | 只對 bad.py 警告 |
| 有 Python，只改 `README.md` | 0 | 沒有輸出 |
| 有 Python，開對話 | 0 | 沒有輸出 |
| 沒 Python，改 bad.py／good.py | 0 | 沒有輸出（不吵） |
| 沒 Python，開對話 | 0 | 印出「這項沒啟用」的 JSON（`systemMessage`；Codex 文件：「Surfaced as a warning in the UI」） |

對照：同樣的 Codex 輸入**直接**餵給 `check_silence.py`，四種都是 `AttributeError: 'str' object has no attribute 'get'`、結束碼 1——這就是為什麼要轉接，而不是直接沿用。

### 4.4 Claude Code 行為沒有變

- `claude plugin validate dev-bingfa-check` → `√ Validation passed`（`claude-validate-check.txt`），清單一樣是 `SessionStart`、`PostToolUse Write|Edit` 兩個，`command` 原文不變。
- 用卡 05 的 `run_hook.py` 重跑 Claude 路線（`claude-hook-recheck.txt`），結果和卡 05 完全一樣：sh／PowerShell 兩條路，有 Python 時 bad=2、good=0、開對話=0；沒 Python 時全部 0（開對話印提示）。
- 在隔離的 `CLAUDE_CONFIG_DIR` 重新安裝：`dev-bingfa-check` → `Hooks (2) SessionStart, PostToolUse`。

### 4.5 真的在 Codex 裡觸發：未實測成功

- 只做了一次小心的嘗試：一般的 `codex exec`（沒有登入）。看到的 `hook: SessionStart`／`hook: UserPromptSubmit` 是公司管控的 hook（研究 01b 已查明），沒有證據是我們的 hook。
- 想加 `--dangerously-bypass-hook-trust`（跳過「信任」檢查）重試一次，被這台電腦的權限機制擋下，所以沒有做，也沒有找別的方法繞過。
- Codex 文件：外掛的 hook 要使用者在 `/hooks` 檢視並信任後才會跑，外掛更新後要重新信任。
- 所以標示：**Codex 存檔檢查「未實測成功」**。手動替代做法寫在 `dev-bingfa/codex/README.md` 第 4 節（交付前貼一句檢查要求）。

### 4.6 Mac／Linux 的 Codex：沒有轉接

非 Windows 時 Codex 用 `command`（兩用寫法 → `run.sh` → `check_silence.py`），收到 `apply_patch` 的輸入會找不到檔案；若 `tool_response` 是字串還會結束碼 1（Codex 會把它記成 hook 失敗，但不會中斷）。要修只有兩條路：改 `check_silence.py`（它和來源逐位元組相同，本卡不准動），或改 `run.sh`／`command`（會動到 Claude Code 路線）。**本卡沒有修，交給維護人決定。** README 已寫「Mac/Linux 的 Codex 裝了也抓不到」。

---

## 5. 對照表：Claude Code 版有的，Codex 版有沒有

| 項目 | Claude Code 版 | Codex 版 | 原因／手動替代做法 |
|---|---|---|---|
| 4 個 skill | 有 | **有**（實測：`prompt-input` 清單） | — |
| 助手：讀碼調查 | 有 | **有**，`bingfa-explorer`，手動複製到 `~/.codex/agents/`（實測：載入無警告） | 外掛帶不進 Codex 助手。派工未實測 |
| 助手：照計畫實作 | 有 | **有**，`bingfa-implementer`（同上） | 同上 |
| 助手：網路搜尋 | 有 | **有**，`bingfa-web-search-agent`（同上） | 策略檔讀外掛快取位置；讀取未實測 |
| `commit` | 有 | **有**（實測：清單裡有） | 叫用未實測 |
| 只能手動叫 | 有 | **有**（實測：加 `openai.yaml` 後從 AI 自動清單消失） | 手動叫得起來未實測；規則第 5 節是第二道防線 |
| 存檔檢查 | 有 | **未實測成功**（Windows 已轉接並模擬通過；Mac/Linux 沒有） | 要在 `/hooks` 信任；公司電腦上自訂 hook 沒看過真的執行。手動替代：交付前的檢查句 |
| 沒 Python 提示「這項沒啟用」 | 有 | **未實測**（Windows 模擬通過） | 提示文字寫「重開 Claude Code」，Codex 上請讀成重開 Codex |
| 通用規則 | 有 | **有**（實測：`~/.codex/AGENTS.md` 全文進入 AI 指示） | 手動複製 |
| Claude 專用附錄（助手名字） | 有 | **沒有** | Codex 上要自己點名 `bingfa-*` |

---

## 6. 換行符號（`.gitattributes`）

新增的規則：`*.sh` → LF；`*.cmd`、`*.bat` → CRLF；`*.py`、`*.json`、`*.toml`、`*.md` → text；`dev-bingfa/離線副本/mattpocock-skills/**` → `-text -eol`（不轉換，放最後蓋過前面）。

`git check-attr` 確認：`run.sh` = `text eol=lf`；`run.cmd`、`codex-post.cmd` = `text eol=crlf`；離線副本內 `README.md`、`LICENSE` = `text: unset`。

工作目錄的實際換行（`git ls-files --eol`）：

```
w/lf    attr/text eol=lf     dev-bingfa/外掛/dev-bingfa-check/hooks/run.sh        ← 正確
w/crlf  attr/text eol=crlf   dev-bingfa/外掛/dev-bingfa-check/hooks/run.cmd       ← 正確
w/crlf  attr/text eol=crlf   dev-bingfa/外掛/dev-bingfa-check/hooks/codex-post.cmd ← 正確
```

**發現一個問題（不在本卡可改的範圍，只回報）：** 離線副本 186 個檔在 Git 裡存的是 LF（`i/lf`），但工作目錄是 CRLF（`w/crlf`）。原因是這台電腦 `core.autocrlf=true`，clone 時把換行改掉了。對照：

```
上游 clone 的 Git 內容 LICENSE：0e7ac423bf2c6e22...（LF）
本 repo 已提交的 LICENSE：      0e7ac423bf2c6e22...（LF，和上游相同）
工作目錄的 LICENSE：            4981c5f6a90eb3a9...（CRLF）
```

所以：已提交的內容和上游逐位元組相同；但**工作目錄那份不是**，證據 08 第 2 節比對的兩個雜湊其實都是 CRLF 版。加了 `-text` 之後，Git 之後重新檢查這些檔時會把它們視為「已修改」（CRLF ≠ LF）；如果有人照工作目錄打包 zip，發出去的也是 CRLF 版。建議維護人在沒有其他改動時重新取出這個資料夾（例如 `git checkout -- "dev-bingfa/離線副本/mattpocock-skills"`），讓工作目錄回到 LF。我沒有做，因為那會改寫 `離線副本/`。

---

## 7. 沒有驗證的事（留給任務卡 12）

1. Codex 裡實際派出三個助手；網路搜尋助手真的讀到快取裡的策略檔。
2. 手動打 `$dev-bingfa:commit`（或 `/skills` 選）叫得起來；4 個 skill 的實際叫法與畫面。
3. 存檔檢查在 Codex 真的被觸發：在 `/hooks` 信任之後，Windows 上 `codex-post.cmd` 是否照模擬執行、警告是否餵回 AI；沒 Python 時「這項沒啟用」是否顯示。
4. 0.140.0 是否和 GitHub main 分支一樣用 cmd.exe、一樣替換 `${CLAUDE_PLUGIN_ROOT}`（我讀的是 main 分支原始碼）。
5. 真實 `apply_patch` 的 `tool_input`／`tool_response` 長相（我照文件與原始碼註解造的；轉接程式也接受 `tool_input.patch`，以防第三方說法才是對的）。
6. Mac／Linux 的 Codex（第 4.6 節，目前沒有轉接）。
7. 路徑含空白、使用者名稱含中文時 cmd.exe 的行為。
8. Codex 0.140.0 在 Windows 實際怎麼把 `commandWindows` 交給 `cmd.exe /C`（審查「沒能驗證」第 2 項）：如果它把指令當一般參數處理、用反斜線跳脫引號，`"…\run.cmd" session` 可能會壞。我們的測試程式都是直接組字串 `cmd.exe /C "<指令>"`，測不出這種情況。

## 8. 實驗副作用

- `codex debug prompt-input` 照研究 01b 的已知行為，仍會讀真實的 `~/.agents/skills`（唯讀）。
- `codex exec` 向 `api.openai.com` 發了未帶憑證的請求，全部 401；執行前清掉了 `OPENAI_API_KEY`、`CODEX_API_KEY`。
- 沙盒 `card06/codex-home` 多了 Codex 自己產生的檔案；`agents/web-search-modules/` 是測試用副本，留在沙盒。
- 搜尋了 `claude.exe` 執行檔裡的字串 `commandWindows`（唯讀）。

---

## 後續修正（2026-11-24，卡 05/06/07 之後）

原始輸出在 `.scratch/dev-bingfa/research/sandbox/card09/`：`run_matrix.py`、`matrix-repo.txt`、`matrix-space.txt`、`card05-rerun.txt`、`card06-rerun.txt`、`claude-validate.txt`、`check-package.txt`。

### 1. 存檔檢查：一個入口、兩種工具、每種系統

修掉第 4.6 節的問題（Mac/Linux 的 Codex 會讓 `check_silence.py` 當掉）。`check_silence.py` **沒動**（SHA-256 仍是 `ff5640ac…`，和 `~/.claude/hooks/check_silence.py` 相同，只讀比對）。

| 檔案 | 動作 |
|---|---|
| `hooks/post_check.py` | 新增（取代 `codex_post.py`，已刪除）。唯一的檢查入口：先看輸入是 Claude Code 的樣子（`tool_input.file_path`，或 `tool_response.filePath` 是物件時）還是 Codex `apply_patch`（`tool_input.command` 的修補內容），再把每個檔案用 Claude 的樣子交給 `check_silence.py`。只有真的抓到問題才回 2 並轉出警告；看不懂的輸入、壞掉的 JSON、自己或 `check_silence.py` 出錯，一律回 0、不輸出 |
| `hooks/run.sh` | `post` 改跑 `post_check.py`；結束碼只傳出 2，其他都變 0 |
| `hooks/run.cmd` | 同上（`errorlevel 2` 才回 2） |
| `hooks/codex-post.cmd` | 改成只做一件事：`call "%~dp0run.cmd" post`（不再自己找 Python）。CRLF |
| `hooks/hooks.json` | **沒改**（`command`、`commandWindows` 都一字未改） |
| `hooks/no-python.json` | 「再重開 Claude Code」→「再重新開啟對話」（兩個工具通用） |

測試矩陣（`run_matrix.py`）：四條路線 × 有／沒有 Python × 各種輸入。路線：`claude-sh`（Git Bash 跑 `command`）、`claude-ps`（PowerShell 跑 `command`）、`codex-cmd`（`cmd.exe /C` 跑 `commandWindows`）、`codex-sh`（用 Git Bash 的 sh 模擬 Mac/Linux 的 Codex 跑 `command`）。輸入：Claude 格式 bad/good、Codex 格式 bad/good/多檔/只改 README、壞掉的 JSON `{not json`、JSON 陣列 `[1, 2]`、`tool_input` 是 null 加字串 `tool_response`、空的輸入、開對話。

| 外掛放在哪 | 結果 |
|---|---|
| repo 原位置（路徑有中文、沒空白） | 72 格全部符合預期（`FAILURES: 0`） |
| `sandbox/路徑 測試/my plugin/dev-bingfa-check`，專案在 `sandbox/路徑 測試/proj 專案`（**有空白、有中文**） | 72 格全部符合預期（`FAILURES: 0`） |

符合預期＝有 Python 且有問題：結束碼 2、stderr 有「靜默失敗檢查」；其他情況：結束碼 0、沒有輸出（PowerShell 路線的 `#< CLIXML` 進度雜訊照卡 05 的說法排除不算）；開對話：有 Python 不輸出，沒 Python 印出「這項沒啟用」JSON。`codex-sh` 路線的 Codex bad 現在正確回 2（修之前是 `AttributeError`、結束碼 1）。沒有找到引號問題，所以沒有改引號。

舊測試重跑：卡 05 `run_hook.py`（sh／PowerShell × 有／沒 Python × bad/good/開對話）與卡 06 `run_codex_hook.py`（p-bad/p-good/p-mixed/p-txt/開對話 × 有／沒 Python）結果和原本完全一樣。`claude plugin validate dev-bingfa-check` → `✔ Validation passed`。

**仍未實測**：Codex／Claude Code 本身真的觸發這些 hook（要登入）；真的 Mac/Linux；Codex 0.140.0 是否真的照 main 分支原始碼用 `cmd.exe /C "<指令>"`。

### 2. 換行格式

`.gitattributes` 改成：`.sh` LF、`.cmd`/`.bat` CRLF，`.py`、`.json`、`.toml`、`.md`、`.yaml`、`.yml`、`.ps1`、`VERSION` 一律 `text eol=lf`（不管哪台電腦的 `core.autocrlf` 怎麼設，取出來都是 LF；照工作目錄打包 zip 結果固定）。離線副本仍是 `-text -eol`（放最後）。

工作目錄原本只有 5 個檔不是 LF：`外掛/dev-bingfa/web-search-modules/*.md`（CRLF，從 `~/.claude/agents/web-search-modules/` 照原樣複製來的）。已改成 LF；去掉 CR 之後和原檔內容逐位元組相同（只讀比對）。其餘 `dev-bingfa/` 底下的檔案本來就是 LF（`.cmd` 是 CRLF）。已提交的檔案本來就都是 `i/lf`，不需要重新正規化。離線副本另見證據 08「更正：換行格式」。

### 3. Codex 專用附錄

新增 `規則/CODEX專用附錄.md`；`規則/README.md`、`codex/README.md` 改成「`AGENTS.md` → `CODEX專用附錄.md` → 個人偏好」。`規則/AGENTS.md` 與 `CLAUDE.md` 沒動，SHA-256 都是 `82b5f14c…`。

更正一件事：Matt 的「只能手動叫」skill 在 Codex 上**大多有保護**——他的 repo 在這些 skill 裡附了 `agents/openai.yaml`（`allow_implicit_invocation: false`），證據 08 的 Codex 清單裡也看不到它們。沒有這個檔的只有 `in-progress/software-factory`，它就出現在 AI 自動清單裡；Codex 還會載入 Matt 清單以外的 `misc/`、`in-progress/` skill。所以附錄寫的是「規則文字才是防線」，沒有寫「全部沒保護」。

### 4. 維護工具

- `tools/sync-basic.ps1`：本來就整個資料夾複製；加上 `-Force`（隱藏檔也算）。重跑：新增 `基本版/.agents/skills/commit/agents/openai.yaml`，`PASS: all 6 file(s) equal to master.`
- 新增 `tools/check-package.ps1`（全 ASCII、PowerShell 5.1）。結束碼：0 全過、1 有失敗、2 沒失敗但有跳過。故意弄壞一份複本（改 run.sh 換行、改 check_silence.py、改 toml 一行、改 CLAUDE.md、改 VERSION）→ 5 項 FAIL、exit 1；拿掉 Python 的 PATH → `agent-twin SKIPPED`、exit 2。從 Git Bash 執行時要加 `</dev/null`，否則會卡住等輸入（PowerShell 直接執行沒問題）。

目前輸出：

```
Check         Result Detail
-----         ------ ------
basic-sync    PASS   PASS: all 6 file(s) equal to master.
rules-twin    PASS   AGENTS.md == CLAUDE.md 82B5F14C684D
agent-twin    PASS   explorer ok(0 allowed), implementer ok(0 allowed), web-search-agent ok(2 allowed)
check-silence PASS   sha256 FF5640ACBCF5 == recorded
version       PASS   VERSION 1.0 -> both plugin.json 1.0.0
line-endings  PASS   3 file(s): .sh LF, .cmd CRLF
PASS: all 6 check(s) passed.
```

---

## 審查後修正（2026-11-24，依 `審查-05-06-07.md`）

原始輸出：`.scratch/dev-bingfa/research/sandbox/review-050607/fix/`。

| 審查項目 | 修了什麼 |
|---|---|
| S2 一次修補很多檔案會超過 10 秒 | `post_check.py` 先篩選：只留存在的 `.py`、不是測試檔（判準直接取用 `check_silence.py` 的 `_EXTS`、`_TEST_FILE`）。再把 `check_silence.py` 當模組載入，在**同一個程序**裡逐檔呼叫它的 `main()`（呼叫前暫時換掉 `sys.stdin`／`sys.stderr`，不寫 `__pycache__`）。`check_silence.py` 一個位元組都沒改；警告文字、結束碼和以前每檔開一個程序時一樣（一個檔案出錯只略過那一個） |
| S3 備案搜尋樣式 | `bingfa-web-search-agent.toml` 的備案改成在 `<Codex home>/plugins/cache/` 底下找 `**/web-search-modules/*.md`；Claude 版同步改（證據 05） |
| S4 `check-package.ps1` 守太少 | 從 6 項加到 13 項，見下表 |
| Nit 6 寫死 `1.0.0` | `codex/README.md` 第 2 節兩處改成 `<版本>/`（例如 `1.0.0`） |
| Nit 7 「most likely」 | `規則/CLAUDE專用附錄.md` 改成「`claude plugin validate` 列出的名字是 `dev-bingfa:explorer`、`dev-bingfa:implementer`、`dev-bingfa:web-search-agent`；如果 `/agents` 顯示的不一樣，以 `/agents` 為準」。`規則/AGENTS.md`、`CLAUDE.md` 沒動（仍是 `82B5F14C…`） |

### 300 個檔案的修補要跑多久（`codex-cmd` 路線，`tools/test-hooks.py`）

| 修補內容 | 修改前 | 修改後 |
|---|---|---|
| 300 個 `.md` | 12.13 秒（超過 10 秒逾時） | 0.13 秒，結束碼 0 |
| 300 個 `.py` + 1 個有問題的 `.py` | 12.11 秒 | 0.16 秒，結束碼 2、有警告 |

### `tools/check-package.ps1`（13 項，PowerShell 5.1，全 ASCII）

新增的檢查：`agent-files`（剛好 3 個 Claude 助手、3 個 Codex 助手，資料夾裡沒有別的檔）、`agent-twin` 改成**整行**比對（允許不同的那兩組行記成 SHA-256，改到一個字就會 FAIL，並印出新的雜湊方便更新；TOML 只能有 name／description／developer_instructions，Claude 助手的 frontmatter 只能有 name／description）、`json`（`dev-bingfa/` 底下所有 `.json` 都能剖析，不含 Matt 副本）、`hooks-json`（事件、matcher、timeout 10、`command` 叫對 `run.sh`／`run.cmd`、`commandWindows` 一字不差）、`marketplace`（兩個外掛的 `source` 都對得到 `plugin.json` 而且名字相同）、`commit-manual`（`disable-model-invocation: true` 與 `openai.yaml` 的 `allow_implicit_invocation: false`）、`search-modules`（5 個策略檔都在、不是空的、第一行是標題）、`hook-matrix`（呼叫 `tools/test-hooks.py`；沒有 Python 3.8 以上或找不到 Git 的 sh 時是 SKIPPED、結束碼 2，不會假裝通過）。比對助手的 Python 部分放在 `tools/check-agents.py`（從 stdin 讀清單）。

修改後第一次完整執行：

```
Check          Result Detail
-----          ------ ------
basic-sync     PASS   PASS: all 6 file(s) equal to master.
rules-twin     PASS   AGENTS.md == CLAUDE.md 82B5F14C684D
agent-files    PASS   3 Claude .md + 3 Codex .toml, nothing else
agent-twin     PASS   explorer ok(0 allowed), implementer ok(0 allowed), web-search-agent ok(2 allowed)
check-silence  PASS   sha256 FF5640ACBCF5 == recorded
version        PASS   VERSION 1.0 -> both plugin.json 1.0.0
line-endings   PASS   3 file(s): .sh LF, .cmd CRLF
json           PASS   5 file(s) parse
hooks-json     PASS   SessionStart + PostToolUse(Write|Edit), timeout 10, commands as expected
marketplace    PASS   sources resolve: dev-bingfa, dev-bingfa-check
commit-manual  PASS   disable-model-invocation: true + openai.yaml allow_implicit_invocation: false
search-modules PASS   5 module(s), each with a heading
hook-matrix    PASS   98 cases, 0 failed; 300-file patch: 300.md=0.12s, 300.py=0.14s
PASS: all 13 check(s) passed.
```

### 重跑審查的 11 種故意弄壞（`mutate.ps1`，每次一份新複本，沒動真正的資料夾）

| 弄壞 | 結果 |
|---|---|
| M1 Codex 搜尋助手那一行刪掉 `CODEX_HOME`／`<version>` 說明 | **抓到**：`agent-twin` allowed line 對不到、1 行不同 |
| M2 TOML 多 `model`、`sandbox_mode` | **抓到**：`agent-twin` TOML 欄位不對 |
| M3 Claude 助手多 `tools`、`permissionMode` | **抓到**：`agent-twin` frontmatter 欄位不對 |
| M4 matcher 打錯、timeout 改 1 | **抓到**：`hooks-json` |
| M5 `post_check.py` 永遠回 0 | **抓到**：`hook-matrix` 98 格中 22 格失敗 |
| M11 多一個 `rogue.toml` | **抓到**：`agent-files`（直接對那份複本跑） |
| M6 `run.cmd` 變成 LF | 這次的執行被防毒擋下（見下段），沒拿到結果；`line-endings` 的程式和修改前一樣，修改前就抓得到 |
| M7 壞掉的 JSON、M8 `source` 改錯、M9 刪掉 `openai.yaml`、M10 清空策略檔 | **沒拿到結果**：被防毒擋下。對應的檢查（`json`、`marketplace`、`commit-manual`、`search-modules`）在真正的資料夾上跑過、都是 PASS，但「弄壞時會 FAIL」這半段沒有實測 |

確定抓到 6／11；M6 靠沒改過的舊檢查（修改前已證明抓得到）；M7–M10 未驗證。

### 防毒擋下 `check-package.ps1`（**需要維護人處理**）

修改後的 `check-package.ps1` 前幾次都正常跑完（上面的 13 項表、M1–M5、M11 都是那時候拿到的）。之後不管在沙盒複本還是 repo 裡的那份，PowerShell 都回：`This script contains malicious content and has been blocked by your antivirus software.`（`ScriptContainedMaliciousContent`，擋在第 1 行，還沒開始跑）。同資料夾的 `sync-basic.ps1` 照常能跑。我試過一次把「寫暫存 .py 檔再執行」改成正式檔案 `tools/check-agents.py`（從 stdin 傳清單），雜湊變了還是被擋。（注意：上面的 13 項表是改成 `check-agents.py` **之前**那一版跑出來的；現在這一版的 PowerShell 部分因為被擋，還沒完整跑過。`check-agents.py` 單獨用 Python 跑過：`PASS|explorer ok(0 allowed), implementer ok(0 allowed), web-search-agent ok(2 allowed)`。）`Get-MpThreatDetection` 沒有任何紀錄，可能不是 Defender，是公司另外裝的防毒。為了不在公司電腦上一直觸發防毒警報，我沒有再試別的寫法。

這代表：在這台電腦上 `check-package.ps1` 目前**跑不起來**（會顯示上面那句錯誤，結束碼 1，不會假裝通過）。`python tools\test-hooks.py` 和 `tools\sync-basic.ps1` 可以單獨跑。要請維護人決定：向 IT 申請把這支列為誤判，或改寫成別的形式（例如整支改成 Python）。

### 其他

- 加到第 7 節：Codex 0.140.0 怎麼把 `commandWindows` 交給 `cmd.exe /C`（第 8 項），留給任務卡 12。
- 審查說的「`bash -n` 0 錯誤」對整段指令不成立（修改前也一樣），見證據 05「審查後修正」Nit 4；不影響實際執行。

---

## 檢查工具改寫為 Python（2026-11-24）

### 為什麼

`tools/check-package.ps1` 在這台公司電腦上被防毒軟體當成惡意程式擋下（`ScriptContainedMaliciousContent`，誤判）。我們不去繞過防毒（不改寫來躲、不加例外、不改設定、不重複觸發），改成一支普通的 Python 程式。

### 改了什麼

- 新增 `tools/check_package.py`：Python 3.8 以上、只用標準程式庫，13 項檢查和舊版相同，全部直接用 Python 做。「基本版和母本相同」那一項自己算 SHA-256 比對，不再呼叫 `sync-basic.ps1`；比對助手的邏輯（原本在 `check-agents.py`）也併進來了。加了 `--root <資料夾>`，可以拿去檢查一份複本。結束碼不變：0 全過、1 有失敗、2 沒失敗但有跳過（不會假裝通過）。
- 比舊版稍微嚴一點的地方：`.json`、助手檔一律用嚴格 UTF-8 讀（有 BOM 或壞字元算失敗）；`openai.yaml` 的 `allow_implicit_invocation: false` 要在 `policy:` 底下；`agents/`、`web-search-modules/` 資料夾裡多出子資料夾也算多餘。
- 刪掉 `tools/check-package.ps1`。`tools/sync-basic.ps1` 沒動。
- 新增 `tools/README.md`（每個工具做什麼、打包前跑 `python tools/check_package.py`、為什麼拿掉 PowerShell 版）。
- `tools/check-agents.py` **還在**：內容已併進 `check_package.py`，沒有人再呼叫它；要刪掉時系統沒有給刪除權限，留給維護人決定。
- Python 跑這些檔案時，防毒沒有擋。

### 在真正的資料夾上執行（`python tools/check_package.py`）

```
Check           Result   Detail
-----           ------   ------
basic-sync      PASS     all 6 file(s) equal to master
rules-twin      PASS     AGENTS.md == CLAUDE.md 82B5F14C684D
agent-files     PASS     3 Claude .md + 3 Codex .toml, nothing else
agent-twin      PASS     explorer ok(0 allowed), implementer ok(0 allowed), web-search-agent ok(2 allowed)
check-silence   PASS     sha256 FF5640ACBCF5 == recorded
version         PASS     VERSION 1.0 -> both plugin.json 1.0.0
line-endings    PASS     3 file(s): .sh LF, .cmd CRLF
json            PASS     5 file(s) parse
hooks-json      PASS     SessionStart + PostToolUse(Write|Edit), timeout 10, commands as expected
marketplace     PASS     sources resolve: dev-bingfa, dev-bingfa-check
commit-manual   PASS     disable-model-invocation: true + openai.yaml allow_implicit_invocation: false
search-modules  PASS     5 module(s), each with a heading
hook-matrix     PASS     98 cases, 0 failed; 300-file patch: 300.md=0.11s, 300.py=0.15s
PASS: all 13 check(s) passed.
```

結束碼 0，約 25 秒（大部分是 `hook-matrix`）。

### 11 種故意弄壞，重跑（`.scratch/dev-bingfa/research/sandbox/mutations/mutate.py`）

把審查的 `mutate.ps1` 改寫成 Python。每一種都先把 `dev-bingfa/`（不含 `離線副本`）和 `tools/` 複製到沙盒，只改複本，再跑 `check_package.py --root <複本>`；真正的資料夾只讀不改。另外先跑一次沒改過的複本當對照組（M0），確認複製方法本身會通過。原始輸出：`mutations/mutate-out.txt`。

| 弄壞 | 結果 | 哪一項 FAIL |
|---|---|---|
| M0 對照組：沒改的複本 | 通過（exit 0） | 無 |
| M1 Codex 搜尋助手刪掉 `CODEX_HOME`／`<version>` 說明 | **抓到** | `agent-twin` |
| M2 TOML 多 `sandbox_mode`、`model` | **抓到** | `agent-twin` |
| M3 Claude 助手多 `tools`、`permissionMode` | **抓到** | `agent-twin` |
| M4 matcher 打錯、timeout 改 1 | **抓到** | `hooks-json` |
| M5 `post_check.py` 永遠回 0 | **抓到** | `hook-matrix` |
| M6 `run.cmd` 從 CRLF 變 LF | **抓到** | `line-endings` |
| M7 `no-python.json` 壞掉 | **抓到** | `json`、`hook-matrix` |
| M8 marketplace 的 `source` 改錯 | **抓到** | `marketplace` |
| M9 母本和基本版都刪掉 `openai.yaml` | **抓到** | `commit-manual` |
| M10 清空一個策略檔 | **抓到** | `search-modules` |
| M11 多一個 `rogue.toml` | **抓到** | `agent-files` |

**11／11 抓到**，每一種都是由預期的那一項抓到。上一段 M6–M10「沒拿到結果」的缺口，這次補齊了。