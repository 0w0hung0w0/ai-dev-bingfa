# 02 — 桌面 App 安裝路線（Codex 桌面 App／Claude 桌面 App）

- 調查日期：2026-11-24，Windows 10 Pro 10.0.19045
- 性質：唯讀調查。沒有改動 `~/.codex`、`~/.claude`、`~/.agents`、`C:\ProgramData\OpenAI`；沒有登入、沒有安裝、沒有打開桌面 App 操作。
- 標記：**文件** = 官方文件原文引用；**實測** = 本機指令輸出；**推論／未確認** = 沒有文件原文也沒有實測。
- 重要前提：**本報告沒有任何一步是在桌面 App 畫面上實際點過的**。所有「App 裡怎麼點」都只到「文件」等級。

## 先講結論

1. Codex 桌面 App 在 Windows 上存在，但**現在的正式名稱是「ChatGPT desktop app」**（Codex 是裡面的一個模式）。它和 CLI 共用 `%USERPROFILE%\.codex`。**裝 App 不會給你 `codex` 指令**（本機實測：PATH 上的 `codex` 來自獨立安裝程式與 npm，不是 App）。
2. 官方文件**沒有**寫 App 裡有「加入本機資料夾 marketplace」的按鈕。文件寫的本機路線有三條：(a) 把 `marketplace.json` 放在 App 會自動讀的固定位置後重啟 App；(b) 用 CLI `codex plugin marketplace add <path>`；(c) `codex://plugins/<plugin-name>?marketplacePath=<絕對路徑>` 深層連結。加進來之後，在 App 的 **Plugins** 分頁選該 marketplace、按「+」安裝。
3. 對非工程師最穩的路線見第 6 節；其中「App 會不會認我們 `外掛/.claude-plugin/marketplace.json` 這個位置」是**最大的未驗證點**。

---

## 1. App 是否存在、是否共用 `~/.codex`、`codex` 指令從哪來

### 1.1 存在與名稱

- **文件**（https://learn.chatgpt.com/docs/windows/windows-app ，由 https://developers.openai.com/codex/app/windows 308 轉址而來）：
  > "The Windows app supports core workflows such as worktrees, scheduled tasks, Git functionality, the built-in browser, file previews, plugins, and skills. It runs natively on Windows using PowerShell and the Windows sandbox, or you can configure it to run in Windows Subsystem for Linux 2 (WSL2)."

  安裝方式：Microsoft Store 連結，或
  > `winget install --id 9PLM9XGG6VKS -s msstore`
- **實測**：本機已裝，套件名 `OpenAI.Codex`，版本 `26.1013.4894.0`，但 AppxManifest 的 DisplayName 是 **`ChatGPT`**。安裝位置 `C:\Program Files\WindowsApps\OpenAI.Codex_26.1013.4894.0_x64__2p2nqsd0c76g0`。
- 注意：`developers.openai.com/codex/...` 的頁面現在大多 308 轉到 `learn.chatgpt.com/docs/...`，文件裡一律稱「ChatGPT desktop app」「Codex in the ChatGPT desktop app」。寫給同事的說明要用「ChatGPT 桌面 App 裡的 Codex」，否則他們會找不到。

### 1.2 是否共用 `~/.codex`

- **文件**（同上頁）：
  > "The Windows app uses the same Codex home directory as native Codex on Windows: `%USERPROFILE%\.codex`."
- 各項目的文件依據：
  - plugins：**文件**（https://developers.openai.com/plugins/build/plugins ）"ChatGPT installs plugins into `~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`."、"The plugin browser saves user-level choices in `~/.codex/config.toml`"、"These settings apply to local-marketplace plugins in supported local clients, including Codex CLI and Codex in the ChatGPT desktop app."
  - hooks：**文件**（https://learn.chatgpt.com/docs/hooks ）使用者層 `%USERPROFILE%\.codex\hooks.json`。
  - agents：**文件**（https://learn.chatgpt.com/docs/agent-configuration/subagents ）"add standalone TOML files under `~/.codex/agents/` for personal agents"，且 "In local Codex clients, you can also define custom agents"。
  - AGENTS.md：見第 4 節。
  - skills：**文件**（https://learn.chatgpt.com/docs/build-skills ）使用者層是 **`$HOME/.agents/skills`**，不是 `~/.codex/skills`（文件沒有提 `~/.codex/skills`）。
