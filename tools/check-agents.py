# -*- coding: utf-8 -*-
"""Helper for tools/check-package.ps1 (agent-twin row). Maintainer tool; not shipped.

Reads {"allowed": [{"agent", "claude", "codex"}, ...], "names": [...]} as JSON on stdin
(allowed = SHA-256 of whole trimmed lines that may differ between a Claude agent body and
its Codex twin). Prints one ASCII line: PASS|... , FAIL|... or SKIPPED|...
Usage: python tools/check-agents.py <dev-bingfa folder>  < spec.json
"""
import hashlib
import json
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    print("SKIPPED|Python %d.%d has no tomllib (needs 3.11+)" % sys.version_info[:2])
    sys.exit(0)

spec = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
allowed, names = spec["allowed"], spec["names"]
pkg = Path(sys.argv[1])
agents_md = pkg / (chr(0x5916) + chr(0x639B)) / "dev-bingfa" / "agents"
agents_toml = pkg / "codex" / "agents"
problems, notes = [], []


def sha(s):
    return hashlib.sha256(s.strip().encode("utf-8")).hexdigest().upper()


def mark(lines, h, tag, where):
    hits = [i for i, l in enumerate(lines) if sha(l) == h]
    if len(hits) != 1:
        problems.append("%s: allowed line %s matched %d times" % (where, h[:12], len(hits)))
        return
    lines[hits[0]] = tag


for name in names:
    md = agents_md / ("%s.md" % name)
    tp = agents_toml / ("bingfa-%s.toml" % name)
    if not md.exists() or not tp.exists():
        problems.append("%s: missing .md or .toml" % name)
        continue
    _, fm, body = md.read_text(encoding="utf-8").split("---", 2)
    keys = [l.split(":", 1)[0] for l in fm.strip().splitlines() if l.strip()]
    if sorted(keys) != ["description", "name"]:
        problems.append("%s.md frontmatter keys %s (only name, description allowed)" % (name, ",".join(keys)))
    desc = [l for l in fm.splitlines() if l.startswith("description:")][0][len("description:"):].strip()
    t = tomllib.loads(tp.read_text(encoding="utf-8"))
    if sorted(t) != ["description", "developer_instructions", "name"]:
        problems.append("%s.toml keys %s (only name, description, developer_instructions allowed)"
                        % (name, ",".join(sorted(t))))
    if t.get("name") != "bingfa-" + name:
        problems.append("%s: toml name is not bingfa-%s" % (name, name))
    if t.get("description") != desc:
        problems.append("%s: description differs" % name)
    a = body.strip().splitlines()
    b = t.get("developer_instructions", "").strip().splitlines()
    n = 0
    for i, rule in enumerate(r for r in allowed if r["agent"] == name):
        tag = "<allowed-%d>" % i
        mark(a, rule["claude"], tag, name + " claude")
        mark(b, rule["codex"], tag, name + " codex")
        n += 1
    if a != b:
        diff = [(x, y) for x, y in zip(a, b) if x != y]
        bad = len(diff) + abs(len(a) - len(b))
        hint = "; first: claude %s / codex %s" % (sha(diff[0][0]), sha(diff[0][1])) if diff else ""
        problems.append("%s: %d unexpected differing line(s)%s" % (name, bad, hint))
    notes.append("%s ok(%d allowed)" % (name, n))

print(("FAIL|" + "; ".join(problems)) if problems else ("PASS|" + ", ".join(notes)))
