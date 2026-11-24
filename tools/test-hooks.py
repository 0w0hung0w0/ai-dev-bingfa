# -*- coding: utf-8 -*-
"""Behaviour test for dev-bingfa-check (maintainer tool; not shipped to colleagues).

Invariant guarded here:
  With a working Python 3.8+, a write that contains a silent `except: pass` ends with exit 2 and the
  warning on stderr; every other input ends with exit 0 and no output at all. Without a usable
  Python (none, Microsoft Store stub, or too old), saving is silent (exit 0) and session start
  always prints the "not enabled" notice.

It runs hooks/hooks.json the way each tool does:
  claude-sh   Claude Code with Git Bash: `command` via sh -c (${CLAUDE_PLUGIN_ROOT} -> forward slashes)
  claude-ps   Claude Code without Git Bash: `command` via powershell -EncodedCommand (backslashes)
  claude-ps-env  same, but ${CLAUDE_PLUGIN_ROOT} NOT substituted (falls back to $env:CLAUDE_PLUGIN_ROOT)
  codex-cmd   Codex on Windows: `commandWindows` via %COMSPEC% /C "<cmd>"
  codex-sh    Codex on macOS/Linux: `command` via sh -c (simulated with Git's sh)
Python modes: yes (this PATH) / no (Store-like stub only) / old (a python that reports 2.7).
Everything is built in a fresh folder under the system temp dir whose path has spaces and Chinese.

Usage:  python tools/test-hooks.py [plugin_root]
Last line is machine-readable (ASCII):  SUMMARY|PASS|... , SUMMARY|FAIL|... or SUMMARY|SKIPPED|...
Exit code: 0 = all pass, 1 = at least one failure, 2 = skipped (no Git sh / not Windows).
"""
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROOT = REPO / "dev-bingfa" / (chr(0x5916) + chr(0x639B)) / "dev-bingfa-check"
TIMEOUT_LIMIT = 10.0  # hooks.json "timeout"


def skip(why):
    print("SUMMARY|SKIPPED|" + why)
    sys.exit(2)


if os.name != "nt":
    skip("this matrix drives cmd.exe / PowerShell / Git sh and needs Windows")


def find_git_sh():
    if os.environ.get("GIT_SH") and Path(os.environ["GIT_SH"]).is_file():
        return Path(os.environ["GIT_SH"])
    git = shutil.which("git")
    cands = []
    if git:
        g = Path(git).resolve()
        cands += [g.parent.parent / "usr" / "bin" / "sh.exe", g.parent.parent.parent / "usr" / "bin" / "sh.exe"]
    cands.append(Path(r"C:\Program Files\Git\usr\bin\sh.exe"))
    for c in cands:
        if c.is_file():
            return c
    return None


SH = find_git_sh()
if SH is None:
    skip("Git's sh.exe not found (set GIT_SH to its path)")
GIT_USR_BIN = str(SH.parent)
SYSROOT = os.environ.get("SYSTEMROOT", r"C:\Windows")
PS = os.path.join(SYSROOT, r"System32\WindowsPowerShell\v1.0\powershell.exe")
COMSPEC = os.environ.get("COMSPEC", os.path.join(SYSROOT, r"System32\cmd.exe"))

src_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_ROOT
tmp = Path(tempfile.mkdtemp(prefix="dev-bingfa-hooktest-"))
base = tmp / "路徑 測試 空白"
root = base / "my plugin" / "dev-bingfa-check"
proj = base / "專案 資料夾"
shutil.copytree(src_root, root, ignore=shutil.ignore_patterns("__pycache__"))

BAD = "def f():\n    try:\n        g()\n    except Exception:\n        pass\n"
GOOD = "def f():\n    return 1\n"
src = proj / "src"
(src / "子 資料夾").mkdir(parents=True)
(src / "many").mkdir()
for name, body in (("bad.py", BAD), ("good.py", GOOD), ("子 資料夾/my bad 檔.py", BAD),
                   ("test_bad.py", BAD)):
    (src / name).write_text(body, encoding="utf-8")
for i in range(300):
    (src / "many" / f"m{i}.py").write_text(GOOD, encoding="utf-8")

