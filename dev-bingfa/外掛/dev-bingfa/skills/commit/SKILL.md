---
name: commit
description: 檢視變更並建立 git commit。只在使用者明確要求提交（例如叫用本 skill、說「幫我 commit」）時使用，不要自己主動提交。
disable-model-invocation: true
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*)
---

建立一個 git commit:

1. 執行 `git status` 和 `git diff` 檢視目前的變更,並用 `git log --oneline -10` 了解本 repo 的 commit message 風格。
2. 只 stage 與本次工作相關的檔案,逐一寫出檔案路徑(`git add <路徑>`),不要用 `git add -A` 或 `git add .` 盲目全加,也不要用 `git commit -a` / `--all`(含 `-am`),它會把所有已追蹤的修改一起提交;無關的變更留在 working tree。
3. 撰寫符合該 repo 既有風格的 commit message(語言、格式、前綴都跟隨既有慣例),並建立 commit。
4. 若 working tree 沒有任何變更、或變更看起來混雜了多個不相關的主題,先回報並詢問,不要硬 commit。
5. 只 commit,不要 push。

使用者叫用時若附帶說明(例如只提交哪些檔案、訊息要強調什麼),照著做。
