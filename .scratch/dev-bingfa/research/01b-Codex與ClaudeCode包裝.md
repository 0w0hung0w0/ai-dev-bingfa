# 01b — Codex CLI 與 Claude Code 的包裝/安裝機制調查

- 調查日期：2026-11-24
- 實測版本：`codex-cli 0.140.0`、`2.1.330 (Claude Code)`（`claude` 不在 PATH，實際執行檔為 `C:\Users\nick.ch.wei\AppData\Roaming\Claude\claude-code\2.1.330\9424831ad51c\claude.exe`）
- 實測環境：全部用隔離設定目錄 `CODEX_HOME=...\sandbox\codex-home`、`CLAUDE_CONFIG_DIR=...\sandbox\claude-home`，未登入、未建立帳號、未 commit。
- 文件來源注意：Codex 官方文件已搬家，`https://developers.openai.com/codex/...` 會 308 轉址到 `https://learn.chatgpt.com/docs/...`；外掛打包文件在 `https://developers.openai.com/plugins/build/plugins`。兩站都可在網址後加 `.md` 取得原文。**文件描述的是最新版，和本機 0.140.0 有落差（見第 1 題）**，以下凡是「實測」都以本機為準。

信心標記：高 = 官方文件 + 本機實測一致；中 = 只有官方文件或只有實測；低 = 推論。

---

## 總結（先看這段）

1. **一個資料夾可以同時當 Claude Code 外掛與 Codex 外掛**，而且只要 Claude 的那一份 manifest 就夠：`.claude-plugin/plugin.json` + `.claude-plugin/marketplace.json` + `skills/`。本機實測兩邊都安裝成功；Matt Pocock 的 repo 也正是這樣做。
2. 但 **Codex 外掛只會載入 skills（以及 MCP、apps、hooks）**；`agents/` 與 `commands/` 會被複製進快取卻不會被載入。所以 3 個 subagent 在 Codex 必須另外放 TOML 檔到 `~/.codex/agents/`，規則檔必須另外放 `AGENTS.md`。
3. **`commit` 請做成 skill，不要做成 command**：Codex 的 custom prompts（`~/.codex/prompts/*.md`）官方已標為 deprecated，且不能隨外掛散佈。
4. **Hook 的事件名稱與 JSON 格式兩邊幾乎相同**（Codex 是照 Claude Code 的格式做的），同一支 Python `Stop` 腳本原則上可共用；但 Codex 的 hook 需要使用者在 `/hooks` 手動「信任」才會跑，而且本機有公司管控的 hook 設定，我**沒能實測到自訂 hook 真的執行**。
5. 本機 0.140.0 **不支援**文件主推的「根目錄 `plugin.json`」新格式（實測報 `missing plugin.json`）。

---

## 1. Codex 有沒有外掛/打包格式？

**結論**：有。Codex 0.140.0 有 `codex plugin` 子指令與 marketplace 機制，可以從本機資料夾安裝；外掛可含 skills、MCP、apps、hooks，**不含** subagent 與 slash command。

**證據（指令）**

```
> codex plugin --help
Commands:
  add          Install a plugin from a configured marketplace snapshot
  list         List plugins available from configured marketplace snapshots
  marketplace  Add, list, upgrade, or remove configured plugin marketplaces
  remove       Remove an installed plugin from local config and cache

> codex plugin marketplace add --help
  <SOURCE>  Marketplace source: a local path, owner/repo[@ref], HTTPS Git URL, or SSH Git URL
```

`codex features list` 顯示 `plugins  stable  true`、`hooks  stable  true`、`multi_agent  stable  true`。

**證據（文件）** `https://developers.openai.com/plugins/build/plugins.md`

- manifest 路徑（文件說法）：「A portable plugin has a `plugin.json` manifest at its root.」「Existing `.codex-plugin/plugin.json` files remain supported as a compatibility fallback.」「OpenAI also accepts legacy and Claude-compatible manifests, but new packages should use this format.」
- 欄位：`$schema`（`https://agent-plugins.org/schemas/1.0.0/plugin.schema.json`）、`name`（kebab-case）、`version`、`description`、`author{name,email,url}`、`homepage`、`repository`、`license`、`keywords`；OpenAI 專屬放在 `extensions.com.openai`（`apps`、`hooks`、`onboardingSkill`、`interface{displayName,shortDescription,...}`）。舊格式 `.codex-plugin/plugin.json` 另有 `skills: "./skills/"`、`hooks`、`apps`。
- 可包含：「A `skills/` directory…」「An `mcp.json` file for MCP servers…」「Optional assets.」「Lifecycle hooks (manually installed Codex desktop plugins only).」
- marketplace 檔：`$REPO_ROOT/.agents/plugins/marketplace.json`、`~/.agents/plugins/marketplace.json`，以及「a legacy-compatible marketplace at `$REPO_ROOT/.claude-plugin/marketplace.json`」。每筆要有 `policy.installation`、`policy.authentication`、`category`。
- 安裝後位置：「`~/.codex/plugins/cache/$MARKETPLACE_NAME/$PLUGIN_NAME/$VERSION/`」。

**證據（實測，與文件不同之處）**

