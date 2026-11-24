#!/bin/sh
# dev-bingfa-check 啟動器（macOS / Linux / Windows Git Bash）
# 用法：sh run.sh post     → 有 Python 就跑 post_check.py（它再叫 check_silence.py）；沒有就安靜跳過
#       sh run.sh session  → 沒有 Python 時印出「這項沒啟用」的提示（每個對話開頭一次）
# Claude Code 和 Codex（非 Windows）都走這支；post_check.py 自己分辨兩種輸入。
# 結束碼只有兩種：2 = 抓到問題（警告在 stderr）；其他一律 0，檢查程式出錯也不能弄壞對話。
here=$(dirname "$0")

# 真的執行一次才算數：Windows 的 Microsoft Store 假 python 會回傳非 0，不會被當成有 Python。
# 版本太舊（Python 2、3.7 以前）也當成沒有 Python：檢查程式需要 3.8 以上，開對話時就會出現「這項沒啟用」提示。
py=""
for cand in python3 python "py -3"; do
  if $cand -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then py=$cand; break; fi
done

if [ "$1" = "session" ]; then
  [ -z "$py" ] && cat "$here/no-python.json"
  exit 0
fi

[ -z "$py" ] && exit 0
$py "$here/post_check.py"
[ $? -eq 2 ] && exit 2
exit 0
