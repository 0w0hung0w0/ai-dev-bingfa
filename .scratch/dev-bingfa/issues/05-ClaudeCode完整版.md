# 05 Claude Code 完整版

依賴：02、03、04

## 目的

把所有東西包成 Claude Code 的外掛，同事可以從本地資料夾安裝，不需要 GitHub。

## 要做什麼

- 建立外掛（`.claude-plugin/plugin.json`），內含：
  - 03 的三個 skill。
  - 三個助手設定：`explorer`、`implementer`、`web-search-agent`（含 `web-search-modules/`）。拿掉外掛會忽略的欄位（`permissionMode`、`hooks`、`mcpServers`、`initialPrompt`），並確認拿掉後行為沒有少掉關鍵限制；模型名稱的處理與 04 的「個人偏好」一致。
  - 提交指令 `commit`。
  - 檢查腳本 `check_silence.py`，做成**選用**：沒有 Python 就跳過，而且要讓使用者明確看到「這項沒啟用」，不能靜悄悄失效。
- 規則無法由外掛帶入：準備好讓使用者手動貼上的 `CLAUDE.md`（通用＋Claude 附錄），貼上步驟留給 09 寫。
- 在本機用不影響 `~/.claude` 的方式做一次冒煙測試（例如暫時指定另一個設定資料夾）。

## 不做什麼

- 不修改使用者的 `~/.claude`，不把使用者的環境換成包裹版。
- 不寫說明書（09）。正式的乾淨環境實裝是 12。
- 不放 Matt 的工具（走官方安裝）。

## 完成的樣子

- 在隔離的設定下裝上外掛後，畫面上看得到：三個 skill、三個助手、`/commit` 指令都出現在清單裡（附畫面或指令輸出）。
- 有 Python 時檢查腳本會動；沒有 Python 時看得到「這項沒啟用」的訊息——兩種情況各一份證據。
- `~/.claude` 沒被改到：附做之前與之後的檔案清單比對。