| 外掛資料夾裡的 manifest | marketplace 檔 | `codex plugin add` 結果 |
|---|---|---|
| `.codex-plugin/plugin.json`（同時也有 `.claude-plugin/plugin.json`） | `.agents/plugins/marketplace.json` | 成功 |
| **只有** `.claude-plugin/plugin.json` | **只有** `.claude-plugin/marketplace.json` | 成功 |
| 只有根目錄 `plugin.json`（文件主推的新格式） | `.agents/plugins/marketplace.json` | **失敗：`Error: missing plugin.json`** |

模型實際看到的說明文字（`codex debug prompt-input`）：「A plugin is a local bundle of skills, MCP servers, and apps.」外掛裡的 `agents/demo-agent.md`、`commands/demo-cmd.md` 有被複製進快取，但沒有出現在模型可見的清單中。

文件有一句和實測不一致：「These commands support plugin authoring and catalog setup. Use the ChatGPT desktop app to install and test a local plugin.」——但 0.140.0 的 `codex plugin add` 在 CLI 直接裝成功了。

**信心**：高（安裝流程、可含內容）；中（root `plugin.json` 何時開始支援——文件說支援，本機版不支援）。

**對我們的影響**：Codex 這邊可以用外掛散佈 3 個 skill（含 `commit`）；3 個 subagent 與規則檔不能進外掛，要另外處理。不要用根目錄 `plugin.json` 新格式。

---

## 2. 一個資料夾能不能同時是兩邊的外掛？

**結論**：可以；最小做法是只放 Claude 的兩個 JSON（`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`）加共用的 `skills/`，Codex 會直接吃。

**證據（實測）** sandbox 的 `claude-only-mkt/`：

```
> codex plugin marketplace add "...\sandbox\claude-only-mkt"
Added marketplace `conly-local` from \\?\C:\...\sandbox\claude-only-mkt.
> codex plugin add conly-demo@conly-local
Added plugin `conly-demo` from marketplace `conly-local`.
> codex plugin list
Marketplace `conly-local`
C:\...\sandbox\claude-only-mkt\.claude-plugin\marketplace.json
conly-demo@conly-local  installed, enabled  0.0.1
```

`codex debug prompt-input` 的 skills 清單裡出現 `conly-demo:conly-skill`。同一種資料夾（`dual-mkt/`）用 Claude Code 也安裝成功（見第 10 題）。

**證據（第三方實例）** `https://github.com/mattpocock/skills` 只有 `.claude-plugin/plugin.json` 與 `.claude-plugin/marketplace.json`（`"source": "./"`），README 卻同時列出 `claude plugin install ...` 與 `codex plugin marketplace add mattpocock/skills` / `codex plugin add mattpocock-skills@mattpocock`。

**兩邊各自會載入什麼（同一個資料夾）**

| 資料夾內容 | Claude Code | Codex 0.140 |
|---|---|---|
| `skills/<name>/SKILL.md` | 載入，叫 `/外掛名:skill名` | 載入，清單上叫 `外掛名:skill名` |
| `agents/*.md` | 載入，叫 `外掛名:agent名` | **不載入** |
| `commands/*.md` | 載入（`claude plugin details` 把它算在 Skills 裡） | **不載入** |
| `hooks/hooks.json` | 載入 | 文件說會自動找這個預設路徑；未實測到執行 |
| `CLAUDE.md` / `AGENTS.md` | **不載入** | **不載入** |

**注意**：兩種 marketplace 檔同時存在時，Codex 選的是 `.agents/plugins/marketplace.json`（`dual-mkt` 的 `codex plugin list` 顯示該路徑）。兩份內容不同步會造成兩邊行為不一致，所以建議只留 `.claude-plugin/` 那一份。

**最小重複清單**

- 共用：`.claude-plugin/plugin.json`、`.claude-plugin/marketplace.json`、`skills/`（含 `commit` skill）、hook 的 Python 腳本。
- 只給 Claude：`agents/*.md`（放外掛內即可）。
- 只給 Codex（外掛外，需要安裝腳本或手動複製）：`agents/*.toml` → `~/.codex/agents/`；`AGENTS.md` → `~/.codex/AGENTS.md` 或專案根目錄。
- 規則檔在 Claude 也要外掛外處理（`~/.claude/CLAUDE.md` 或專案 `CLAUDE.md`）。

**信心**：高（skills 共用，雙邊實測）；中（`hooks/hooks.json` 被兩邊同時撿到的後果，Codex 端未實測到執行）。

**對我們的影響**：可以做成「一個資料夾、一份 manifest」。但 `hooks/hooks.json` 會被兩邊都撿走，寫的時候要以兩邊都能跑為前提，或乾脆不放外掛內、改用各自的設定檔。

---

## 3. Codex skills

**結論**：Codex 原生讀 `.agents/skills`（專案）與 `~/.agents/skills`（使用者）；本機 0.140.0 另外仍會讀 `$CODEX_HOME/skills` 與專案的 `.codex/skills`，不讀 `.claude/skills`。

**證據（文件）** `https://learn.chatgpt.com/docs/build-skills.md`

