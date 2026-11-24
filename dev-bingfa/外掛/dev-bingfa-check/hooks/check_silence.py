# -*- coding: utf-8 -*-
"""靜默失敗偵測 —— Claude Code 的 PostToolUse hook。

每次 AI 寫檔或改檔之後自動跑，掃剛動過的那一個檔案，
只抓一種東西：**廣泛捕捉例外之後什麼都不做**。

    except Exception:
        pass

抓到不擋、不中斷，只把訊息餵回給 AI，要它交代
「上游怎麼知道這一步失敗了、使用者在哪裡看得到」。

── 為什麼只抓這一種 ──────────────────────────────────────────
校準時拿一個 1.5 萬行的真實專案實測過：

  版本一（抓所有 `except 任何型別: pass`）→ 15 處，大多是誤報
      except OSError: pass        刪暫存檔失敗，合理
      except ValueError: pass     窄型別、局部解析，合理
      except LocateError: pass    測試在驗「該拋錯」，合理

  版本二（只抓廣泛捕捉）→ 7 處，訊噪比 2 真 : 5 假
      誤報全部來自兩種樣板：
        try: sys.stdout = io.TextIOWrapper(...)  except Exception: pass
        try: import 選用套件                      except Exception: pass

  版本三（本版：廣泛捕捉 + 排除上述兩種樣板 + 排除測試檔）→ 只剩真陽性

**訊噪比比覆蓋率重要。** 一個會誤報的 hook，兩天內就會被關掉，
那比沒有 hook 更糟——因為你以為有防護。寧可漏抓，不要吵。

── 維護原則 ──────────────────────────────────────────────
想加新的偵測項目之前，先拿真實專案跑一次，算訊噪比。
低於 3 真 : 1 假就不要加。
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

# 只看 Python。其他語言的等式不同，另外校準過再加。
_EXTS = {".py"}

# 測試檔裡「預期會拋錯」是正常寫法
_TEST_FILE = re.compile(r"(^|[\\/])(test_|conftest)")


def _err(text: str) -> None:
    """把訊息寫到 stderr，強制 UTF-8。

    Windows 的 sys.stderr 走系統編碼（繁中是 cp950），直接 print 中文會變亂碼，
    而 Claude Code 收到的就是那串亂碼。寫 bytes 才穩。
    """
    try:
        sys.stderr.buffer.write((text + "\n").encode("utf-8"))
        sys.stderr.buffer.flush()
    except Exception:  # noqa: BLE001
        print(text.encode("ascii", "replace").decode("ascii"), file=sys.stderr)


def _is_broad(handler: ast.ExceptHandler) -> bool:
    """這個 except 是不是「廣泛捕捉」（沒寫型別／Exception／BaseException）。"""
    t = handler.type
    if t is None:                                   # 裸 except:
        return True
    names = t.elts if isinstance(t, ast.Tuple) else [t]
    return any(isinstance(n, ast.Name) and n.id in ("Exception", "BaseException")
               for n in names)


def _is_guard_body(body: list) -> bool:
    """try 區塊是不是「整段只有 import／設定 stdout」的防呆樣板。

    ⚠️ 判準是**每一行都是**，不是「出現過」。校準時第一版寫成「含 import 就排除」，
       結果把真陽性一起濾掉了——
           try:
               from services import usage_tracker   ← 有 import
               usage_tracker.record(response, ...)  ← 但也真的在做事
           except Exception:
               pass
       這是「記帳失敗被吞掉」，要抓。而整段只有 `import pdfplumber` 才是選用套件防呆。
    """
    for stmt in body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(stmt, ast.Assign):
            tgt = stmt.targets[0] if stmt.targets else None
            if (isinstance(tgt, ast.Attribute) and tgt.attr in ("stdout", "stderr")
                    and isinstance(tgt.value, ast.Name) and tgt.value.id == "sys"):
                continue
        return False
    return bool(body)


def find_silent_excepts(source: str) -> list[tuple[int, str]]:
    """回傳 [(行號, 該行原文)]。行號從 1 起算。

    ⚠️ 用語法樹而不是正則掃文字。校準時的病歷：第一版用正則逐行比對，
       結果**抓到本檔 docstring 裡當範例寫的那段 `except Exception: pass`**。
       字串、註解、說明文件裡的程式碼片段都會被誤判——那是文字比對的通病。
       語法樹只看真正會執行的程式碼，這一類誤報自然消失。

    檔案語法不完整時（AI 寫到一半）解析會失敗，此時回空清單＝不打擾。
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    lines = source.splitlines()
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        if _is_guard_body(node.body):
            continue
        for h in node.handlers:
            if not _is_broad(h):
                continue
            if len(h.body) != 1 or not isinstance(h.body[0], ast.Pass):
                continue
            n = h.lineno
            text = lines[n - 1].strip() if 0 < n <= len(lines) else "except ...:"
            hits.append((n, text))
    return sorted(hits)


def main() -> int:
    # ⚠️ 病歷（校準時自己踩的，很諷刺）：
    #    第一版寫 `json.load(sys.stdin)`。Windows 的 stdin 預設用系統編碼
    #    （繁中是 cp950），路徑含中文時解碼失敗 → JSONDecodeError →
    #    被下面那個 except 靜默吞掉 → hook 每次都安靜地什麼都不做。
    #    **這個 hook 自己犯了它要抓的罪，而且完全看不出來。**
    #    改成讀 bytes 再顯式用 UTF-8 解。
    #    最外層的 except 保留（hook 絕不能變成擋路的東西），但吞掉之前先留痕跡。
    try:
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw.decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        _err(f"[check_silence] 讀取輸入失敗，略過本次檢查：{e}")
        return 0

    path = ((payload.get("tool_input") or {}).get("file_path")
            or (payload.get("tool_response") or {}).get("filePath") or "")
    if not path:
        return 0
    p = Path(path)
    if p.suffix.lower() not in _EXTS or _TEST_FILE.search(str(p)):
        return 0

    try:
        src = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:  # noqa: BLE001
        return 0

    hits = find_silent_excepts(src)
    if not hits:
        return 0

    where = "、".join(f"第 {n} 行" for n, _ in hits[:5])
    msg = (
        f"⚠️ 靜默失敗檢查：{p.name} 的 {where} 有「廣泛捕捉例外後什麼都不做」。\n\n"
        + "\n".join(f"    {n}: {t}" for n, t in hits[:5])
        + "\n\n請針對每一處說明：\n"
        "  1. 這裡吞掉例外之後，上游怎麼知道這一步失敗了？\n"
        "  2. 使用者在哪裡看得到？（寫進 log 不算）\n"
        "如果兩題都沒有答案，這就是靜默失敗，請改成至少留下痕跡"
        "（記錄到回傳結構、或縮小成具體的例外型別）。\n"
        "如果這裡確實應該吞掉，請在程式碼註解寫明理由。"
    )
    # ⚠️ 同一個編碼病歷的第二現場：Windows 的 stderr 也是系統編碼（繁中 cp950），
    #    直接 print 中文會變亂碼餵給 AI。顯式寫 UTF-8 bytes。
    _err(msg)
    return 2      # PostToolUse 的 exit 2 = 把 stderr 餵回給 AI，不中斷流程


if __name__ == "__main__":
    sys.exit(main())
