# 個人偏好範例（Codex 版）

**貼在哪裡**：`~/.codex/AGENTS.md`，放在 `<!-- dev-bingfa:end -->` 那一行的下面（用 `安裝指示-Codex.md` 安裝時，第一次會自動放好，之後重裝不會再動它）。
`~/` 代表你的使用者資料夾（Windows 通常是 `C:\Users\你的帳號`）。Claude Code 請用 `個人偏好範例.md`。

## 怎麼改

- 可以改的地方都用 【請改：…】 標出來。把整個 【請改：…】（連括號一起）換成你自己的寫法就好，不需要懂程式。例如 `【請改：繁體中文】` 改成 `English`。（自動安裝時會先換成括號裡的預設值。）
- 沒有 【請改：…】 的句子可以照用，也可以直接改那一行的中文句子。
- 不想要的項目整行刪掉即可；刪掉後 AI 會照通用規則的預設做。
- 改完存檔，**開一個新的對話**才會生效。
- 注意：個人偏好只能調整語言、長短、驗收方式和模型；不能取消通用規則 §7 要求的回報（漏了什麼、放棄了什麼、猜了什麼、在哪裡看得到）。

---（從這裡開始複製）---

## Personal Preferences

These override the common rules where they say "follow your personal preferences". They never waive the reporting duties of §7 (what was missed, given up on, guessed at, and where the user can see each).

### Reply language

- 一律用【請改：繁體中文】回覆。檔案路徑、指令、程式碼、引用原文保持原樣，不要翻譯。

### Brevity

- 回覆要簡短，先講結論。但 §7 要求的回報不能省。

### How I verify results

- 我不會讀程式碼。交付時請給我看得到的證據：實際畫面、執行結果、改動前後對照，或我可以自己照做一次的步驟。
- 只說「已經改好了」不算交付；要說明我去哪裡、做什麼、看到什麼，才算成功。

### Models per role

- 主對話（規劃與審查）與一般實作：【請改：用 Codex 模型選單裡較強的那個】
- 機械式小修改、簡單查找：【請改：用較快的那個】
- 沒有填就照通用規則的預設。
