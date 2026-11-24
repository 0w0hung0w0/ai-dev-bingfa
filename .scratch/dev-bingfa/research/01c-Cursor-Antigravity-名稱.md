# 研究報告 01c:Cursor / Antigravity / 名稱查重 / npx skills(2026-11-24)

方法備註:
- WebFetch 回傳的是「小模型對頁面的摘要」,引文可能經過轉述,非逐字原頁文字;下文標「[fetch]」。
- WebSearch 回傳的是模型生成的搜尋摘要,標「[search 摘要]」,可信度低於 fetch 到的頁面。
- 以下「未確認」代表我沒有取得一手證據,不從記憶補。

---

## Q1. Cursor 是否每次 agent 對話都自動納入專案根目錄 AGENTS.md?

結論:官方文件只說可把 AGENTS.md 放在專案根目錄,作為 `.cursor/rules` 的簡易替代;「是否每次對話一定載入根目錄 AGENTS.md」文件沒有明說,故未確認。巢狀 AGENTS.md 的行為有明文。

- 證據 URL:https://cursor.com/docs/context/rules (另試 https://cursor.com/docs/rules 同內容;/docs/context/rules.md 回 404)
- 引文 [fetch]:"Place it in your project root as an alternative to `.cursor/rules` for straightforward use cases."
- 巢狀 [fetch]:巢狀檔 "will be automatically applied when working with files in that directory or its children."
- 優先序 [fetch]:"Instructions from nested AGENTS.md files are combined with parent directories, with more specific instructions taking precedence."
- 大小限制:頁面未提 AGENTS.md 的大小上限;只有一般規則的「Keep rules under 500 lines」建議,不專屬 AGENTS.md。
- 信心:根目錄「每次必載入」=未確認;巢狀規則=中高(兩次 fetch 一致,但為摘要)。

## Q2. Cursor 的 Agent Skills 搜尋路徑;是否讀 .claude/agents?

結論:Cursor 讀 `.agents/skills/`、`.cursor/skills/`(專案)與 `~/.agents/skills/`、`~/.cursor/skills/`(使用者層),另為相容也讀 `.claude/skills/`、`.codex/skills/` 及其 `~/` 版本;子代理(subagents)則會讀 `.claude/agents/`。

- Skills 證據:https://cursor.com/docs/context/skills
  - [fetch] 四個原生位置:`.agents/skills/`、`.cursor/skills/`、`~/.agents/skills/`、`~/.cursor/skills/`。
  - 引文 [fetch]:"For compatibility, Cursor also loads skills from Claude and Codex directories" — 列出 `.claude/skills/`、`.codex/skills/`、`~/.claude/skills/`、`~/.codex/skills/`。
  - 信心:高(以 fetch 摘要為據,未見逐字原頁)。
- Subagents 證據:https://cursor.com/docs/subagents
  - [fetch] 專案:`.cursor/agents/`、`.claude/agents/`、`.grok/agents/`;使用者:`~/.cursor/agents/`、`~/.claude/agents/`、`~/.grok/agents/`。
  - 引文 [fetch]:"When multiple locations contain subagents with the same name, `.cursor/` takes precedence over `.claude/` or `.grok/`."
  - 引文 [fetch]:"The CLI and hosted Cloud Agents don't read subagents from your home folder."(使用者層子代理只在編輯器與自架 worker 載入)
  - `.grok/` 路徑需啟用 "Include Third-Party Plugins, Skills, and Other Configs"。
  - 文件未提 `.codex/agents/`,故該路徑未確認。
  - 信心:中高。
- 注意:skills 頁本身沒談 `.claude/agents`;那是在 subagents 頁。

## Q3. Google Antigravity:skills / AGENTS.md / GEMINI.md / rules

結論:專案層 skills 讀 `<workspace>/.agents/skills/`(舊的 `.agent/skills` 仍相容);全域層依最新文件為 `~/.gemini/config/skills/`,CLI 另有 `~/.gemini/antigravity-cli/skills/`;舊文件寫 `~/.gemini/antigravity/skills/`。規則面讀 `AGENTS.md`、`GEMINI.md`、`.agents/rules/`。