- 例外：若 App 的 agent 被切到 WSL，就改用 Linux 家目錄，不共用（**文件**："If you also run the Codex CLI inside WSL, the CLI uses the Linux home directory by default, so it doesn't automatically share configuration, cached auth, or session history with the Windows app."）。

### 1.3 裝 App 會不會有 `codex` 指令

- **文件**：Windows App 頁沒有說 App 會安裝 CLI。CLI 是另外的安裝方式（https://learn.chatgpt.com/docs/cli ）：
  > `powershell -ExecutionPolicy ByPass -c "irm https://chatgpt.com/codex/install.ps1 | iex"`
  > `npm install -g @openai/codex`
- **實測**（本機 `Get-Command codex -All`、`where.exe codex`）：
  1. `C:\Users\nick.ch.wei\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` — 這是連結，指向 `C:\Users\nick.ch.wei\.codex\packages\standalone\releases\0.140.0-x86_64-pc-windows-msvc\bin\codex.exe`，也就是**獨立安裝程式**裝的（2026/6/16）。PATH 上排第一，實際執行的是它。
  2. `C:\Users\nick.ch.wei\AppData\Roaming\npm\codex(.cmd/.ps1)` — **npm 全域** `@openai/codex@0.140.0`。
  3. 兩者 `--version` 都是 `codex-cli 0.140.0`。
- **實測**：App 套件自己帶一份 `app\resources\codex.exe`（341 MB），但**不在 PATH 上**；App 註冊的執行別名只有 `codex-chrome-native-host.exe`、`codex-core-command-runner.exe`，沒有 `codex.exe`。直接執行套件內那份回 `Access is denied`，所以**App 內建引擎的版本號查不到**。
- **推論**：只裝 App 的同事，開 PowerShell 打 `codex` 會找不到指令。App（2026-10 版）內建的引擎比我們驗證用的 CLI 0.140.0（2026-06）新約四個月，行為可能有差。App 的整合終端機裡有沒有 `codex` 可用：**未確認**。

---

## 2. 在 App 裡怎麼加本機 marketplace、怎麼裝外掛

### 2.1 有沒有外掛介面

- **文件**（https://learn.chatgpt.com/docs/plugins ）：
  > "On the web or in the ChatGPT desktop app, open the **Plugins** tab to browse and install plugins."
  > "The Plugins Directory organizes plugins into tabs: **OpenAI** … **Your workspace name** … **Personal:** personal marketplace plugins, including **Created by me** and **Shared with me** sections … Use the separate **Installed** row to review plugins you already installed."

  安裝步驟："Search or browse for a plugin, then open its details." → "Select the plus button to install the plugin." → "After installation, start a new chat and ask ChatGPT or Codex to use the plugin."

### 2.2 介面收不收本機路徑

- **文件沒有寫** App 裡有「輸入本機資料夾路徑來加 marketplace」的按鈕或欄位。→ **未確認**（可能有，文件沒寫）。
- **文件**寫的是「App 自動讀固定位置」（https://developers.openai.com/plugins/build/plugins ，"How local marketplaces work"）：
  > "The ChatGPT desktop app can read marketplace files from:
  > - a repo marketplace at `$REPO_ROOT/.agents/plugins/marketplace.json`
  > - a legacy-compatible marketplace at `$REPO_ROOT/.claude-plugin/marketplace.json`
  > - a personal marketplace at `~/.agents/plugins/marketplace.json`"

  以及：
  > "In Work mode or Codex in the ChatGPT desktop app, each marketplace appears as a selectable source in the Plugins Directory. … Then restart the ChatGPT desktop app. After that, open the Plugins Directory, choose your marketplace, and browse or install the plugins in that curated list."
