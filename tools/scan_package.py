# -*- coding: utf-8 -*-
"""Scan everything under dev-bingfa/ for personal data, secrets and leftovers before packaging.

Maintainer tool; not shipped to colleagues. Python 3.8+, standard library only.

Every file under dev-bingfa/ is read (as UTF-8, bad bytes replaced) and checked for:
  personal    the Windows user name ("nick", "ch.wei")
  email       e-mail addresses; example.com / example.org / example.net are allowed;
              noreply@anthropic.com is always a finding (it must not be in the package at all)
  path        absolute personal paths C:\\Users\\<name>, C:/Users/<name>, /c/Users/<name>,
              /home/<name>, /Users/<name>; placeholders (<...>, %...%, $..., {...}, 你的...)
              are allowed but still listed
  secret      sk-..., ghp_..., github_pat_..., xox?-..., AKIA..., PRIVATE KEY blocks,
              long base64 / hex blobs (>= 40 chars, lockfiles skipped), api_key mentions,
              secret / password / token assignments
  leftover    .scratch, sandbox, card16, review-
  internal    identifiers from the owner's real project noted in the source inventory
              (usage_tracker, pdfplumber, LocateError, "1.5 萬行")
  excluded    tool names that are not shipped (guardrail-spec, work-order, diff-review, patent)
  stray       .gitkeep, __pycache__, *.pyc, Thumbs.db, .DS_Store, *.bak*, editor temp files,
              *.jsonl / *.log (conversation logs)
  size        files larger than 1 MB (always a finding; their content is not scanned)
  licence     copyright / licence lines (listed only, never a finding)

Hits are printed in two groups:
  MATT   inside 離線副本/mattpocock-skills/ (Matt Pocock's unmodified copy): informational,
         except noreply@anthropic.com, stray files and size, which are findings everywhere.
  OURS   everything else: each hit is a finding unless JUSTIFIED below (file + text + reason).

Usage:  python tools/scan_package.py [--root <repo folder>]
        (--root defaults to the folder above tools/; it must contain dev-bingfa/)
Exit code: 0 = no findings, 1 = at least one finding (or the package folder is missing).
"""
import argparse
import re
import sys
from pathlib import Path

if sys.version_info < (3, 8):
    print("FAIL: needs Python 3.8+, this is %d.%d" % sys.version_info[:2])
    sys.exit(1)

MATT = ("離線副本", "mattpocock-skills")
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml"}
MAX_BYTES = 1024 * 1024
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
PLACEHOLDER_START = "<%${["

# Hits in OUR files that were looked at and are fine. (path relative to dev-bingfa/ with "/",
# category, a substring of the hit's line, reason). Each entry must match at least one hit,
# otherwise it is reported as stale (so the list cannot silently rot).
JUSTIFIED = [
    ("外掛/dev-bingfa-check/hooks/check_silence.py", "internal", "1.5 萬行",
     "owner's original check_silence.py; must stay byte-identical (check_package check 5)"),
    ("外掛/dev-bingfa-check/hooks/check_silence.py", "internal", "LocateError",
     "owner's original check_silence.py; must stay byte-identical (check_package check 5)"),
    ("外掛/dev-bingfa-check/hooks/check_silence.py", "internal", "usage_tracker",
     "owner's original check_silence.py; must stay byte-identical (check_package check 5)"),
    ("外掛/dev-bingfa-check/hooks/check_silence.py", "internal", "pdfplumber",
     "owner's original check_silence.py; must stay byte-identical (check_package check 5)"),
    ("說明書/2-第一次使用.html", "leftover", ".scratch",
     "the user's own project folder where Matt's to-spec / to-tickets save files, not ours"),
    ("說明書/3-日常速查.html", "leftover", ".scratch",
     "the user's own project folder where Matt's to-spec / to-tickets save files, not ours"),
    ("離線副本/第三方內容聲明.md", "secret", "提交編號（commit）",
     "the public git commit id of Matt Pocock's repo the offline copy was taken from"),
]