# --- fake Pythons -------------------------------------------------------------------------
stub_no = base / "stub-no"
stub_old = base / "stub-old"
stub_no.mkdir()
stub_old.mkdir()
for n in ("python", "python3"):
    (stub_no / (n + ".cmd")).write_text(
        "@echo Python was not found but can be installed from the Microsoft Store 1>&2\r\n@exit /b 9009\r\n",
        encoding="ascii")
    (stub_no / n).write_bytes(b'#!/bin/sh\necho "Python was not found but can be installed from the Microsoft Store" >&2\nexit 9009\n')
# "old" python: -c code runs with sys.version_info patched to 2.7; running a script fails like Python 2
(stub_old / "fakeold.py").write_text(
    "import sys\n"
    "a = sys.argv[1:]\n"
    "if a[:1] == ['-c']:\n"
    "    sys.version_info = (2, 7, 18, 'final', 0)\n"
    "    exec(compile(a[1], '<string>', 'exec'), {'__name__': '__main__'})\n"
    "    sys.exit(0)\n"
    "sys.stderr.write('SyntaxError: future feature annotations is not defined\\n')\n"
    "sys.exit(1)\n", encoding="utf-8")
real_py = sys.executable
for n in ("python", "python3"):
    (stub_old / (n + ".cmd")).write_text(
        f'@"{real_py}" -I "%~dp0fakeold.py" %*\r\n@exit /b %ERRORLEVEL%\r\n', encoding="utf-8")
    (stub_old / n).write_bytes(
        f'#!/bin/sh\nexec "{real_py.replace(chr(92), "/")}" -I "{(stub_old / "fakeold.py").as_posix()}" "$@"\n'.encode("utf-8"))


def env_for(mode):
    e = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(root), PLUGIN_ROOT=str(root))
    base_path = [os.path.join(SYSROOT, "System32"), os.path.join(SYSROOT, r"System32\WindowsPowerShell\v1.0"),
                 GIT_USR_BIN]
    if mode == "no":
        e["PATH"] = os.pathsep.join([str(stub_no)] + base_path)
    elif mode == "old":
        e["PATH"] = os.pathsep.join([str(stub_old)] + base_path)
    else:
        e["PATH"] = os.environ.get("PATH", "") + os.pathsep + GIT_USR_BIN
    return e


