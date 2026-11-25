# tools：維護人用的工具（不發給同事）

## 打包之前跑這一行

```
python tools/check_package.py
```

會印出 13 項檢查的表，每項是 PASS（通過）、FAIL（失敗）或 SKIPPED（沒辦法檢查）。
結束碼：0 全部通過、1 有失敗、2 沒有失敗但有跳過（跳過不算通過，要補跑）。
要檢查一份複本，加 `--root <複本資料夾>`。

## 發新版的步驟（三行）

先改好 `dev-bingfa/VERSION`、兩個 `plugin.json` 的版本號，並在 `dev-bingfa/更新紀錄.md` 最上面加這一版的紀錄（照檔案最後的範本），然後：

```
python tools/check_package.py
python tools/scan_package.py
python tools/build_zip.py
```

- 前兩行各自要印出 `PASS`（結束碼 0）。`build_zip.py` 會自己再跑一次這兩支，任何一支沒過就不打包。
- 打包結果在 `dist/`（不進 git）：`dev-bingfa-<版本>.zip`、`dev-bingfa-<版本>.sha256`（壓縮檔的指紋）、`dev-bingfa-<版本>-檔案清單.txt`（每個檔案的路徑、大小、指紋）。
- 壓縮檔裡**沒有**最上層資料夾：`安裝指示-ClaudeCode.md` 等檔案直接在壓縮檔的最外層。這樣同事用「解壓縮全部」時，Windows 預設建立的 `dev-bingfa-<版本>\` 資料夾裡就直接是這些檔案，和說明書寫的一樣。內容是 `dev-bingfa/` 底下的**工作中檔案**（不是 git 裡的版本），只排除暫存檔類（`__pycache__`、`.pyc`、`.gitkeep`、`Thumbs.db`、`.DS_Store`、`.bak` 等）。
- 同樣的內容重跑一次，壓縮檔會一模一樣（指紋相同）。要自己核對指紋：`certutil -hashfile dist\dev-bingfa-<版本>.zip SHA256`，和 `.sha256` 檔比。
- `scan_package.py` 找到東西時會列出檔案和行號。我們自己的檔案裡確定沒問題的，要寫進它最上面的 `JUSTIFIED` 清單並附理由；Matt Pocock 離線副本裡的命中只列出來參考，不算失敗。

## 每個工具做什麼

| 檔案 | 做什麼 |
|---|---|
| `check_package.py` | 一次跑完包裹的 13 項檢查（基本版和母本一樣、規則檔兩份相同、助手對得上、設定檔格式、換行、存檔檢查的行為等），會呼叫 `test-hooks.py` |
| `scan_package.py` | 掃 `dev-bingfa/` 全部檔案找個資和機密：使用者帳號名、信箱、`C:\Users\…` 這類個人路徑、金鑰或權杖樣式、測試殘留、公司內部識別字、被排除的工具名、暫存檔、超過 1 MB 的檔案。結束碼 0 沒找到、1 有找到 |
| `build_zip.py` | 先跑上面兩支檢查，都過了才把包裹打成 `dist/dev-bingfa-<版本>.zip`，另外寫指紋檔和檔案清單 |
| `test-hooks.py` | 照 Claude Code 和 Codex 的方式實際跑存檔檢查（有／沒有／太舊的 Python、各種輸入、300 個檔案），也可以單獨跑 |
| `check-agents.py` | 舊 PowerShell 版用的小幫手，內容已經併進 `check_package.py`，沒有人再呼叫它，可以刪掉 |
| `sync-basic.ps1` | 把母本的 skill 和 `規則/AGENTS.md` 複製到 `基本版/`。加 `-CheckOnly` 只比對不複製。`check_package.py` 不需要它，自己會比對 |

需要 Python 3.8 以上；「助手對得上」那一項要 Python 3.11 以上，版本不夠時會顯示 SKIPPED。

## 為什麼沒有 `check-package.ps1` 了

舊的 PowerShell 版檢查工具被公司的防毒軟體誤判成惡意程式擋下來，跑不起來。我們不去繞過防毒，改用這支 Python 版，檢查項目相同。