PATTERNS = [
    ("personal", re.compile(r"(?i)(?<![a-z])nick(?![a-z])")),
    ("personal", re.compile(r"(?i)ch\.wei")),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("path", re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+(?:<[^>\s]*>|[^\\/\s\"'`)<>]+)")),
    ("path", re.compile(r"(?i)(?<![\w.])/(?:c/users|home|users)/(?:<[^>\s]*>|[^/\s\"'`)<>]+)")),
    ("secret", re.compile(r"\bsk-[A-Za-z0-9_-]{16,}")),
    ("secret", re.compile(r"\bghp_[A-Za-z0-9]{20,}")),
    ("secret", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}")),
    ("secret", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("secret", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("secret", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
    ("secret", re.compile(r"(?i)api[_-]?key")),
    ("secret", re.compile(r"(?i)\b(?:secret|password|passwd|token)s?\b[\"']?\s*[:=]\s*[\"']?[^\s\"'<>]{4,}")),
    ("leftover", re.compile(r"(?i)\.scratch|sandbox|card16|review-")),
    ("internal", re.compile(r"usage_tracker|pdfplumber|LocateError|1\.5 ?萬行")),
    ("excluded", re.compile(r"(?i)guardrail-spec|work-order|diff-review|patent")),
    ("licence", re.compile(r"(?i)copyright|\(c\) ?\d{4}|licen[cs]ed? under")),
]
BLOB_B64 = re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")
BLOB_HEX = re.compile(r"\b[0-9a-fA-F]{40,}\b")
STRAY_NAMES = {".gitkeep", "thumbs.db", ".ds_store", "desktop.ini"}
STRAY_DIRS = {"__pycache__"}
STRAY_RE = re.compile(r"(?i)(\.pyc|\.pyo|\.bak.*|\.orig|\.swp|\.swo|\.tmp|~|\.jsonl|\.log)$|^~\$|^\.#")


def is_stray(rel_parts):
    """True for a file the package must never carry (also used by build_zip.py)."""
    name = rel_parts[-1]
    if any(p.lower() in STRAY_DIRS for p in rel_parts[:-1]):
        return True
    return name.lower() in STRAY_NAMES or bool(STRAY_RE.search(name))


def in_matt(rel_parts):
    return tuple(rel_parts[:2]) == MATT


def blob_hits(line):
    out = []
    for m in BLOB_HEX.finditer(line):
        out.append(m.group())
    for m in BLOB_B64.finditer(line):
        s = m.group()
        # a real blob mixes upper, lower and digits; plain paths / words do not
        if re.search(r"[A-Z]", s) and re.search(r"[a-z]", s) and re.search(r"[0-9]", s):
            out.append(s)
    return out


def classify(cat, text):
    """Return 'skip' for hits that are allowed outright, else 'hit'."""
    if cat == "email":
        domain = text.rsplit("@", 1)[1].lower()
        if text.lower() == "noreply@anthropic.com":
            return "always"
        if domain in ALLOWED_EMAIL_DOMAINS or domain.endswith(tuple("." + d for d in ALLOWED_EMAIL_DOMAINS)):
            return "allowed"
    if cat == "path":
        name = re.split(r"[\\/]+", text.rstrip("\\/"))[-1]
        if name[:1] in PLACEHOLDER_START or name.startswith("你的") or name.lower() in ("public", "default", "..."):
            return "allowed"
    if cat == "licence":
        return "info"
    return "hit"


def scan(pkg):
    hits = []  # (group, kind, rel, line_no, cat, text, line)
    for f in sorted(pkg.rglob("*")):
        if not f.is_file():
            continue
        parts = f.relative_to(pkg).parts
        rel = "/".join(parts)
        group = "MATT" if in_matt(parts) else "OURS"
        if is_stray(parts):
            hits.append((group, "always", rel, 0, "stray", parts[-1], ""))
        size = f.stat().st_size
        if size > MAX_BYTES:
            hits.append((group, "always", rel, 0, "size", "%d bytes" % size, ""))
            continue  # already a finding; its content is not scanned (regexes get slow on huge lines)
        text = f.read_bytes().decode("utf-8", "replace")
        for no, line in enumerate(text.splitlines(), 1):
            found = [(cat, m.group()) for cat, rx in PATTERNS
                     if cat != "email" or "@" in line  # the e-mail regex is slow on long lines
                     for m in rx.finditer(line)]
            if f.name not in LOCKFILES:
                found += [("secret", b) for b in blob_hits(line)]
            for cat, t in found:
                kind = classify(cat, t)
                hits.append((group, kind, rel, no, cat, t, line.strip()))
    return hits


def main():
    tools = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Scan dev-bingfa/ for personal data and secrets.")
    ap.add_argument("--root", default=str(tools.parent), help="repo folder that contains dev-bingfa/")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    pkg = Path(args.root).resolve() / "dev-bingfa"
    if not pkg.is_dir():
        print("FAIL: package folder not found: %s" % pkg)
        return 1

    hits = scan(pkg)
    used = set()
    findings, justified, listed, info = [], [], [], []
    for h in hits:
        group, kind, rel, no, cat, t, line = h
        if kind == "always":
            findings.append(h)
        elif kind in ("allowed", "info"):
            (listed if kind == "allowed" else info).append(h)
        elif group == "MATT":
            info.append(h)
        else:
            j = next((i for i, (p, c, sub, _) in enumerate(JUSTIFIED)
                      if p == rel and c == cat and sub in line), None)
            if j is None:
                findings.append(h)
            else:
                used.add(j)
                justified.append(h + (JUSTIFIED[j][3],))
    stale = [JUSTIFIED[i] for i in range(len(JUSTIFIED)) if i not in used]

    def show(title, rows, reason=False):
        print("\n== %s: %d" % (title, len(rows)))
        for r in rows:
            loc = "%s:%d" % (r[2], r[3]) if r[3] else r[2]
            extra = "  -- " + r[7] if reason else ""
            print("  [%s/%s] %s  %r%s" % (r[0], r[4], loc, r[5][:80], extra))

    print("package:", pkg)
    print("files scanned:", sum(1 for p in pkg.rglob("*") if p.is_file()))
    show("FINDINGS (must be zero)", findings)
    show("OURS justified", justified, reason=True)
    show("allowed placeholders / example addresses (listed for judgment)", listed)
    show("informational (Matt's copy, licence lines)", info)
    if stale:
        print("\n== stale JUSTIFIED entries (no longer match anything): %d" % len(stale))
        for p, c, sub, _ in stale:
            print("  %s [%s] %r" % (p, c, sub))
    bad = len(findings) + len(stale)
    print("\n%s: %d finding(s), %d stale justification(s)." % ("FAIL" if bad else "PASS", len(findings), len(stale)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