- 對我們的影響：我們的檔案是 `外掛/.claude-plugin/marketplace.json`。依文件，它只在 `外掛/` 被當成 **`$REPO_ROOT`**（專案根目錄）時才算「legacy-compatible」位置。「把 `外掛/` 資料夾用 App 開成專案就會出現」是**推論，未確認**（也不確定是否需要它是 Git 倉庫）。個人層位置 `~/.agents/plugins/marketplace.json` 只列了 `.agents/plugins/` 這個格式，沒有列 `.claude-plugin/`。

### 2.3 CLI 加的 marketplace，App 看不看得到

- **文件**（同頁 "Add a marketplace from the CLI"）：
  > "Use `codex plugin marketplace add` to add and track a marketplace source instead of editing `config.toml` by hand. These commands support plugin authoring and catalog setup. Use the ChatGPT desktop app to install and test a local plugin."
  > `codex plugin marketplace add ./local-marketplace-root`
- **實測**：本機 `codex plugin marketplace --help` 有 `add`（"Add a local or Git marketplace to the configured marketplace sources"）、`list`、`upgrade`、`remove`；`codex plugin --help` 有 `add`、`list`、`remove`。
- **推論（強）**：CLI 把來源寫進共用的 `~/.codex/config.toml`，文件又明說「用 CLI 加來源、用桌面 App 安裝測試」，所以 CLI 加的 marketplace 與 CLI 裝的外掛**應該**會在 App 出現（要重啟 App）。但**沒有實際開 App 確認**。

### 2.4 深層連結（文件有寫，值得試）

- **文件**（https://learn.chatgpt.com/docs/app/commands ，"Deep links"）：
  > "`codex://plugins/<plugin-name>?marketplacePath=<absolute-marketplace-path>` — A local plugin detail page from a local marketplace."
  > "`marketplacePath=<absolute-marketplace-path>` — Required — Absolute path to the local `marketplace.json`, for example `/Users/alex/.agents/plugins/marketplace.json`."
  > "`codex://plugins/install/<plugin-name>?marketplace=<marketplace-name>` — The install flow for a plugin from a known marketplace."
- **未確認**：Windows 路徑怎麼編碼、是否接受 `.claude-plugin/marketplace.json`、路徑含中文（`外掛`）是否可用。文件只給了 macOS 範例。

### 2.5 外掛本身的格式風險

- **文件**（同 build 頁）："A portable plugin has a `plugin.json` manifest at its root. … A separate `.codex-plugin/plugin.json` is optional and serves as a compatibility fallback" 以及 "OpenAI also accepts legacy and Claude-compatible manifests, but new packages should use this format."
- 我們的外掛只有 `.claude-plugin/plugin.json`（先前在 CLI 0.140.0 驗過可裝）。文件說「接受」Claude 相容格式，但**在 2026-10 版 App 上沒有實測過**。

---

## 3. App 裡：技能、子代理、hooks、看已安裝項目

### 3.1 技能怎麼叫

- **文件**（https://learn.chatgpt.com/docs/reference/slash-commands ，App 的斜線指令頁）：
  > "You can also explicitly invoke skills by typing `$` in the chat composer."
  > "Enabled skills also appear in the slash command list."
- **文件**（https://learn.chatgpt.com/docs/skills-and-plugins ）："ChatGPT supports `@` mentions, while Codex supports `$` mentions for skills."
- **文件**（https://learn.chatgpt.com/docs/plugins ，App 分頁）："Type `@` to invoke the plugin or one of its bundled skills explicitly."
- **文件**（https://learn.chatgpt.com/docs/build-skills ）："In ChatGPT, type `@` to select a skill. In Codex CLI or the IDE extension, run `/skills` or type `$` to mention a skill."、"In the ChatGPT desktop app, open **Skills** in the sidebar to view and explore skills"。
- 小結：App 的 Codex 模式打 `$` 選技能、打 `/` 清單裡也會列出已啟用技能；`@` 是選外掛或其技能。`/skills` 指令文件只寫 CLI／IDE，App 的斜線指令表裡**沒有** `/skills`、`/hooks`、`/plugins`、`/subagents`。外掛技能在 `$` 清單裡顯示的確切名稱（有沒有 `外掛名:` 前綴）：**未確認**。
- 生效時機：**文件** "Bundled skills become available when you start a new chat or CLI session after installation."