hooks = json.loads((root / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]


def run(route, event, data, mode):
    h = hooks[event][0]["hooks"][0]
    t = time.time()
    if route in ("claude-sh", "codex-sh"):
        c = h["command"].replace("${CLAUDE_PLUGIN_ROOT}", root.as_posix())
        r = subprocess.run([str(SH), "-c", c], input=data, capture_output=True, env=env_for(mode), cwd=proj, timeout=120)
    elif route in ("claude-ps", "claude-ps-env"):
        c = h["command"]
        if route == "claude-ps":
            c = c.replace("${CLAUDE_PLUGIN_ROOT}", str(root))
        enc = base64.b64encode(c.encode("utf-16-le")).decode()
        r = subprocess.run([PS, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", enc],
                           input=data, capture_output=True, env=env_for(mode), cwd=proj, timeout=120)
    else:  # codex-cmd
        c = h["commandWindows"]
        for k in ("PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOT"):
            c = c.replace("${%s}" % k, str(root))
        r = subprocess.run(f'"{COMSPEC}" /C "{c}"', input=data, capture_output=True, env=env_for(mode), cwd=proj,
                           timeout=120)
    return r, time.time() - t


J = lambda o: json.dumps(o, ensure_ascii=False).encode("utf-8")


def claude(rel):
    p = str(src / rel)
    return J({"session_id": "t", "cwd": str(proj), "hook_event_name": "PostToolUse", "tool_name": "Write",
              "tool_input": {"file_path": p, "content": "x"}, "tool_response": {"filePath": p, "type": "create"}})


def codex(patch):
    return J({"session_id": "s", "turn_id": "t", "cwd": str(proj), "hook_event_name": "PostToolUse",
              "tool_name": "apply_patch", "tool_input": {"command": "*** Begin Patch\n" + patch + "*** End Patch\n"},
              "tool_response": "Success. Updated the following files:\nM src/bad.py\n"})


CASES = {  # name: (payload, expected exit with a working Python, applies to claude routes?)
    "claude-bad": (claude("bad.py"), 2, True),
    "claude-good": (claude("good.py"), 0, True),
    "claude-bad-space-cjk": (claude("子 資料夾/my bad 檔.py"), 2, True),
    "claude-testfile": (claude("test_bad.py"), 0, True),
    "claude-bom": (b"\xef\xbb\xbf" + claude("bad.py"), 2, True),
    "codex-bad": (codex("*** Update File: src/bad.py\n@@\n-x\n+y\n"), 2, False),
    "codex-good": (codex("*** Add File: src/good.py\n+x\n"), 0, False),
    "codex-bad-space-cjk": (codex("*** Update File: src/子 資料夾/my bad 檔.py\n@@\n-x\n+y\n"), 2, False),
    "codex-multi": (codex("*** Add File: src/good.py\n+x\n*** Update File: src/other.txt\n*** Delete File: src/gone.py\n"
                          "*** Update File: src/old.py\n*** Move to: src/bad.py\n"), 2, False),
    "codex-txt-only": (codex("*** Update File: README.md\n"), 0, False),
    "codex-delete-only": (codex("*** Delete File: src/bad.py\n"), 0, False),
    "malformed-json": (b"{not json", 0, True),
    "json-list": (b"[1, 2]", 0, True),
    "tool_input-null": (J({"tool_input": None, "tool_response": "ok"}), 0, True),
    "empty-stdin": (b"", 0, True),
}
ROUTES = ["claude-sh", "claude-ps", "claude-ps-env", "codex-cmd", "codex-sh"]
SHORT = ["claude-bad", "codex-bad", "malformed-json"]  # enough for the no/old Python modes

fails = 0
total = 0


def check(route, mode, name, r, want, dt):
    global fails, total
    total += 1
    err = r.stderr.decode("utf-8", "replace")
    err_clean = "\n".join(l for l in err.splitlines() if not l.startswith("#< CLIXML") and "<Objs" not in l).strip()
    warn = "靜默失敗檢查" in err
    ok = r.returncode == want and (warn if want == 2 else err_clean == "") and r.stdout.strip() == b""
    fails += not ok
    note = (err_clean.splitlines()[0][:50] if err_clean else "")
    if r.stdout.strip():
        note += " | stdout:" + r.stdout.decode("utf-8", "replace")[:50]
    print(f"{route:13} {mode:4} {name:22} want={want} got={r.returncode:<4} {'OK ' if ok else 'BAD'} {dt:4.1f}s {note}")


print("plugin copy:", root)
print("project    :", proj)
print("git sh     :", SH)
for route in ROUTES:
    claude_route = route.startswith("claude")
    for mode in ("yes", "no", "old"):
        for name, (data, want, for_claude) in CASES.items():
            if claude_route and not for_claude:
                continue
            if mode != "yes" and name not in SHORT:
                continue
            r, dt = run(route, "PostToolUse", data, mode)
            check(route, mode, name, r, want if mode == "yes" else 0, dt)
        r, dt = run(route, "SessionStart", J({"session_id": "s", "hook_event_name": "SessionStart"}), mode)
        out = r.stdout.decode("utf-8", "replace").strip()
        ok = r.returncode == 0 and ((out == "") if mode == "yes" else ('"systemMessage"' in out))
        if ok and mode != "yes":
            try:
                json.loads(out)  # the notice must be valid JSON
            except ValueError:
                ok = False
        total += 1
        fails += not ok
        print(f"{route:13} {mode:4} {'session':22} want=0 got={r.returncode:<4} {'OK ' if ok else 'BAD'} {dt:4.1f}s {out[:60]}")

# --- 300-file patch timing (Codex on Windows), must stay well inside the 10 s hook timeout ---
timings = []
for label, patch, want in (
        ("300 .md + 0 .py", "".join(f"*** Update File: docs/n{i}.md\n" for i in range(300)), 0),
        ("300 .py + bad.py", "".join(f"*** Update File: src/many/m{i}.py\n" for i in range(300))
         + "*** Update File: src/bad.py\n", 2)):
    r, dt = run("codex-cmd", "PostToolUse", codex(patch), "yes")
    check("codex-cmd", "yes", label, r, want, dt)
    timings.append(f"{label.split(' +')[0].replace(' ', '')}={dt:.2f}s")
    if dt >= TIMEOUT_LIMIT / 2:
        fails += 1
        print(f"TOO SLOW: {label} took {dt:.2f}s (limit for this test: {TIMEOUT_LIMIT / 2:.0f}s)")

shutil.rmtree(tmp, ignore_errors=True)
summary = f"{total} cases, {fails} failed; 300-file patch: {', '.join(timings)}"
print("FAILURES:", fails)
print(("SUMMARY|FAIL|" if fails else "SUMMARY|PASS|") + summary)
sys.exit(1 if fails else 0)