- 路徑表：`$CWD/.agents/skills`、`$CWD/../.agents/skills`、`$REPO_ROOT/.agents/skills`、`$HOME/.agents/skills`、`/etc/codex/skills`、內建（`skill-creator`、`skill-installer`）。
- 「The `SKILL.md` file must include `name` and `description`.」
- 呼叫：「In Codex CLI or the IDE extension, run `/skills` or type `$` to mention a skill.」也會依 `description` 自動觸發。
- 只准手動呼叫：在 skill 資料夾加 `agents/openai.yaml`，內容 `policy:\n  allow_implicit_invocation: false`。「explicit `$skill` invocation still works.」
- 清單預算：「at most 2% of the model's context window, or 8,000 characters when the context window is unknown」，超過會先縮短描述。
- 停用：`~/.codex/config.toml` 的 `[[skills.config]]`（`path` 或 `name` + `enabled = false`）。

**證據（實測）** 在 `sandbox/proj/sub` 執行 `codex debug prompt-input "hi"`（不需登入），檢查清單內有無探針 skill：

| 位置 | 有被載入？ |
|---|---|
| `proj/.agents/skills/proj-agents-skill`（repo 根，cwd 在子資料夾） | 有 |
| `proj/.codex/skills/proj-codex-skill` | 有（文件未列） |
| `$CODEX_HOME/skills/codexhome-skill` | 有（文件未列；內建 `skill-installer` 的描述仍寫「Install Codex skills into $CODEX_HOME/skills」） |
| `proj/.claude/skills/proj-claude-skill` | 沒有 |
| 真實的 `C:/Users/nick.ch.wei/.agents/skills/*` | 有（見下方「意外」） |
| 外掛 skill | 有，名稱為 `bingfa-demo:hello-demo`、`conly-demo:conly-skill` |

**列出已安裝 skill**：TUI 內 `/skills`；CLI 沒有 `codex skills` 子指令。不登入也能用的替代法是 `codex debug prompt-input`（輸出 JSON，裡面有 `### Available skills`）。

**意外（需揭露）**：我把 `USERPROFILE` / `HOME` 指到 sandbox 的假家目錄，但 Codex 仍然讀了真實的 `~/.agents/skills`（清單出現 `blast-radius`、`brownfield-recon` 等）。只有讀取，沒有寫入或修改。

**未驗證**：Claude 專用的 frontmatter `disable-model-invocation: true` 在 Codex 是否有效（推測被忽略，Codex 用的是 `agents/openai.yaml`）。

**信心**：高。

**對我們的影響**：若不走外掛，直接把 skill 資料夾複製到 `~/.agents/skills/` 也能讓 Codex 用（Claude 則是 `~/.claude/skills/`）。要「只能手動叫」的 skill 得兩邊各寫一種設定：Claude 用 frontmatter `disable-model-invocation: true`，Codex 用 `agents/openai.yaml`。

---

## 4. Codex subagents

**結論**：格式是 TOML，一檔一個 agent，放 `~/.codex/agents/`（個人）或 `.codex/agents/`（專案）；必填 `name`、`description`、`developer_instructions`；無法在檔內設定工具或沙箱。

**證據（文件）** `https://learn.chatgpt.com/docs/agent-configuration/subagents.md`

- 「add standalone TOML files under `~/.codex/agents/` for personal agents or `.codex/agents/` for project-scoped agents.」
- 「Every standalone custom agent file must define: `name` `description` `developer_instructions`」
- 選填：`model`、`model_reasoning_effort`、`model_reasoning_summary`、`model_verbosity`；可關閉功能 `features.shell_tool` 等；`[[skills.config]]` 停用個別 skill。
- 「Other session settings, including `sandbox_mode`, `approval_policy`, `model_provider`, and `mcp_servers`, don't override the parent configuration when placed in a custom agent file.」「Custom agent instructions can ask an agent to avoid edits, but they don't create a separate read-only sandbox.」
- 呼叫方式：在對話中直接要求（例：「Have pr_explorer map the affected code paths…」），或由 `AGENTS.md` / skill 的指示觸發；`/subagents` 切換檢視。
- 內建 agent：`default`、`worker`、`explorer`。「If a custom agent name matches a built-in agent such as `explorer`, your custom agent takes precedence.」

**最小可用範例**（`~/.codex/agents/reviewer.toml`）

```toml
name = "reviewer"
description = "PR reviewer focused on correctness, security, and missing tests."
developer_instructions = """
Review code like an owner.
Do not edit files.
"""
```

**證據（實測）** 在 `$CODEX_HOME/agents/` 放一個缺 `developer_instructions` 的檔，`codex exec` 啟動時印出：

```
warning: Ignoring malformed agent role definition: agent role file at ...\codex-home\agents\broken-agent.toml must define `developer_instructions`
```

證明該資料夾確實被讀取並驗證。實際叫 subagent 工作需要登入，未測。

**信心**：高（格式與位置）；中（實際派工行為，未實測）。