### 3.2 自訂子代理（`~/.codex/agents/*.toml`）

- **文件**（https://learn.chatgpt.com/docs/agent-configuration/subagents ）：
  > "Subagent activity appears in the ChatGPT desktop app, Codex CLI, and the IDE extension."
  > App："Ask Codex in an app chat to delegate independent parts of the work to subagents." "The app surfaces each subagent thread so you can inspect its work and the summary returned to the main chat."
  > 必填欄位：`name`、`description`、`developer_instructions`；"Codex identifies the custom agent by its `name` field."
- 用法：在對話裡直接用文字要求（例如點名代理名稱請它分工）。App 沒有文件記載的「代理選單」；有唯讀的 **Subagents** 面板看 Active／Done。App 裡**列出已安裝的自訂代理定義**的介面：文件沒寫，**未確認**。
- **實測**：本機 CLI 0.140.0 `codex features list` 顯示 `multi_agent  stable  true`。

### 3.3 hooks

- **文件**（https://developers.openai.com/plugins/build/plugins ）：
  > "Lifecycle hooks are supported for plugins installed manually in Codex desktop."
  > "Installing or enabling a plugin doesn't automatically trust its hooks. Plugin-bundled hooks are non-managed hooks, so Codex skips them until the user reviews and trusts the current hook definition."
  > "Codex discovers `hooks/hooks.json` by default …"；"also sets `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility with existing plugin hooks."
- 信任方式，**文件**（https://learn.chatgpt.com/docs/hooks ）：
  > "In the CLI, open `/hooks`. In the desktop app, select **Review hooks** in the composer or open **Settings > Hooks**."
  > "Codex records trust against the hook's current hash, so new or changed hooks are marked for review and skipped until trusted."
  > "Hooks are enabled by default."
- `systemMessage`：**文件** "Surfaced as a warning in the UI or event stream"；SessionStart 的純文字 stdout "is added as extra developer context"。在 App 畫面上實際長什麼樣：**未確認**。
- **實測**：CLI 0.140.0 `codex features list`：`hooks  stable  true`；`plugin_hooks  removed  false`（這個旗標在 0.140.0 標為「已移除」，意義不明——**未確認**是否代表 0.140.0 的外掛 hooks 行為與現行文件不同）。
- 對同事的意義：**裝完外掛後 hooks 不會自動跑**，必須每個人在 App 裡按一次 Review hooks／Settings > Hooks 信任；之後我們每改一次 hook 內容，他們要再信任一次。

### 3.4 哪裡看已安裝的東西

- 外掛：**Plugins** 分頁的 **Installed** 列（文件）。
- 技能：側欄 **Skills**（文件；也可用 `codex://skills`）。
- hooks：**Settings > Hooks**（文件）。
- 子代理定義、AGENTS.md 內容：見 3.2、第 4 節。

---

## 4. App 讀不讀 `~/.codex/AGENTS.md`、有沒有編輯介面

- **文件**（https://learn.chatgpt.com/docs/app/settings ，"Personalization"）：
  > "Edit your personal instructions in `AGENTS.md` for the selected machine. Repository instructions can also apply to your chats."
- **文件**（https://learn.chatgpt.com/docs/agent-configuration/agents-md ）："In your Codex home directory (defaults to `~/.codex`, unless you set `CODEX_HOME`)" 先看 `AGENTS.override.md`，否則讀 `AGENTS.md`；"Codex uses only the first non-empty file at this level."
- 小結：App 會讀，而且 **Settings（`Ctrl+,`）> Personalization** 有編輯介面，改的就是個人的 `AGENTS.md`。
- **未確認**：那個編輯框是「整份覆寫」還是「附加」；同事若已經在裡面寫過自己的指示，我們的檔案直接覆蓋會蓋掉他的內容，反之他在介面存檔可能蓋掉我們的。**沒有實測**。
- 載入時機：**文件** "Codex builds an instruction chain when it starts (once per run…)" → 改完要開新對話（保險起見重啟 App）。

