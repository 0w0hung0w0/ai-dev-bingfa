# 規則資料夾

這裡有三種規則。外掛不會自動帶入規則檔，所以要自己複製貼上（詳細步驟見說明書）。

| 檔案 | 是什麼 | 給誰用 |
|---|---|---|
| `AGENTS.md` | 通用規則 | Codex、Cursor、Antigravity |
| `CLAUDE.md` | 通用規則（和 `AGENTS.md` 內容一模一樣，只是檔名不同） | Claude Code |
| `CLAUDE專用附錄.md` | 只有 Claude Code 才適用的補充 | Claude Code |
| `個人偏好範例.md` | 回覆語言、驗收方式、模型名稱等，自己改 | 所有工具 |

## 每個工具放哪裡

| 工具 | 放到哪個檔案 | 依序貼入 |
|---|---|---|
| Claude Code | `~/.claude/CLAUDE.md` | `CLAUDE.md` → `CLAUDE專用附錄.md` → 你改好的個人偏好 |
| Codex | `~/.codex/AGENTS.md` | `AGENTS.md` → 你改好的個人偏好 |
| Cursor、Antigravity（基本版，未實測） | 專案資料夾最上層的 `AGENTS.md` | `AGENTS.md` → 你改好的個人偏好 |

`~` 代表你的使用者資料夾（Windows 通常是 `C:\Users\你的帳號`）。如果那個檔案已經有內容，把新內容貼在最後面，不要蓋掉原本的。

## 注意

- `AGENTS.md` 和 `CLAUDE.md` 要保持一模一樣。改其中一份，另一份也要照改。
- Codex 讀規則檔有大小上限（預設 32 KiB，所有規則檔合計），貼太多東西可能會被截掉。
