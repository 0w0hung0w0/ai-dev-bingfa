# -*- coding: utf-8 -*-
"""Run every dev-bingfa package invariant and print a PASS / FAIL / SKIPPED table.

Maintainer tool; not shipped to colleagues. Python 3.8+, standard library only.
Replaces the old tools/check-package.ps1 (blocked on the company PC by a false positive).

Checks (<plugin>, <rules>, <basic> = the package folders 外掛, 規則, 基本版):
   1. basic-sync     every file under <plugin>/dev-bingfa/skills/** equals (SHA-256) its copy under
                     <basic>/.agents/skills/**, <rules>/AGENTS.md equals <basic>/AGENTS.md, and
                     <basic>/.agents/skills/ has no file without a master (same rule as
                     tools/sync-basic.ps1 -CheckOnly, re-implemented here).
   2. rules-twin     <rules>/AGENTS.md is byte-identical to <rules>/CLAUDE.md.
   3. agent-files    <plugin>/dev-bingfa/agents/ holds exactly the three expected <name>.md and
                     codex/agents/ holds exactly the three expected bingfa-<name>.toml, nothing else.
   4. agent-twin     each Codex TOML has only name / description / developer_instructions,
                     name == bingfa-<name>, the same description as its Claude agent, and
                     developer_instructions == the Claude body except for the whole lines in
                     ALLOWED_DIFFS (SHA-256 of the trimmed line). Each Claude agent's frontmatter
                     has only name / description. Needs Python 3.11+ (tomllib), else SKIPPED.
   5. check-silence  check_silence.py has the recorded SHA-256 (owner's original; never edited).
   6. version        VERSION (e.g. 1.0) matches "version" in both plugin.json files (1.0.0).
   7. line-endings   every .sh is LF only, every .cmd is CRLF only (offline copy excluded).
   8. json           every *.json under dev-bingfa/ (offline copy excluded) parses.
   9. hooks-json     hooks.json has exactly SessionStart + PostToolUse, matcher "Write|Edit" on
                     PostToolUse only, one command hook each with timeout 10, `command` calls
                     run.sh and run.cmd with the right argument, and the exact `commandWindows`.
  10. marketplace    marketplace.json lists exactly dev-bingfa and dev-bingfa-check, and each
                     "source" folder has a plugin.json with the same name.
  11. commit-manual  skills/commit/SKILL.md frontmatter has `disable-model-invocation: true` and
                     skills/commit/agents/openai.yaml has `policy:` with
                     `allow_implicit_invocation: false`.
  12. search-modules exactly the five expected web-search-modules/*.md, each non-empty and
                     starting with a "# " heading.
  13. hook-matrix    tools/test-hooks.py (next to this file) against the package's
                     dev-bingfa-check. SKIPPED when it reports SKIPPED (no Git sh / not Windows).

Usage:  python tools/check_package.py [--root <repo folder>]
        (--root defaults to the folder above tools/; point it at a copy to test that copy)
Exit code: 0 = all PASS, 1 = at least one FAIL, 2 = no FAIL but something SKIPPED.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

if sys.version_info < (3, 8):
    print("FAIL: needs Python 3.8+, this is %d.%d" % sys.version_info[:2])
    sys.exit(1)

# SHA-256 of the owner's original check_silence.py (recorded 2026-11-24).
CHECK_SILENCE_SHA = "FF5640ACBCF50B74B90E5FADA003A48F7E52CDC0F8ADC05DD6775DE05C604C39"

# Whole lines allowed to differ between a Claude agent body and its Codex twin, as SHA-256
# (upper-case hex, UTF-8) of the trimmed line. Each hash must match exactly one line on its side.
# When a line is changed on purpose, the agent-twin FAIL detail prints the new hashes.
ALLOWED_DIFFS = [
    # "Before executing any WebSearch or WebFetch ..." / "Before running any web search ..."
    {"agent": "web-search-agent",
     "claude": "1724276F97E456E405DF8369EEBAA4606D93EBF25C3EC46F7C8E88836879D9F7",
     "codex": "AD4E2201A9C187EFB2A8BC2A485EC942F79AFEF31F7F8598985A80E2AB69BC4B"},
    # "DO NOT skip this step. DO NOT call WebSearch ..." / "... DO NOT run any web search ..."
    {"agent": "web-search-agent",
     "claude": "0449BD187586A8C6C87902061CBEF6948F6A95D19648BC302C0B22A60826B224",
     "codex": "FA3C96AD42D188523F11FF8078DCF92A3709AF584C89A5EAEE8B5D4D5D93A983"},
]
AGENT_NAMES = ["explorer", "implementer", "web-search-agent"]
SEARCH_MODULES = ["academic-papers.md", "chinese-tech.md", "general-web.md", "github-debug.md",
                  "stackoverflow.md"]
PLUGIN, RULES, BASIC, OFFLINE = "外掛", "規則", "基本版", "離線副本"

TOOLS = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="Check the dev-bingfa package invariants.")
parser.add_argument("--root", default=str(TOOLS.parent), help="repo folder that contains dev-bingfa/")
args = parser.parse_args()

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
PKG = Path(args.root).resolve() / "dev-bingfa"
PLUG = PKG / PLUGIN
if not PKG.is_dir():
    print("FAIL: package folder not found: %s" % PKG)
    sys.exit(1)

rows = []


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def sha_line(line):
    return hashlib.sha256(line.strip().encode("utf-8")).hexdigest().upper()


def read_utf8(path):
    return Path(path).read_bytes().decode("utf-8")  # strict: a BOM or bad byte is a problem too


def entries(folder):
    """Names of everything in a folder (files, folders, hidden ones)."""
    return sorted(p.name for p in Path(folder).iterdir())


def package_files():
    skip = PKG / OFFLINE
    return [p for p in PKG.rglob("*") if p.is_file() and skip not in p.parents]


def result(problems, ok_detail):
    return ("FAIL", "; ".join(problems)) if problems else ("PASS", ok_detail)


# --- the checks: each returns (result, detail) --------------------------------------------------

def check_basic_sync():
    src = PLUG / "dev-bingfa" / "skills"
    basic = PKG / BASIC
    dst = basic / ".agents" / "skills"
    for p in (src, PKG / RULES):
        if not p.is_dir():
            return "FAIL", "master folder not found: %s" % p
    pairs = [(f, dst / f.relative_to(src)) for f in sorted(src.rglob("*")) if f.is_file()]
    pairs.append((PKG / RULES / "AGENTS.md", basic / "AGENTS.md"))
    problems = []
    for s, d in pairs:
        if not d.is_file():
            problems.append("MISSING " + str(d.relative_to(PKG)))
        elif sha_file(s) != sha_file(d):
            problems.append("DIFF " + str(d.relative_to(PKG)))
    expected = {str(d).lower() for _, d in pairs}  # Windows paths are case-insensitive
    if dst.is_dir():
        for f in sorted(dst.rglob("*")):
            if f.is_file() and str(f).lower() not in expected:
                problems.append("EXTRA " + str(f.relative_to(PKG)))
    return result(problems, "all %d file(s) equal to master" % len(pairs))


def check_rules_twin():
    a = sha_file(PKG / RULES / "AGENTS.md")
    c = sha_file(PKG / RULES / "CLAUDE.md")
    if a == c:
        return "PASS", "AGENTS.md == CLAUDE.md " + a[:12]
    return "FAIL", "AGENTS.md %s != CLAUDE.md %s" % (a[:12], c[:12])


def check_agent_files():
    got_md = entries(PLUG / "dev-bingfa" / "agents")
    got_toml = entries(PKG / "codex" / "agents")
    problems = []
    if got_md != sorted(n + ".md" for n in AGENT_NAMES):
        problems.append("Claude agents: " + ",".join(got_md))
    if got_toml != sorted("bingfa-%s.toml" % n for n in AGENT_NAMES):
        problems.append("Codex agents: " + ",".join(got_toml))
    return result(problems, "3 Claude .md + 3 Codex .toml, nothing else")


def check_agent_twin():
    try:
        import tomllib
    except ImportError:
        return "SKIPPED", "Python %d.%d has no tomllib (needs 3.11+)" % sys.version_info[:2]
    problems, notes = [], []

    def mark(lines, h, tag, where):
        hits = [i for i, line in enumerate(lines) if sha_line(line) == h]
        if len(hits) != 1:
            problems.append("%s: allowed line %s matched %d times" % (where, h[:12], len(hits)))
            return
        lines[hits[0]] = tag

    for name in AGENT_NAMES:
        md = PLUG / "dev-bingfa" / "agents" / (name + ".md")
        tp = PKG / "codex" / "agents" / ("bingfa-%s.toml" % name)
        if not md.is_file() or not tp.is_file():
            problems.append("%s: missing .md or .toml" % name)
            continue
        text = read_utf8(md).replace("\r\n", "\n")
        if not text.startswith("---\n"):
            problems.append("%s.md does not start with a --- frontmatter" % name)
            continue
        _, fm, body = text.split("---", 2)
        keys = [line.split(":", 1)[0] for line in fm.strip().splitlines() if line.strip()]
        if sorted(keys) != ["description", "name"]:
            problems.append("%s.md frontmatter keys %s (only name, description allowed)" % (name, ",".join(keys)))
        desc = [line for line in fm.splitlines() if line.startswith("description:")]
        desc = desc[0][len("description:"):].strip() if desc else None
        t = tomllib.loads(read_utf8(tp))
        if sorted(t) != ["description", "developer_instructions", "name"]:
            problems.append("%s.toml keys %s (only name, description, developer_instructions allowed)"
                            % (name, ",".join(sorted(t))))
        if t.get("name") != "bingfa-" + name:
            problems.append("%s: toml name is not bingfa-%s" % (name, name))
        if t.get("description") != desc:
            problems.append("%s: description differs" % name)
        a = body.strip().splitlines()
        b = str(t.get("developer_instructions", "")).replace("\r\n", "\n").strip().splitlines()
        n = 0
        for i, rule in enumerate(r for r in ALLOWED_DIFFS if r["agent"] == name):
            tag = "<allowed-%d>" % i
            mark(a, rule["claude"], tag, name + " claude")
            mark(b, rule["codex"], tag, name + " codex")
            n += 1
        if a != b:
            diff = [(x, y) for x, y in zip(a, b) if x != y]
            bad = len(diff) + abs(len(a) - len(b))
            hint = "; first: claude %s / codex %s" % (sha_line(diff[0][0]), sha_line(diff[0][1])) if diff else ""
            problems.append("%s: %d unexpected differing line(s)%s" % (name, bad, hint))
        notes.append("%s ok(%d allowed)" % (name, n))
    return result(problems, ", ".join(notes))


def check_check_silence():
    h = sha_file(PLUG / "dev-bingfa-check" / "hooks" / "check_silence.py")
    if h == CHECK_SILENCE_SHA:
        return "PASS", "sha256 %s == recorded" % h[:12]
    return "FAIL", "sha256 %s != recorded %s" % (h[:12], CHECK_SILENCE_SHA[:12])


def check_version():
    v = read_utf8(PKG / "VERSION").strip()
    want = v + ".0" if len(v.split(".")) == 2 else v
    problems = []
    for name in ("dev-bingfa", "dev-bingfa-check"):
        got = json.loads(read_utf8(PLUG / name / ".claude-plugin" / "plugin.json")).get("version")
        if got != want:
            problems.append("%s=%s" % (name, got))
    if problems:
        return "FAIL", "VERSION %s wants %s; %s" % (v, want, ", ".join(problems))
    return "PASS", "VERSION %s -> both plugin.json %s" % (v, want)


def check_line_endings():
    files = [f for f in package_files() if f.suffix.lower() in (".sh", ".cmd")]
    if not files:
        return "FAIL", "no .sh / .cmd files found"
    problems = []
    for f in files:
        data = f.read_bytes()
        crlf = data.count(b"\r\n")
        lf = data.count(b"\n") - crlf
        ok = crlf == 0 if f.suffix.lower() == ".sh" else (lf == 0 and crlf > 0)
        if not ok:
            problems.append("%s (LF=%d CRLF=%d)" % (f.name, lf, crlf))
    return result(problems, "%d file(s): .sh LF, .cmd CRLF" % len(files))


def check_json():
    files = [f for f in package_files() if f.suffix.lower() == ".json"]
    if not files:
        return "FAIL", "no .json files found"
    bad = []
    for f in files:
        try:
            json.loads(read_utf8(f))
        except ValueError as e:  # UnicodeDecodeError and JSONDecodeError are both ValueError
            bad.append("%s (%s)" % (f.relative_to(PKG), str(e)[:60]))
    if bad:
        return "FAIL", "does not parse: " + ", ".join(bad)
    return "PASS", "%d file(s) parse" % len(files)


def check_hooks_json():
    hj = json.loads(read_utf8(PLUG / "dev-bingfa-check" / "hooks" / "hooks.json"))["hooks"]
    want = {
        "SessionStart": (None, "session", '"${CLAUDE_PLUGIN_ROOT}\\hooks\\run.cmd" session'),
        "PostToolUse": ("Write|Edit", "post", '"${CLAUDE_PLUGIN_ROOT}\\hooks\\codex-post.cmd"'),
    }
    problems = []
    if sorted(hj) != sorted(want):
        problems.append("events: " + ",".join(sorted(hj)))
    for ev, (matcher, arg, win) in want.items():
        groups = hj.get(ev) or []
        if len(groups) != 1:
            problems.append("%s has %d groups" % (ev, len(groups)))
            continue
        if groups[0].get("matcher") != matcher:
            problems.append("%s matcher %r" % (ev, groups[0].get("matcher")))
        hs = groups[0].get("hooks") or []
        if len(hs) != 1:
            problems.append("%s has %d hooks" % (ev, len(hs)))
            continue
        h = hs[0]
        command = str(h.get("command", ""))
        if h.get("type") != "command":
            problems.append("%s type %r" % (ev, h.get("type")))
        if h.get("timeout") != 10 or isinstance(h.get("timeout"), bool):
            problems.append("%s timeout %r" % (ev, h.get("timeout")))
        if ('/hooks/run.sh" %s\n' % arg) not in command:
            problems.append("%s command does not call run.sh %s" % (ev, arg))
        if ('/hooks/run.cmd" %s\n' % arg) not in command:
            problems.append("%s command does not call run.cmd %s" % (ev, arg))
        if h.get("commandWindows") != win:
            problems.append("%s commandWindows %r" % (ev, h.get("commandWindows")))
    return result(problems, "SessionStart + PostToolUse(Write|Edit), timeout 10, commands as expected")


def check_marketplace():
    mp = json.loads(read_utf8(PLUG / ".claude-plugin" / "marketplace.json"))
    plugins = mp.get("plugins") or []
    names = sorted(str(p.get("name")) for p in plugins)
    problems = []
    if names != ["dev-bingfa", "dev-bingfa-check"]:
        problems.append("plugins: " + ",".join(names))
    for p in plugins:
        pj = PLUG / str(p.get("source")) / ".claude-plugin" / "plugin.json"
        if not pj.is_file():
            problems.append("%s: source %r has no plugin.json" % (p.get("name"), p.get("source")))
            continue
        pn = json.loads(read_utf8(pj)).get("name")
        if pn != p.get("name"):
            problems.append("%s: source plugin.json name is %r" % (p.get("name"), pn))
    return result(problems, "sources resolve: " + ", ".join(names))


def check_commit_manual():
    cdir = PLUG / "dev-bingfa" / "skills" / "commit"
    problems = []
    parts = re.split(r"(?m)^---[ \t]*\r?$", read_utf8(cdir / "SKILL.md"), maxsplit=2)
    fm = parts[1] if len(parts) == 3 else ""
    if not re.search(r"(?m)^disable-model-invocation:[ \t]*true[ \t]*\r?$", fm):
        problems.append("SKILL.md frontmatter lacks disable-model-invocation: true")
    oy = cdir / "agents" / "openai.yaml"
    if not oy.is_file():
        problems.append("agents/openai.yaml missing")
    else:
        text = read_utf8(oy)
        if not re.search(r"(?m)^policy:[ \t]*\r?\n(?:[ \t]*#.*\r?\n)*[ \t]+allow_implicit_invocation:[ \t]*false[ \t]*\r?$",
                         text):
            problems.append("openai.yaml lacks policy: allow_implicit_invocation: false")
    return result(problems, "disable-model-invocation: true + openai.yaml allow_implicit_invocation: false")


def check_search_modules():
    mdir = PLUG / "dev-bingfa" / "web-search-modules"
    got = entries(mdir)
    problems = []
    if got != sorted(SEARCH_MODULES):
        problems.append("files: " + ",".join(got))
    for n in got:
        f = mdir / n
        if not f.is_file():
            continue
        t = read_utf8(f)
        if not t.strip() or not t.startswith("# "):
            problems.append("%s empty or no '# ' heading" % n)
    return result(problems, "%d module(s), each with a heading" % len(got))


def check_hook_matrix():
    script = TOOLS / "test-hooks.py"
    r = subprocess.run([sys.executable, "-I", str(script), str(PLUG / "dev-bingfa-check")],
                       capture_output=True, stdin=subprocess.DEVNULL, timeout=900)
    out = r.stdout.decode("utf-8", "replace")
    sums = [line for line in out.splitlines() if line.startswith("SUMMARY|")]
    parts = sums[-1].split("|", 2) if sums else []
    if len(parts) == 3 and parts[1] == "PASS" and r.returncode == 0:
        return "PASS", parts[2]
    if len(parts) == 3 and parts[1] == "SKIPPED" and r.returncode == 2:
        return "SKIPPED", parts[2]
    if len(parts) == 3:
        return "FAIL", parts[2] + " (run python tools/test-hooks.py for the table)"
    err = r.stderr.decode("utf-8", "replace").strip().splitlines()
    return "FAIL", "exit %d, no SUMMARY line%s" % (r.returncode, ("; " + err[-1][:100]) if err else "")


CHECKS = [
    ("basic-sync", check_basic_sync),
    ("rules-twin", check_rules_twin),
    ("agent-files", check_agent_files),
    ("agent-twin", check_agent_twin),
    ("check-silence", check_check_silence),
    ("version", check_version),
    ("line-endings", check_line_endings),
    ("json", check_json),
    ("hooks-json", check_hooks_json),
    ("marketplace", check_marketplace),
    ("commit-manual", check_commit_manual),
    ("search-modules", check_search_modules),
    ("hook-matrix", check_hook_matrix),
]

print("package:", PKG)
for name, fn in CHECKS:
    try:
        res, detail = fn()
    except Exception as e:  # a missing / unreadable file is a FAIL, never a crash or a PASS
        res, detail = "FAIL", "%s: %s" % (type(e).__name__, e)
    rows.append((name, res, detail))

w = max(len(r[0]) for r in rows)
print("%-*s  %-7s  %s" % (w, "Check", "Result", "Detail"))
print("%-*s  %-7s  %s" % (w, "-----", "------", "------"))
for name, res, detail in rows:
    print("%-*s  %-7s  %s" % (w, name, res, detail))

fails = sum(r[1] == "FAIL" for r in rows)
skipped = sum(r[1] == "SKIPPED" for r in rows)
if fails:
    print("FAIL: %d of %d check(s) failed." % (fails, len(rows)))
    sys.exit(1)
if skipped:
    print("INCOMPLETE: %d check(s) skipped, the rest passed." % skipped)
    sys.exit(2)
print("PASS: all %d check(s) passed." % len(rows))
sys.exit(0)