---

## 5. Windows 特有事項

- **不需要 WSL**。**文件**："By default, the ChatGPT desktop app uses the Windows-native Codex agent. That means the agent runs commands in PowerShell."
- 沙箱，**文件**（https://learn.chatgpt.com/docs/windows/windows-sandbox ）：三種實作。MXC（建議）"Uses native process isolation without administrator-approved setup"；Elevated "Requires administrator-approved setup"；Unelevated 為舊式退路。"In practice, Windows 10 version 1809 or newer is required."（本機 19045 符合。）同事機器實際用哪一種、會不會跳管理員視窗：**未確認**。
- **hooks 用哪個 shell 跑：文件沒有寫**（Claude 那邊有寫 Git Bash／PowerShell，Codex 這邊沒有對應說明）。文件只提供 `commandWindows`／`command_windows` 這個「Windows 專用指令覆寫」欄位，範例是 `py -3 C:\...`。→ 我們 hooks 的指令在 Windows App 上能不能跑：**未確認，風險高**（若指令依賴 bash 語法或 `python3`，很可能失敗）。
- PowerShell 執行原則：**文件** "npm.ps1 cannot be loaded because running scripts is disabled on this system." 常見解法 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned`。若 hook 是 `.ps1` 會受影響。
- Git：**文件** "If you don't have Git installed natively on Windows, the app can't use some features."（review 面板等）。裝外掛是否需要 Git：文件沒說，**未確認**。
- 路徑含中文（`外掛/`、`AI系統開發兵法`）：文件沒提，**未確認**。建議 zip 內改用英文資料夾名以排除這個變數。

---

## 6. 給非工程師的最穩步驟（只用桌面 App）

前提：同事已裝好 ChatGPT 桌面 App 並登入、能開 Codex 模式。

| 步驟 | 做什麼 | 依據 |
|---|---|---|
| 1 | 把 zip 解壓到固定位置（建議純英文路徑，例如 `C:\dev-bingfa\`），之後不要搬動、不要刪 | 推論（本機來源的外掛要留著來源資料夾才能更新；App 是從 cache 複本載入） |
| 2 | 在 App 用 **Add new project**（`Ctrl+O`）把含有 `.claude-plugin\marketplace.json` 的那個資料夾（我們的 `外掛\`）開成專案，然後**完全關閉並重開 App** | 文件說 App 會讀 `$REPO_ROOT/.claude-plugin/marketplace.json` 並要求 restart；**「開成專案就會被讀到」未驗證** |
| 3 | 開 **Plugins** 分頁，在來源選單選我們的 marketplace，點 `dev-bingfa` 進詳情，按 **+** 安裝 | 文件；**未在 App 實測** |
| 4 | 開一個**新對話**，在輸入框打 `$`（或 `/`），確認清單裡有我們的技能 | 文件；顯示名稱**未驗證** |
| 5 | 若輸入框上方出現 **Review hooks**，點進去逐一信任；或到 **Settings > Hooks** 信任 | 文件；**未在 App 實測**；hooks 在 Windows 能否執行**未驗證** |
| 6 | 把 zip 裡的 `*.toml` 用檔案總管複製到 `%USERPROFILE%\.codex\agents\`（在檔案總管網址列貼上 `%USERPROFILE%\.codex`，沒有 `agents` 資料夾就新建） | 文件（路徑）；App 是否需重啟才認到**未驗證** |
| 7 | `Ctrl+,` 開 **Settings > Personalization**，把我們 `AGENTS.md` 的內容貼進個人指示並存檔（比叫同事去改隱藏資料夾裡的檔案安全） | 文件（有此介面）；貼上後的實際寫入行為**未驗證** |
| 8 | 重啟 App、開新對話，問一句「你現在遵守哪些個人規則？有哪些自訂代理？」做確認 | 推論 |

**如果第 2～3 步在 Plugins 分頁看不到我們的 marketplace**，退路依序是：

- 退路 A（深層連結）：在瀏覽器或「執行」視窗開 `codex://plugins/dev-bingfa?marketplacePath=<marketplace.json 的絕對路徑，需做 URL 編碼>`。文件有此格式，**Windows 路徑與 `.claude-plugin` 位置未驗證**。
- 退路 B（改 zip 結構，我方要做的事）：在 zip 內多放一份 `.agents\plugins\marketplace.json`（文件列為 App 的第一順位位置），或提供一個雙擊即可的安裝腳本，把 marketplace 寫到 `%USERPROFILE%\.agents\plugins\marketplace.json`（文件明列的個人層位置）。
- 退路 C（CLI，一次性）：請同事或 IT 另外裝 CLI 後跑 `codex plugin marketplace add <路徑>` 與 `codex plugin add dev-bingfa@<marketplace 名>`（這條是我們唯一實測過的路，但測的是 0.140.0，不是 App 內建版本），再重啟 App。這違反「只用桌面 App」的要求。