**對我們的影響**：
- 每個 agent 要維護兩份：Claude 的 `agents/*.md`（frontmatter + 內文）與 Codex 的 `*.toml`（內文搬進 `developer_instructions`）。
- Claude 的 `tools:` 白名單在 Codex 沒有對應物，「唯讀」只能靠指示文字。
- 若我們的 agent 取名 `explorer`，在 Codex 會**蓋掉內建的 `explorer`**，要先決定這是不是想要的。
- 不要在 TOML 寫死 `model`（文件範例的型號如 `gpt-6.2-sol` 會變動），省略就繼承主對話的模型。

---

## 5. Codex 自訂 slash command / prompts

**結論**：`~/.codex/prompts/*.md` 仍有文件但已標為 deprecated，官方明說用 skill 取代；它也不能放進專案或外掛。

**證據（文件）** `https://learn.chatgpt.com/docs/custom-prompts.md`

- 「Custom prompts are deprecated. Use skills for reusable instructions that Codex can invoke explicitly or implicitly.」
- 「Custom prompts require explicit invocation and live in your local Codex home directory (for example, `~/.codex`), so they're not shared through your repository.」
- 呼叫為 `/prompts:draftpr`；支援 `$1`–`$9`、`$ARGUMENTS`、`KEY=value`；「Codex scans only the top-level Markdown files in that folder」。
- 文件索引 `https://learn.chatgpt.com/llms.txt` 的條目：「Custom Prompts: Deprecated. Use skills for reusable prompts」。

**實測**：0.140.0 是否還會載入 `~/.codex/prompts/` 無法驗證（要進 TUI 打 `/`，需要登入）。`codex debug prompt-input` 裡沒有它，這符合預期（prompts 是使用者端展開，不進模型清單）。

**信心**：高（已棄用、官方建議改用 skill）；低（0.140.0 是否仍可用）。

**對我們的影響**：`commit` 做成 skill 一份通吃。Claude 端叫 `/外掛名:commit`，Codex 端叫 `$外掛名:commit`（或 `/skills` 選）。Claude Code 也已把 commands 併入 skills（`claude plugin details` 把 `demo-cmd` 列在「Skills (2)」底下；文件寫「Prefer `skills/` for new plugins」）。

---

## 6. Codex hooks（與 Claude Code 比較）

**結論**：Codex hooks 的設定形狀、核心事件名稱、stdin JSON 與阻擋方式都和 Claude Code 相容，一支讀 stdin JSON 的 Python `Stop` 腳本可以共用；差別在安裝位置、信任流程與少數欄位。

**證據（文件）** `https://learn.chatgpt.com/docs/hooks.md`

- 位置：使用者 `$CODEX_HOME/hooks.json`（Windows 預設 `%USERPROFILE%\.codex\hooks.json`）、受信任專案 `.codex/hooks.json`、系統 `%ProgramData%\OpenAI\Codex\hooks.json`；也可寫在 `config.toml` 的 `[hooks]`；外掛預設 `hooks/hooks.json`。
- 格式：`{"hooks": {"Stop": [{"matcher": "...", "hooks": [{"type": "command", "command": "...", "timeout": 30}]}]}}`——與 Claude Code 相同的三層結構。
- 事件：`PreToolUse`、`PermissionRequest`、`PostToolUse`、`PreCompact`、`PostCompact`、`UserPromptSubmit`、`SubagentStop`、`Stop`、`PreModelRequest`、`PostModelRequest`、`Interrupt`、`SessionStart`、`SubagentStart`、`SessionEnd`。
- stdin 共同欄位：`session_id`、`transcript_path`、`cwd`、`hook_event_name`、`model`（Codex 專屬）；`Stop` 另有 `turn_id`、`stop_hook_active`、`last_assistant_message`。
- 阻擋/回饋：`Stop` 回 `{"decision":"block","reason":"..."}` 會讓 Codex 繼續做，「using your `reason` as that prompt text」；「You can also use exit code `2` and write the continuation reason to `stderr`.」；`PreToolUse` 用 `hookSpecificOutput.permissionDecision: "deny"` 或舊式 `decision: "block"` 或 exit 2。
- 「`Stop` expects JSON on `stdout` when it exits `0`. Plain text output is invalid for this event.」「Exit `0` with no output is treated as success」。
- Windows：有 `commandWindows`（TOML 為 `command_windows`）可覆寫 Windows 指令；系統層有 Windows 路徑。文件沒有說 Windows 不支援。
- 信任：「Non-managed hooks must be reviewed and trusted before they run.」用 `/hooks` 檢視與信任；「If a plugin update changes a bundled script, Codex requires a new review even if the hook definition stays the same.」
- 外掛 hook 的環境變數：`PLUGIN_ROOT`、`PLUGIN_DATA`，且「Codex also sets `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` for compatibility with existing plugin hooks.」
- 限制：「`command` and `mcp_tool` handlers are supported. `prompt` and `agent` handlers are parsed but skipped.」

**Claude Code 對照** `https://code.claude.com/docs/en/hooks.md`

