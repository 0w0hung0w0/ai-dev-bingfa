# 03 整理三個補充 skill

依賴：01、02

## 目的

把「既有專案探勘」「影響範圍檢查」「接縫對帳」三個 skill 整理成可以發給同事的版本。

## 要做什麼

- 從 `~/.claude/skills/` 複製 `brownfield-recon`、`blast-radius`、`seam-audit` 到包裹（來源只讀不改）。
- 改 `brownfield-recon`：不再自己記專有名詞（拿掉 `CONTEXT_MAP.md` 的 Language／名詞區），只產出專案地圖；需要記名詞時指向 `GLOSSARY.md`。
- 依 01 找到的懸空引用清單，把指向被排除工具（`guardrail-spec`、`work-order`、`diff-review`、專利類）的地方改成指向 Matt 主線的對應步驟，或刪除。
- 檢查三個 skill 的內容沒有個人資料、個人路徑、公司內部資訊。
- 確認 skill 格式在 Claude Code 與 Codex 都能被讀到（依 01 的結論）。

## 不做什麼

- 不改三個 skill 的核心做法（只改名詞區、懸空引用、個資）。
- 不把 Matt 的 skill 放進來（那是 08）。
- 不動 `~/.claude` 的原檔。

## 完成的樣子

- 一份前後對照表：每個 skill 改了哪幾處、為什麼改（白話）。
- 搜尋整個包裹，找不到被排除工具的名稱，也找不到「Language 節」這類說法——附搜尋指令與「零筆結果」的輸出。
- 搜尋不到使用者的姓名、信箱、個人路徑。

註：`commit` skill（原屬卡 05）實際在本卡一併做了，見 `../evidence/03-前後對照.md`。