**整條路線沒有驗證的部分（坦白講）**：步驟 2、3、4、5 在 App 上全都沒點過；App 內建引擎版本不明；`.claude-plugin/plugin.json` 格式在新版 App 上沒測；hooks 在 Windows 的執行 shell 文件沒寫；中文路徑沒測。**在發給同事之前，至少要有一個人在一台乾淨的 Windows 機器上，只用 App 實際走完一次。**

---

## 來源

- https://learn.chatgpt.com/docs/windows/windows-app （原 https://developers.openai.com/codex/app/windows ）
- https://learn.chatgpt.com/docs/windows/windows-sandbox
- https://learn.chatgpt.com/docs/plugins （原 https://developers.openai.com/codex/plugins ）
- https://developers.openai.com/plugins/build/plugins
- https://learn.chatgpt.com/docs/hooks （原 https://developers.openai.com/codex/hooks ）
- https://learn.chatgpt.com/docs/build-skills （原 https://developers.openai.com/codex/skills ）
- https://learn.chatgpt.com/docs/skills-and-plugins
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/agent-configuration/agents-md
- https://learn.chatgpt.com/docs/app/settings
- https://learn.chatgpt.com/docs/app/commands
- https://learn.chatgpt.com/docs/reference/slash-commands
- https://learn.chatgpt.com/docs/cli
- 沒有查的：github.com/openai/codex 的原始碼與 issue（時間內未查；若要確認 hooks 在 Windows 用哪個 shell，那裡最可能有答案）。

---

# Claude 桌面 App（已由另一位助手查過，原樣記錄）

以下內容不是本次調查所得，依交辦原樣記錄：

- Claude 桌面 App 的 Code 分頁使用 Plugin manager 介面（+ → Add plugins／Plugins > Manage plugins）。
- Customize > Plugins > Add marketplace **只接受 Git URL 或 owner/repo，不接受本機資料夾**。
- 「Upload plugin」接受一個內含單一 `.claude-plugin/plugin.json` 的 .zip／.plugin，存放在 claude.ai 帳號裡；文件列出的載入位置**不包含**桌面 App 的本機 Code 分頁。
- 在 Code 分頁裡輸入 `/plugin marketplace add <path>` 是否可用：文件沒有記載。
- 文件說終端機、桌面本機工作階段與 VS Code "read the same settings files, so a plugin you install at user scope in any of them is available in the other two"（code.claude.com/docs/en/plugins/install.md），且 `~/.claude/settings.json` 是共用的（desktop.md）。
- 桌面 App 內建 Claude Code，但沒有穩定的 CLI 路徑（本機為 `%APPDATA%\Claude\claude-code\<version>\<hash>\claude.exe`）。
- Windows 上 hooks 在 Git Bash 執行；沒有 Git Bash 時用 PowerShell。
- SessionStart hook 的 `systemMessage` 是否顯示在桌面介面：文件沒有記載。
- 沒有文件記載的桌面介面可以編輯 `~/.claude/CLAUDE.md`（用記事本直接改檔）。
- 確認是否安裝成功：輸入 `/` 應該會列出 `/<plugin>:<skill>`。