- 事件 33 種，含 Codex 沒有的 `PostToolUseFailure`、`PostToolBatch`、`Notification`、`StopFailure`、`TaskCreated`、`TaskCompleted`、`InstructionsLoaded`、`ConfigChange`、`WorktreeCreate` 等；Codex 獨有 `PreModelRequest`、`PostModelRequest`、`Interrupt`。
- `Stop` 的輸入：「Stop hooks receive `stop_hook_active`, `last_assistant_message`, `background_tasks`, and `session_crons`.」阻擋方式同為 `{"decision":"block","reason":...}` 或 exit 2 + stderr。
- Claude 有「8-consecutive-continuation cap」；Codex 文件未提上限，所以腳本一定要自己檢查 `stop_hook_active`。
- Windows：hook 預設用 Git Bash 執行，沒裝才用 PowerShell；可用 `"shell": "powershell"` 指定。

**共用一支 Python 腳本的條件**

- 只讀兩邊都有的欄位：`hook_event_name`、`cwd`、`stop_hook_active`、`last_assistant_message`。
- 不要解析 `transcript_path` 指向的檔案（兩邊格式不同，Codex 明說「isn't a stable interface」）。
- 放行時 exit 0 且**不印任何東西**；要擋時印 `{"decision":"block","reason":"..."}`（或 exit 2 + stderr）。不要印純文字到 stdout。
- 指令列用 `python`（Windows 上通常沒有 `python3`）；Codex 可用 `commandWindows` 分開寫。
- 腳本路徑在外掛內可用 `${CLAUDE_PLUGIN_ROOT}`（兩邊都會設定這個環境變數；Codex 在 Windows 上是否會展開 `${...}` 寫法**未驗證**）。

**實測結果（部分失敗，如實記錄）**

- `codex exec --dangerously-bypass-hook-trust ...`（未登入）會跑到 `hook: SessionStart` / `hook: UserPromptSubmit` 後才因 401 失敗，所以 hook 階段可在不登入下觀察。
- 但那兩行其實是**公司管控的 hook**：本機有 `C:\ProgramData\OpenAI\Codex\requirements.toml`，對 `PreToolUse`、`PostToolUse`、`UserPromptSubmit`、`PermissionRequest`、`SessionStart`、`Stop` 六個事件都掛了標註 `# koi-managed` 的 PowerShell hook。檔內沒有 `allow_managed_hooks_only`。
- 我放在 `$CODEX_HOME/hooks.json` 的自訂 hook 有被**讀到**（同時寫 `config.toml` 時出現 `warning: loading hooks from both ...hooks.json and ...config.toml; prefer a single representation`），但**沒有任何一次留下執行痕跡**（預期要寫出的檔案都沒出現，試過 `python 腳本`、`echo > 檔案`、絕對與相對路徑）。原因未查明——可能是信任機制、Windows 上的執行方式、或管控設定。外掛內的 `hooks/hooks.json` 同樣沒看到執行痕跡。
- `Stop` 事件需要模型真的回覆一輪才會觸發，未登入無法測。

**信心**：高（文件層面的格式相容）；低（在這台機器上自訂 Codex hook 能否實際執行）。

**對我們的影響**：Python hook 腳本可以只寫一份，但 Codex 端要把它當「選配、需人工在 `/hooks` 信任、且在公司電腦上可能跑不起來」來設計，不能讓整包的正確性依賴它。安裝說明要告訴使用者：Codex 第一次啟動會提示有 hook 待審核。

---

## 7. Codex `AGENTS.md`

**結論**：先讀全域 `~/.codex/AGENTS.md`，再從專案根一路讀到目前資料夾，越靠近的排越後面（等於優先）；合計上限預設 32 KiB。

**證據（文件）** `https://learn.chatgpt.com/docs/agent-configuration/agents-md.md`

- 全域：「In your Codex home directory (defaults to `~/.codex`, unless you set `CODEX_HOME`), Codex reads `AGENTS.override.md` if it exists. Otherwise, Codex reads `AGENTS.md`.」
- 專案：「Starting at the project root (typically the Git root), Codex walks down to your current working directory… it checks for `AGENTS.override.md`, then `AGENTS.md`, then any fallback names in `project_doc_fallback_filenames`. Codex includes at most one file per directory.」
- 上限：「stops adding files once the combined size reaches the limit defined by `project_doc_max_bytes` (32 KiB by default)」。

**證據（實測）** `codex debug prompt-input` 的輸出順序：

```
<INSTRUCTIONS>
PROBE-GLOBAL-AGENTS-MD
--- project-doc ---
PROBE-PROJECT-AGENTS-MD
PROBE-SUB-AGENTS-MD
</INSTRUCTIONS>
```

同資料夾的 `CLAUDE.md`（`PROBE-CLAUDE-MD`）**沒有**被讀。

**補充（Claude 端）** `https://code.claude.com/docs/en/memory.md`：Claude Code 也能讀 `AGENTS.md`，但「By default, Claude reads `AGENTS.md` only when you have no `CLAUDE.md` in your working directory or above it.」「Reading `AGENTS.md` directly requires Claude Code v2.1.277 or later.」

**信心**：高。

**對我們的影響**：規則檔無法由外掛帶入。專案層可以只放一份 `AGENTS.md`（沒有 `CLAUDE.md` 時 Claude Code 2.1.277+ 也會讀）；全域層仍是兩個位置（`~/.codex/AGENTS.md` 與 `~/.claude/CLAUDE.md`）。規則檔要控制在 32 KiB 以內（與全域、其他層合計）。

---

