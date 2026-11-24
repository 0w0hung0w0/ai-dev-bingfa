# Codex 版：這個資料夾放什麼、東西要放到哪裡

這裡只放 **Codex 才需要、外掛帶不進去** 的東西。skill、提交指令、存檔檢查都和 Claude Code 共用 `外掛/` 那一份，不在這裡。

測試環境：`codex-cli 0.140.0`，Windows 10，隔離設定、沒有登入。下面寫「未實測」的地方，是要登入開對話才看得到的，留給任務卡 12 在乾淨電腦上確認。

## 1. 這個資料夾裡有什麼

| 檔案 | 是什麼 | 要放到哪裡 |
|---|---|---|
| `agents/bingfa-explorer.toml` | 讀碼調查助手 | 複製到 `~/.codex/agents/` |
| `agents/bingfa-implementer.toml` | 照計畫實作助手 | 複製到 `~/.codex/agents/` |
| `agents/bingfa-web-search-agent.toml` | 網路搜尋助手 | 複製到 `~/.codex/agents/` |

`~` 是你的使用者資料夾（Windows 通常是 `C:\Users\你的帳號`），所以 `~/.codex/agents/` 在 Windows 就是 `C:\Users\你的帳號\.codex\agents\`。資料夾不存在就自己建一個。如果你有設定 `CODEX_HOME` 環境變數，就改放到那個資料夾底下的 `agents\`。

名字前面都加了 `bingfa-`：Codex 內建一個叫 `explorer` 的助手，同名會把內建的蓋掉，所以三個都加前綴，叫法一致。內容和 Claude Code 版逐行相同，只有網路搜尋助手的「搜尋策略檔在哪裡」那一段改成 Codex 的位置。

## 2. 其他東西放哪裡（Codex 完整版的全部安裝位置）

| 東西 | 怎麼裝 | 放在哪裡 |
|---|---|---|
| 4 個 skill（含 `commit`） | `codex plugin marketplace add "<包裹>\外掛"`，再 `codex plugin add dev-bingfa@dev-bingfa` | Codex 自己複製到 `~/.codex/plugins/cache/dev-bingfa/dev-bingfa/<版本>/`（例如 `1.0.0`） |
| 網路搜尋的 5 個策略檔 | 跟著上一行一起裝好，不用另外動 | 同上資料夾裡的 `web-search-modules/`（網路搜尋助手會自己去那裡讀） |
| 3 個助手 | 手動複製（見第 1 節） | `~/.codex/agents/` |
| 存檔檢查（選用） | `codex plugin add dev-bingfa-check@dev-bingfa`，第一次開 Codex 時在 `/hooks` 按「信任」 | `~/.codex/plugins/cache/dev-bingfa/dev-bingfa-check/<版本>/`（例如 `1.0.0`） |
| 通用規則 | 把 `規則/AGENTS.md` 複製成 `~/.codex/AGENTS.md`（整台電腦都套用） | `~/.codex/AGENTS.md` |
| Codex 專用附錄 | 把 `規則/CODEX專用附錄.md` 的內容貼在 `~/.codex/AGENTS.md` 通用規則的後面 | 同上 |
| 個人偏好 | 照 `規則/個人偏好範例.md` 的說明，貼在 `~/.codex/AGENTS.md` 最後面（附錄之後） | 同上 |

規則也可以只放在某個專案：把 `AGENTS.md` 放在專案最上層資料夾。Codex 會先讀 `~/.codex/AGENTS.md`，再讀專案的 `AGENTS.md`（專案的排在後面，等於優先）。全部規則檔加起來不能超過 32 KiB（通用規則本身約 8.5 KB）。`規則/CLAUDE專用附錄.md` 不要貼給 Codex；Codex 用的是 `規則/CODEX專用附錄.md`。

## 3. 在 Codex 裡怎麼用

- **skill**：Codex 清單上的名字是 `dev-bingfa:brownfield-recon`、`dev-bingfa:blast-radius`、`dev-bingfa:seam-audit`、`dev-bingfa:commit`。在對話框打 `$` 會跳出 skill 清單可以選，或打 `/skills` 選。前三個 AI 也會在合適時自己用。
- **提交**：只能你自己叫——打 `$` 選 `dev-bingfa:commit`（或 `/skills` 選）。AI 不會自己決定提交（見第 4 節）。
- **助手**：Codex 不會自己派助手，要你在對話裡點名，例如「請派 bingfa-explorer 查清楚登入失敗的原因」。`/subagents` 可以切換查看正在工作的助手。
- 以上「打 `$` 選」「點名派助手」都是官方文件的用法，**本機沒登入所以未實測**。

## 4. 對照表：Claude Code 版有的，Codex 版有沒有

| 項目 | Claude Code 版 | Codex 版 | 原因／手動替代做法 |
|---|---|---|---|
| 4 個 skill | 有 | **有**（實測：清單裡看得到） | — |
| 助手：讀碼調查 | 有（`dev-bingfa:explorer`） | **有**（`bingfa-explorer`，要手動複製；實測：Codex 讀得到、沒有報錯） | 外掛帶不進 Codex 的助手，所以要複製檔案。實際派工未實測 |
| 助手：照計畫實作 | 有（`dev-bingfa:implementer`） | **有**（`bingfa-implementer`，同上） | 同上 |
| 助手：網路搜尋 | 有（`dev-bingfa:web-search-agent`） | **有**（`bingfa-web-search-agent`，同上） | 同上。搜尋策略檔改讀外掛安裝位置；找不到時助手會說出來 |
| 提交 `commit` | 有，只能手動叫 | **有**，只能手動叫 | 見下一列 |
| 「只能手動叫」的保護 | 有（`SKILL.md` 的 `disable-model-invocation: true`） | **有**（`skills/commit/agents/openai.yaml` 的 `allow_implicit_invocation: false`；實測：加了之後 `commit` 從 AI 看得到的自動清單消失） | 「你手動叫還叫得起來」是官方文件說的，未實測。萬一失效，規則檔第 5 節「提交只能由使用者叫」仍是第二道防線 |
| 存檔自動檢查（選用） | 有（已模擬測試） | **未實測成功**（Windows 與 Mac/Linux 的執行方式都只在這台 Windows 電腦上模擬過） | Codex 的 hook 要你在 `/hooks` 手動信任才會跑；這台公司電腦上自訂 hook 從沒看到真的執行過。**手動替代**：交付前自己問 AI 一句（見下方） |
| 沒有 Python 時提示「這項沒啟用」 | 有 | **未實測**（Windows 上指令已接好） | 提示文字寫「再重新開啟對話」，兩個工具通用 |
| 通用規則 | 有（`~/.claude/CLAUDE.md`） | **有**（`~/.codex/AGENTS.md`；實測：Codex 讀進去了） | 外掛帶不進規則檔，要手動複製 |
| 工具專用附錄（助手名字對照） | 有（`規則/CLAUDE專用附錄.md`） | **有**（`規則/CODEX專用附錄.md`） | 貼在 `~/.codex/AGENTS.md` 通用規則後面。附錄裡寫「未實測」的叫法，同樣要登入才看得到 |

### 存檔檢查的手動替代做法（Codex 上沒有確定會自動跑，就每次交付前貼這句）

> 交付前請檢查：這次改過的 Python 檔裡，有沒有「`except Exception:` 或 `except:` 後面只有 `pass`」的地方？每一處請回答：上游怎麼知道這一步失敗了？使用者在哪裡看得到（寫進 log 不算）？答不出來就改成至少留下痕跡，或縮小成具體的例外型別；確定該吞掉的，在程式碼註解寫明理由。
