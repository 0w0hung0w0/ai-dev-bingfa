# dev-bingfa-check（選用：存檔時自動檢查）

## 它檢查什麼

每次 AI 寫好或改好一個檔案，這個外掛會自動看一下剛動過的那個檔案。目前只抓一種問題：

> Python 程式裡「出錯了就整個吞掉、什麼都不做」的寫法（例如 `except Exception: pass`）。

這種寫法會讓程式壞掉時沒有人知道。抓到時它**不會擋住**工作，只會提醒 AI 說明「出錯時上游怎麼知道、使用者在哪裡看得到」。

只檢查 `.py` 檔；測試檔（`test_` 開頭、`conftest`）不檢查。

## 需要什麼

需要電腦上有可以用的 **Python 3.8 以上**。真的能執行、而且版本夠新才算數：Windows 內建那個「叫你去 Microsoft Store 安裝」的假 python 不算，Python 2 或 3.7 以前的舊版也不算（都會當成「沒有 Python」，開對話時出現「這項沒啟用」提示）。

找 Python 的順序：

- macOS、Linux、Windows 有 Git Bash（`hooks/run.sh`）：`python3` → `python` → `py -3`
- Windows 沒有 Git Bash，或 Codex 在 Windows（`hooks/run.cmd`）：`py -3` → `python` → `python3`

## 安裝（完整步驟看說明書）

先裝好主外掛的 marketplace，再打：

```
claude plugin install dev-bingfa-check@dev-bingfa
```

## 怎麼知道它有沒有在動

- **沒有 Python**：每次開新對話時，畫面上會出現一行提示：
  「dev-bingfa-check：存檔自動檢查「這項沒啟用」——這台電腦找不到 Python。」
  其他功能照常能用，存檔時不會一直跳錯誤。要啟用就先裝 Python 3，再重新開啟對話。
- **有 Python**：開對話時**不會**有任何提示（安靜就是正常）。想親眼確認，可以請 AI 寫一個含有 `except Exception: pass` 的小 `.py` 檔，應該會看到「靜默失敗檢查」的提醒。
- 在終端機打 `claude plugin list`，看到 `dev-bingfa-check@dev-bingfa` 是啟用狀態，代表外掛有裝上。

## 支援的電腦

| 電腦 | 狀況 |
|---|---|
| Windows，有裝 Git（Claude Code 用 Git Bash 跑） | 用 `hooks/run.sh` |
| Windows，沒裝 Git（Claude Code 改用 PowerShell 跑） | 用 `hooks/run.cmd` |
| macOS、Linux | 用 `hooks/run.sh` |

同一行設定在兩種環境都能跑，不用自己改。macOS、Linux 這條路只在 Windows 的 Git Bash 上模擬過，沒有在真的 Mac 上測。

不管走哪一條，最後都是 `hooks/post_check.py` 先看懂輸入、再交給 `check_silence.py`。檢查程式自己出錯或看不懂輸入時，一律安靜跳過，不會讓對話出錯；只有真的抓到問題才會提醒。

## Codex

Codex 也能裝這個外掛：`codex plugin add dev-bingfa-check@dev-bingfa`。狀態：**未實測成功**。

- Codex 的外掛 hook 要你自己在 Codex 裡打 `/hooks`，檢視後按「信任」才會跑；外掛更新後要重新信任。
- Windows 上 Codex 用 `hooks/codex-post.cmd`；macOS、Linux 上用 `hooks/run.sh`。兩條路都只在這台 Windows 電腦上照 Codex 的執行方式模擬過，沒有在 Codex 對話裡真的觸發過。
- 沒把握它有沒有在跑時，就用手動做法：每次交付前，照 `codex/README.md`「存檔檢查的手動替代做法」那一句，請 AI 自己檢查一次。

## 檔案

- `hooks/hooks.json`：告訴 Claude Code／Codex 什麼時候跑（開對話時、寫檔或改檔後）。
- `hooks/run.sh`、`hooks/run.cmd`：找 Python 的小程式。`hooks/codex-post.cmd`：Codex 在 Windows 用的入口，內容等於 `run.cmd post`。
- `hooks/post_check.py`：唯一的檢查入口，分辨 Claude Code 和 Codex 的輸入，找出剛寫好的檔案。
- `hooks/check_silence.py`：真正做檢查的腳本（原樣沿用，沒有修改）。
- `hooks/no-python.json`：「這項沒啟用」提示的內容。