## 8. Claude Code 外掛（重新驗證）

**結論**：既有認知大致正確；新增兩個對「非工程師、不靠 GitHub」很有用的管道：`--plugin-dir` 可直接吃 `.zip`，以及把外掛資料夾丟進 `~/.claude/skills/` 就每次自動載入。

**manifest**（`https://code.claude.com/docs/en/plugins-reference.md`）：位置 `.claude-plugin/plugin.json`；「`name` is the only required key.」甚至「The manifest is optional.」其他欄位：`displayName`、`version`、`description`、`author{name,email,url}`、`homepage`、`repository`、`license`、`keywords`、`defaultEnabled`、`engines`、`dependencies`、`userConfig`、`skills`、`commands`、`agents`、`hooks`、`mcpServers` 等。`version` 的副作用：「Setting it keeps users on that version until you change it」。

**預設佈局**：`skills/`、`commands/`（「Prefer `skills/` for new plugins」）、`agents/`、`hooks/hooks.json`、`.mcp.json`、`.lsp.json`、`output-styles/`、`bin/` 等。

**從本機資料夾安裝的三條路**

1. 本機 marketplace（實測成功，見第 10 題）：
   - 資料夾根放 `.claude-plugin/marketplace.json`（`name`、`owner.name`、`plugins[].name`、`plugins[].source`）。
   - `claude plugin marketplace add <路徑>` → `claude plugin install <外掛>@<marketplace>`。
   - 一行版：`claude plugin install <外掛> --marketplace <路徑>`（`--help` 原文：「A marketplace not added yet is added first」）。
   - 對話內：`/plugin marketplace add <路徑>`、`/plugin install <外掛>@<marketplace>`；文件另載「`/plugin install deploy-helper --marketplace your-org/your-marketplace`. Requires Claude Code v2.1.275 or later.」
2. 單次載入：`claude --plugin-dir <資料夾或 .zip>`（`--help`：「Load a plugin from a directory or .zip」）。
3. 免指令常駐：`https://code.claude.com/docs/en/plugins/publish.md`「they move the plugin directory, with its `.claude-plugin/plugin.json`, under `~/.claude/skills/`. From then on Claude Code loads it at startup」，載入名稱為 `<name>@skills-dir`。（未實測，因為不能動真實的 `~/.claude`；隔離目錄下也需要開 session 才能確認。）

**外掛 agent 被忽略的 frontmatter**（`https://code.claude.com/docs/en/sub-agents.md`）：「plugin subagents don't support the `hooks`, `mcpServers`, or `permissionMode` frontmatter fields. These fields are ignored when loading agents from a plugin.」另 `initialPrompt` 也標示「Ignored for plugin subagents」。`model`、`tools` 仍有效。

**`${CLAUDE_PLUGIN_ROOT}`**：外掛安裝後的根目錄，可用在 hook 指令與 MCP 設定，例：`"command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format.sh"`。

**外掛能不能帶 CLAUDE.md**：不能。「A `CLAUDE.md` at the plugin root isn't loaded as context, and `claude plugin validate` warns when it finds one. To include instructions that load into Claude's context, put them in a skill.」

**命名空間**：skill 與 command 為 `/plugin-name:skill-name`；agent 為 `plugin-name:agent-name`，手動提及寫 `@agent-my-plugin:code-reviewer`。實測 `claude plugin validate` 輸出 `skills: bingfa-demo:hello-demo`、`commands: bingfa-demo:demo-cmd`、`agents: bingfa-demo:demo-agent`。

**信心**：高（marketplace 安裝流程、命名、被忽略欄位）；中（`.zip` 與 `~/.claude/skills/` 兩條路，只有文件與 `--help`）。

**對我們的影響**：
- 我們 agent 檔若用到 `permissionMode`、`hooks`、`mcpServers`，放進外掛後會無聲失效；要嘛不用，要嘛改成複製到 `~/.claude/agents/`。
- skill 進外掛後名字會多一段前綴（`/bingfa:commit` 而非 `/commit`）。若一定要短名 `/commit`，就得走「複製到 `~/.claude/skills/`」而非外掛。這是要請使用者裁決的取捨。
- 本機 marketplace 是以**路徑**登記的（`settings.json` 的 `extraKnownMarketplaces` 記 `"source": "directory", "path": ...`），使用者解壓後若搬動或刪掉資料夾，更新會失效；說明書要寫「解壓到固定位置後再安裝」。

---

## 9. Matt Pocock skills

**結論**：官方安裝方式現在是「外掛優先」；`npx skills@latest add ...` 只列給「其他 agent 或想要可編輯檔案」的情況，且需要 Node 22.20 以上。

**證據** `https://github.com/mattpocock/skills`（README，main 分支）