### 頁面載入狀況(誠實清單)
| 頁面 | 結果 |
|---|---|
| https://codelabs.developers.google.com/getting-started-with-antigravity-skills | 成功載入 [fetch] |
| https://antigravity.google/docs | 失敗:Socket is closed |
| https://antigravity.google/docs/skills | 失敗:Socket is closed |
| https://antigravity.google/docs/skills.md | 失敗:Socket is closed |
| https://antigravity.google/docs/skills?tab=ide | 失敗:Socket is closed |
| https://www.antigravity.google/docs/ide/skills | 失敗:Socket is closed |
| https://antigravity.google/docs/rules-workflows | 失敗:Socket is closed |
| https://antigravity.google/docs/rules-workflows.md | 失敗:Socket is closed |
| https://antigravity.google/docs/rules-workflows?tab=ide | 失敗:Socket is closed |

所以 antigravity.google/docs 官方站我「一頁都沒讀到」;下列官方站內容全部來自 WebSearch 摘要(搜尋結果有列出這些官方 URL,但摘要由搜尋模型生成),僅 codelab 為實際載入。

### Skills 路徑
- Codelab(https://codelabs.developers.google.com/getting-started-with-antigravity-skills)[fetch]:
  - 工作區:`"<project-root>/.agents/skills/"`
  - 全域:`"~/.gemini/config/skills/"`(跨所有 Antigravity 產品與專案)
  - CLI 全域:`"~/.gemini/antigravity-cli/skills/"`
  - 其他:用 `npx skills` 或 `agents-cli` 安裝的 skills 會到 `"~/.agents/skills"`;codelab 稱 Antigravity(App)會讀,Antigravity CLI 不會讀。
- [search 摘要] 官方 docs:預設 `.agents/skills`,向下相容 `.agent/skills`;會讀各層父資料夾到 repo 根的 `.agents/skills/`;CLI 也讀 `~/.gemini/skills/`(App 不讀)。

### 全域 skills 路徑的衝突說法
1. `~/.gemini/config/skills/` — codelab [fetch] 與 vercel-labs/skills 的 docs/agents.md [fetch](`antigravity` 的 global 欄)皆如此(新)。
2. `~/.gemini/antigravity/skills/` — [search 摘要]稱較舊的 Google IDE 文件如此寫;另一版文件稱此 legacy 路徑仍支援。
3. `~/.gemini/antigravity-cli/skills/` — CLI 專用(codelab [fetch])。
4. `~/.gemini/skills/` — 僅 CLI 讀([search 摘要])。
5. `~/.agents/skills` — npx skills 的落點;codelab [fetch] 說 App 讀、CLI 不讀。
- 信心:`.agents/skills`(專案)=中高;全域 `~/.gemini/config/skills/`=中高(兩個獨立來源一致);其餘路徑=低到中。

### AGENTS.md / GEMINI.md / rules
- [search 摘要,官方 URL 有列出:https://www.antigravity.google/docs/rules-workflows 、 https://antigravity.google/docs/rules.md 、 https://antigravity.google/docs/customization-discovery/ ,但我未能 fetch]:
  - 工作區(及各父資料夾至 repo 根)可放 `AGENTS.md`、`GEMINI.md` 或 `.agents/rules/`;`.agents/rules/` 只掃直接子層 `.md`;舊 `.agent/rules/` 仍支援。
  - 全域:`~/.gemini/AGENTS.md`、`~/.gemini/GEMINI.md`、`~/.gemini/config/AGENTS.md`、`~/.gemini/config/GEMINI.md`,或 `~/.gemini/config/rules/*.md`(需 YAML frontmatter)。
  - 第三方稱 GEMINI.md 與 AGENTS.md 衝突時 GEMINI.md 優先(非官方,未驗證)。
- 信心:低到中(僅搜尋摘要,官方頁未讀到)。

## Q4. 「AI 系統開發兵法」或近似名稱是否已存在?

結論:未找到同名或近似名(「AI 開發兵法」「AI 兵法」作為軟體開發方法論的書/課程/產品/知名 repo)的書籍、課程或產品;也無法以博客來/Google Books 直接搜尋驗證(兩者 fetch 失敗)。

搜尋過的查詢與結果:
1. WebSearch `「AI 系統開發兵法」`:無同名結果;最近似為 iThome「AI 協作開發的規範」SOP 文章(https://ithelp.ithome.com.tw/articles/10418802 ,由搜尋摘要得知,我未讀全文)等,皆非同名。
2. WebSearch `AI系统开发兵法 OR "AI 開發兵法" OR "AI 编程兵法" 书 课程`(簡體):無同名;近似為 Udemy《14 Days to Building AI Systems & Agents》、O'Reilly 中文版《AI工程》(Chip Huyen)。
3. WebSearch `博客來 天瓏 "AI 兵法" 軟體開發 書`:無「AI 兵法」書;天瓏 AI Coding 分類頁(https://www.tenlong.com.tw/categories/ai-coding)有多本相關書,如《Claude Code Vibe Coding 開發手冊》,皆非「兵法」。
4. WebSearch `"AI 開發兵法" OR "AI 系統開發" 兵法 GitHub 方法論 spec-driven skills`:無同名;結果多為 GitHub Spec Kit(https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)。
5. GitHub API 搜尋 repositories `AI系統開發兵法`:total_count 1,結果 `Dujltqzv/Some-Many-Books`(看似書單類 repo,我沒查證其內容是否含該名稱;code search 需認證回 401)。
6. GitHub API 搜尋 `AI 兵法 in:name,description,readme`:410 筆,前 10 筆多為孫子兵法 skill 包(如 qbdx-hub/sunzi-bingfa-skill、AI-Nate/miaosuan),非軟體開發方法論;只讀了前 100000 字元中的前 10 筆,其餘未讀。
7. 博客來搜尋頁 https://search.books.com.tw/search/query/key/AI%E7%B3%BB%E7%B5%B1%E9%96%8B%E7%99%BC%E5%85%B5%E6%B3%95/cat/all:fetch 失敗(socket hang up)→ 博客來直接查詢「未確認」。
8. Google Books feed:fetch 失敗(socket hang up)→ Google Books「未確認」。
- 天瓏:僅經由 WebSearch 的分類頁,未做站內關鍵字搜尋。
- 信心:低到中(「找不到」,但關鍵站台未能直查)。建議使用者自行在博客來/天瓏站內搜尋一次。

## Q5. `npx skills`(vercel-labs/skills)

結論:Cursor 的 `-a` 識別字為 `cursor`,Antigravity 為 `antigravity`(另有 `antigravity-cli`);兩者專案層皆裝到 `.agents/skills/`;全域層 Cursor 為 `~/.cursor/skills/`,Antigravity 為 `~/.gemini/config/skills/`;Node 最低 22.20。

- 證據 URL:https://raw.githubusercontent.com/vercel-labs/skills/main/docs/agents.md [fetch,僅取得兩列]
  - "Cursor | `cursor` | `.agents/skills/` | `~/.cursor/skills/`"
  - "Antigravity, Antigravity CLI | `antigravity`, `antigravity-cli` | `.agents/skills/` | `~/.gemini/config/skills/`"
  - 信心:中高(欄位順序推定為 名稱|-a id|專案路徑|全域路徑,fetch 摘要未明列表頭)。
  - 未確認:`antigravity-cli` 的全域路徑是否與 `antigravity` 相同(該列合併;codelab 說 CLI 另有 `~/.gemini/antigravity-cli/skills/`),以及 `-g` 是否對應該全域欄(README 說 "Skills are installed to the current project by default; add `-g` to make them available across projects.")。
- Node 版本:https://github.com/vercel-labs/skills 引文 "Requires Node.js 22.20 or later."(fetch);https://raw.githubusercontent.com/vercel-labs/skills/main/package.json 為 `"engines": {"node": ">=22.20.0"}`,version 1.9.0。信心:高。
- README 稱 "Supports OpenCode, Claude Code, Codex, Cursor, and [75 more]";README 未描述 `-a` 選項,僅示例 `-a claude-code`。
- 與 Q3 的交叉:codelab 說 npx skills 裝到 `~/.agents/skills` 且 Antigravity CLI 不讀;但 agents.md 說 antigravity 全域為 `~/.gemini/config/skills/`。兩說法並存,實際落點未實測,未確認。

---

## Sources and References
1. https://cursor.com/docs/context/rules
2. https://cursor.com/docs/rules
3. https://cursor.com/docs/context/skills
4. https://cursor.com/docs/subagents
5. https://codelabs.developers.google.com/getting-started-with-antigravity-skills
6. https://antigravity.google/docs/skills(僅搜尋結果,fetch 失敗)
7. https://www.antigravity.google/docs/rules-workflows(僅搜尋結果,fetch 失敗)
8. https://github.com/vercel-labs/skills
9. https://raw.githubusercontent.com/vercel-labs/skills/main/docs/agents.md
10. https://raw.githubusercontent.com/vercel-labs/skills/main/README.md
11. https://raw.githubusercontent.com/vercel-labs/skills/main/package.json
12. https://www.tenlong.com.tw/categories/ai-coding
13. https://ithelp.ithome.com.tw/articles/10418802
14. https://api.github.com/search/repositories?q=AI+%E5%85%B5%E6%B3%95+in:name,description,readme
