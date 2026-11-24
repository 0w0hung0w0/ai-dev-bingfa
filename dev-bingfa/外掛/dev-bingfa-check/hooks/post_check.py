# -*- coding: utf-8 -*-
"""存檔檢查的唯一入口：Claude Code 和 Codex、每種作業系統都走這支。

    run.sh post / run.cmd post / codex-post.cmd  →  post_check.py  →  check_silence.py（原封不動）

為什麼需要：兩個工具給 hook 的輸入長得不一樣。
- Claude Code：{"tool_input": {"file_path": "..."}, "tool_response": {"filePath": "..."}}
- Codex：改檔工具叫 `apply_patch`，沒有 file_path，整段修補內容在 `tool_input.command`
      {"tool_name": "apply_patch", "cwd": "...", "tool_input": {"command": "*** Begin Patch\\n*** Update File: a.py\\n..."},
       "tool_response": "Success. ..."}
  `tool_response` 是字串，直接餵給 check_silence.py 會讓它當掉（AttributeError，結束碼 1）。
這支先看輸入是哪一種，找出被寫到的檔案，只留下 check_silence.py 真的會檢查的那些
（存在的 `.py`、不是測試檔，判準直接取自 check_silence.py），再一個一個用 Claude 的樣子
{"tool_input": {"file_path": 路徑}} 交給 check_silence.py 的 main()；任何一個回傳 2 就整體回傳 2，
並把警告原樣轉出去。

為什麼在同一個程序裡叫 main()，不是每個檔案另開一個 Python：hook 有 10 秒逾時，
一次修補 300 個檔案時每檔開一個程序會超時（審查 S2：12.6 秒）。check_silence.py 本身不改，
這裡只是在呼叫前暫時換掉 sys.stdin／sys.stderr，結果和直接執行它一樣。

約定（檢查程式絕不能弄壞使用者的對話）：
- 真的抓到問題 → 結束碼 2，stderr 是 check_silence.py 的警告。
- 其他任何情況（看不懂的輸入、JSON 壞掉、找不到檔案、這支或 check_silence.py 自己出錯）→ 結束碼 0，不輸出。

依據：https://learn.chatgpt.com/docs/hooks（apply_patch 的內容在 tool_input.command）。
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

_CHECK = Path(__file__).with_name("check_silence.py")
# apply_patch 的檔頭：新增、修改、改名後的新位置（刪除的檔案不用查）
_HEADERS = ("*** Add File: ", "*** Update File: ", "*** Move to: ")


def written_files(payload: object) -> list[str]:
    """回傳這次被寫到的檔案路徑（去重、保留順序）。看不懂的輸入回空清單。"""
    if not isinstance(payload, dict):
        return []
    tool_input = payload.get("tool_input")
    # Claude Code 的樣子：照用，不做任何轉換（和直接跑 check_silence.py 的結果一樣）
    if isinstance(tool_input, dict) and isinstance(tool_input.get("file_path"), str) \
            and tool_input["file_path"]:
        return [tool_input["file_path"]]
    tool_response = payload.get("tool_response")
    if isinstance(tool_response, dict) and isinstance(tool_response.get("filePath"), str) \
            and tool_response["filePath"]:
        return [tool_response["filePath"]]
    # Codex apply_patch 的樣子
    if isinstance(tool_input, dict):
        patch = tool_input.get("command") or tool_input.get("patch") or ""
    else:
        patch = tool_input if isinstance(tool_input, str) else ""
    if not isinstance(patch, str):
        return []
    cwd = payload.get("cwd")
    cwd = Path(cwd) if isinstance(cwd, str) and cwd else Path(".")
    out: list[str] = []
    for line in patch.splitlines():
        for h in _HEADERS:
            if line.startswith(h):
                p = Path(line[len(h):].strip())
                p = p if p.is_absolute() else cwd / p
                if str(p) not in out:
                    out.append(str(p))
    return out


def _load_checker():
    """把 check_silence.py 當模組載入（不寫 __pycache__ 到外掛資料夾裡）。"""
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("check_silence", _CHECK)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_one(checker, path: str) -> tuple[int, bytes]:
    """等於 `python check_silence.py < {"tool_input": {"file_path": path}}`：回傳（結束碼, stderr 位元組）。"""
    sub = json.dumps({"tool_input": {"file_path": path}}, ensure_ascii=False).encode("utf-8")
    old_in, old_err = sys.stdin, sys.stderr
    sys.stdin = io.TextIOWrapper(io.BytesIO(sub), encoding="utf-8")
    sys.stderr = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        code = checker.main()
        sys.stderr.flush()
        return code, sys.stderr.buffer.getvalue()
    except Exception:  # noqa: BLE001
        # 和以前「另開程序、當掉就回 1」一樣：這一個檔案略過，其他檔案照查（約定見檔頭）。
        return 1, b""
    finally:
        sys.stdin, sys.stderr = old_in, old_err


def main() -> int:
    # utf-8-sig：輸入前面如果有 BOM 也照讀（審查 Nit 5）。
    payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig", "replace"))
    paths = written_files(payload)
    if not paths:
        return 0
    checker = _load_checker()
    worst = 0
    for path in paths:
        p = Path(path)
        # 和 check_silence.py 的 main() 同一個判準，先篩掉它本來就會跳過的檔案
        if p.suffix.lower() not in checker._EXTS or checker._TEST_FILE.search(str(p)) or not p.is_file():
            continue
        code, err = _run_one(checker, path)
        if code == 2 and err:
            sys.stderr.buffer.write(err)
            sys.stderr.buffer.flush()
            worst = 2
    return worst


if __name__ == "__main__":
    try:
        code = main()
    except Exception:  # noqa: BLE001
        # 刻意吞掉：這支是檢查工具，自己出錯時不能讓使用者的對話跟著失敗（約定見檔頭）。
        # 使用者看得到的地方：README「怎麼知道它有沒有在動」的自我測試——寫一個有問題的 .py 卻沒看到提醒，就代表沒在動。
        code = 0
    sys.exit(code)
