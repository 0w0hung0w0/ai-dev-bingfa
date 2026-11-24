# tools：維護人用的工具（不發給同事）

## 打包之前跑這一行

```
python tools/check_package.py
```

會印出 13 項檢查的表，每項是 PASS（通過）、FAIL（失敗）或 SKIPPED（沒辦法檢查）。
結束碼：0 全部通過、1 有失敗、2 沒有失敗但有跳過（跳過不算通過，要補跑）。
要檢查一份複本，加 `--root <複本資料夾>`。

## 每個工具做什麼

| 檔案 | 做什麼 |
|---|---|
| `check_package.py` | 一次跑完包裹的 13 項檢查（基本版和母本一樣、規則檔兩份相同、助手對得上、設定檔格式、換行、存檔檢查的行為等），會呼叫 `test-hooks.py` |
| `test-hooks.py` | 照 Claude Code 和 Codex 的方式實際跑存檔檢查（有／沒有／太舊的 Python、各種輸入、300 個檔案），也可以單獨跑 |
| `check-agents.py` | 舊 PowerShell 版用的小幫手，內容已經併進 `check_package.py`，沒有人再呼叫它，可以刪掉 |
| `sync-basic.ps1` | 把母本的 skill 和 `規則/AGENTS.md` 複製到 `基本版/`。加 `-CheckOnly` 只比對不複製。`check_package.py` 不需要它，自己會比對 |

需要 Python 3.8 以上；「助手對得上」那一項要 Python 3.11 以上，版本不夠時會顯示 SKIPPED。

## 為什麼沒有 `check-package.ps1` 了

舊的 PowerShell 版檢查工具被公司的防毒軟體誤判成惡意程式擋下來，跑不起來。我們不去繞過防毒，改用這支 Python 版，檢查項目相同。