- Claude Code：`claude plugin install mattpocock-skills@claude-plugins-official`（「Updates itself by default.」）
- Codex：`codex plugin marketplace add mattpocock/skills` 然後 `codex plugin add mattpocock-skills@mattpocock`（「Updates itself at startup.」）
- 其他：`npx skills@latest add mattpocock/skills -a <agent>  # cursor, opencode, devin, windsurf, amp, pi; omit -a to choose`。README 的 `-a` 範例**沒有列 claude-code 或 codex**。
- README 警告：「Pick one per agent, because installing both gives you every skill twice.」
- 裝完要跑一次 `/setup-matt-pocock-skills`。
- 授權：`LICENSE` 為「MIT License / Copyright (c) 2026 Matt Pocock」；`plugin.json` 的 `"license": "MIT"`，版本 `1.3.2`。
- Node 需求：npm 上的 `skills` CLI 1.9.0，`engines: {"node": ">=22.20.0"}`（來源 `https://registry.npmjs.org/skills/latest`，套件屬 `vercel-labs/skills`）。本機 Node v24 符合。

**外掛實際收錄的 27 個 skill**（依 `.claude-plugin/plugin.json` 的 `skills` 陣列）

- Engineering，只能使用者手動叫：`ask-matt`、`grill-with-docs`、`triage`、`improve-codebase-architecture`、`setup-matt-pocock-skills`、`to-spec`、`to-tickets`、`implement`、`implement-spec`、`wayfinder`、`retro`
- Engineering，模型也可自動叫：`prototype`、`diagnosing-bugs`、`research`、`tdd`、`domain-modeling`、`codebase-design`、`code-review`、`pr`、`wizard`
- Productivity，只能使用者手動叫：`grill-me`、`handoff`、`teach`、`to-questionnaire`、`wait-what`
- Productivity，模型也可自動叫：`grilling`、`writing-for-agents`

repo 內另有未收進外掛的 `skills/in-progress/*`（8 個）與 `skills/misc/*`（4 個）。

「只能手動叫」的實作方式是 frontmatter `disable-model-invocation: true`（已看 `skills/productivity/grill-me/SKILL.md`）。README 原文：「**User-invoked** skills are reachable only when you type them… A user-invoked skill may invoke model-invoked skills, but never another user-invoked one.」

**信心**：高。

**對我們的影響**：
- 這個 repo 是「單一 `.claude-plugin/` 同時供 Claude Code 與 Codex」的現成範本，可以照抄結構。
- 它是 MIT，改寫引用時保留著作權聲明即可。
- 本機 Claude Code 已裝這個外掛（技能清單裡有 `mattpocock-skills:*`），我們的 skill 若同名要注意混淆。
- 他的 skill 名單與之前認知不同處：現在有 `wayfinder`、`handoff`、`grill-with-docs`、`triage` 等，與使用者 CLAUDE.md 第 6 節引用的名稱吻合。

---

## 10. 實測紀錄

所有檔案留在 `C:\Users\nick.ch.wei\Desktop\AI系統開發兵法\.scratch\dev-bingfa\research\sandbox\`。

### 版本與說明

```
> codex --version
codex-cli 0.140.0
> claude --version      （用完整路徑執行）
2.1.330 (Claude Code)
```

`codex --help` 的子指令中與本案相關者：`plugin`、`mcp`、`features`、`debug`、`doctor`、`exec`。沒有 `skills`、`agents`、`hooks` 子指令。
`claude plugin --help` 的子指令：`configure`、`details`、`disable`、`enable`、`eval`、`init|new`、`install|i`、`list`、`marketplace`、`prune`、`tag`、`test`、`uninstall|remove`、`update`、`validate`。

### (a) Claude Code：假外掛從本機路徑安裝（全部成功，不需登入）

測試資料夾 `sandbox\dual-mkt\`：

```
dual-mkt/
├── .claude-plugin/marketplace.json
├── .agents/plugins/marketplace.json        （給 Codex 的對照組）
└── plugins/bingfa-demo/
    ├── .claude-plugin/plugin.json
    ├── .codex-plugin/plugin.json
    ├── skills/hello-demo/SKILL.md
    ├── agents/demo-agent.md
    ├── commands/demo-cmd.md
    └── hooks/hooks.json, stop_check.py, dump.py
```

```
> claude plugin validate "...\sandbox\dual-mkt"
√ Validation passed with warnings        （警告：缺 marketplace description、缺 author）

> claude plugin validate "...\sandbox\dual-mkt\plugins\bingfa-demo"
Provides:
  > hooks: Stop command "python \"${CLAUDE_PLUGIN_ROOT}/hooks/stop_check.py\""
  > skills: bingfa-demo:hello-demo
  > commands: bingfa-demo:demo-cmd
  > agents: bingfa-demo:demo-agent
√ Validation passed with warnings        （另提示缺 README.md、LICENSE、icon，僅在投稿官方目錄時才算錯）

> claude plugin validate --strict ...     → exit=1（警告視為錯誤）

> claude plugin marketplace add "...\sandbox\dual-mkt"
√ Successfully added marketplace: bingfa-local (declared in user settings)

> claude plugin install bingfa-demo@bingfa-local
√ Successfully installed plugin: bingfa-demo@bingfa-local (scope: user)

> claude plugin list
  > bingfa-demo@bingfa-local   Version: 0.0.1   Scope: user   Status: √ enabled

> claude plugin details bingfa-demo@bingfa-local
  Skills (2)  demo-cmd, hello-demo
  Agents (1)  demo-agent
  Hooks (1)  Stop
```

寫入位置都在隔離目錄：`claude-home\settings.json`（`extraKnownMarketplaces`、`enabledPlugins`）、`claude-home\plugins\installed_plugins.json`、`claude-home\plugins\cache\bingfa-local\bingfa-demo\0.0.1`。

### (b) Codex：同一個資料夾（成功，不需登入）

```
> codex plugin marketplace add "...\sandbox\dual-mkt"
Added marketplace `bingfa-local` from \\?\C:\...\sandbox\dual-mkt.

> codex plugin list --available --json     → 列出 bingfa-demo@bingfa-local，"installPolicy": "AVAILABLE"

> codex plugin add bingfa-demo@bingfa-local
Added plugin `bingfa-demo` from marketplace `bingfa-local`.
Installed plugin root: ...\codex-home\plugins\cache\bingfa-local\bingfa-demo\0.0.1

> codex plugin list
bingfa-demo@bingfa-local  installed, enabled  0.0.1
```

`codex-home\config.toml` 被寫入 `[marketplaces.bingfa-local]`（`source_type = "local"`）與 `[plugins."bingfa-demo@bingfa-local"] enabled = true`。路徑含中文也能正常運作。

其他 Codex 實測（細節見各題）：Claude 專用佈局安裝成功；根目錄 `plugin.json` 失敗；`codex debug prompt-input` 驗證 skill 路徑與 `AGENTS.md` 順序；壞掉的 agent TOML 會出警告。

### 不需登入就能做的事

- Claude：`plugin validate`、`plugin marketplace add/list`、`plugin install`、`plugin list`、`plugin details`。
- Codex：`plugin marketplace add/list`、`plugin add/list/remove`、`features list`、`debug prompt-input`（可看 skills 清單與 `AGENTS.md` 合併結果）、`exec` 可跑到 hook 階段與設定檔警告。

### 無法測試（都需要已登入的模型呼叫或互動式 TUI）

- 任一邊實際「叫用」skill、派 subagent、`Stop` hook 觸發。
- Codex TUI 的 `/skills`、`/hooks`、`/plugins`、`/prompts:*`、`/subagents`。
- Claude 的 `--plugin-dir <zip>` 與 `~/.claude/skills/` 常駐載入。
- Codex 自訂 hook 的實際執行（已嘗試，未成功，原因未明，見第 6 題）。

---

## 與先前假設的對照

| 先前假設 | 判定 | 說明 |
|---|---|---|
| Codex 原生讀 `.agents/skills` 與 `~/.agents/skills` | 正確，但不完整 | 0.140.0 另外還讀 `$CODEX_HOME/skills` 與專案 `.codex/skills`；而且 Codex 已有外掛機制，可直接吃 Claude 格式的外掛 |
| 規則檔是 `AGENTS.md` | 正確 | 另有 `AGENTS.override.md`、32 KiB 上限；Claude Code 2.1.277+ 在沒有 `CLAUDE.md` 時也讀 `AGENTS.md` |
| agent 是 TOML | 正確 | 必填三欄；不能設工具/沙箱；`explorer` 同名會蓋掉內建 |
| hook 事件與 Claude Code 不同 | **不正確** | 核心事件同名（`PreToolUse`、`PostToolUse`、`UserPromptSubmit`、`Stop`、`SubagentStop`、`SessionStart`、`SessionEnd`、`PreCompact`、`PostCompact`、`PermissionRequest`、`SubagentStart`），設定結構與阻擋方式也相同；差異只在各自多出的事件與信任流程 |

---

## 我漏掉的、放棄的、用猜的

- **放棄**：查明 Codex 自訂 hook 在這台機器上為何沒有執行痕跡（試了 6 輪後停手）。
- **用猜的**：`disable-model-invocation` 在 Codex 會被忽略；Codex 在 Windows 上會不會展開 hook 指令裡的 `${CLAUDE_PLUGIN_ROOT}`；`.claude-plugin/plugin.json` 與 `.codex-plugin/plugin.json` 並存時 Codex 以哪份為準（測試時兩份內容相同，分不出來）。
- **漏掉**：沒有查 Codex 外掛的自動更新對「本機路徑 marketplace」如何運作；沒有驗證 Claude 桌面版 App 的外掛安裝介面；沒有查 Codex `/import`（可從 Claude Code 匯入設定）能否代替安裝流程——只確認了它存在（`https://learn.chatgpt.com/docs/import.md`）。
- **實驗副作用**：
  - Codex 讀取了真實的 `~/.agents/skills`（唯讀）。
  - 我讀了 `C:\ProgramData\OpenAI\Codex\requirements.toml` 的結構（管控設定，非憑證；內容為編碼過的 PowerShell 指令，未解碼）。
  - `codex exec` 向 `api.openai.com` 發了幾次未帶憑證的請求，全部 401。執行前已清掉 `OPENAI_API_KEY` / `CODEX_API_KEY` 環境變數。
  - sandbox 的 `codex-home` 多了 Codex 自己產生的 `sessions/`、`*.sqlite` 等檔。
  - `sandbox\proj\` 做過 `git init`（無 commit）。
  - 曾在 `%TEMP%\bingfa-hookprobe` 建過暫存資料夾，已刪除。
