# -*- coding: utf-8 -*-
"""Build the release zip of the dev-bingfa package, the same bytes every time.

Maintainer tool; not shipped to colleagues. Python 3.8+, standard library only.

Steps:
  1. Run tools/check_package.py and tools/scan_package.py; stop unless BOTH exit 0
     (a SKIPPED check, exit 2, also stops the build).
  2. Read the version from dev-bingfa/VERSION.
  3. Write dist/dev-bingfa-<version>.zip holding every file under dev-bingfa/ in the working tree
     at the ZIP ROOT (no top-level folder: Explorer's "Extract All" creates a folder named after the
     zip, so C:\\dev-bingfa-<version>\\ then holds the files directly, as manual 1 says), except stray files (same rule as scan_package.py:
     __pycache__, *.pyc, .gitkeep, Thumbs.db, .DS_Store, *.bak*, editor temp files, logs).
     Deterministic: sorted order, fixed timestamp and attributes, bytes copied as-is (no line-ending
     conversion), every non-ASCII file name stored as UTF-8 with the UTF-8 flag set (Windows
     Explorer then shows the Chinese names correctly; ASCII names are the same in any encoding).
  4. Write dist/dev-bingfa-<version>.sha256 and dist/dev-bingfa-<version>-檔案清單.txt
     (path, size, SHA-256 of every file in the zip).

Usage:  python tools/build_zip.py [--root <repo folder>]
        (--root defaults to the folder above tools/; it must contain dev-bingfa/; dist/ goes there)
Exit code: 0 = built, 1 = a gate failed or the build failed (nothing is left half-written).
"""
import argparse
import hashlib
import os
import subprocess
import sys
import zipfile
from pathlib import Path

if sys.version_info < (3, 8):
    print("FAIL: needs Python 3.8+, this is %d.%d" % sys.version_info[:2])
    sys.exit(1)

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))  # -I drops the script folder from sys.path
sys.dont_write_bytecode = True   # no tools/__pycache__ left behind
from scan_package import is_stray  # noqa: E402  (one rule for "stray", shared with the scan)

FIXED_TIME = (2026, 1, 1, 0, 0, 0)  # every entry gets this time, so two builds are identical
UTF8_FLAG = 0x800


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def gate(script, root):
    print("== running %s" % script.name)
    r = subprocess.run([sys.executable, "-I", str(script), "--root", str(root)],
                       stdin=subprocess.DEVNULL, capture_output=True)
    out = r.stdout.decode("utf-8", "replace").strip().splitlines()
    print("   " + (out[-1] if out else "(no output)") + "  [exit %d]" % r.returncode)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser(description="Build dist/dev-bingfa-<version>.zip deterministically.")
    ap.add_argument("--root", default=str(TOOLS.parent), help="repo folder that contains dev-bingfa/")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    root = Path(args.root).resolve()
    pkg = root / "dev-bingfa"
    if not pkg.is_dir():
        print("FAIL: package folder not found: %s" % pkg)
        return 1

    ok = gate(TOOLS / "check_package.py", root)
    ok = gate(TOOLS / "scan_package.py", root) and ok
    if not ok:
        print("FAIL: not building. Run the two tools above, fix what they report, then build again.")
        return 1

    version = (pkg / "VERSION").read_bytes().decode("utf-8").strip()
    if not version or any(c in version for c in '\\/:*?"<>| '):
        print("FAIL: VERSION is empty or not a plain version: %r" % version)
        return 1
    top = "dev-bingfa-%s" % version
    dist = root / "dist"
    dist.mkdir(exist_ok=True)
    zpath = dist / (top + ".zip")
    shapath = dist / (top + ".sha256")
    listpath = dist / (top + "-檔案清單.txt")

    files, skipped = [], []
    for f in pkg.rglob("*"):
        if f.is_file():
            parts = f.relative_to(pkg).parts
            (skipped if is_stray(parts) else files).append(("/".join(parts), f))
    files.sort(key=lambda x: x[0].encode("utf-8"))

    tmp = zpath.with_name(zpath.name + ".partial")
    rows = []
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for rel, f in files:
                data = f.read_bytes()
                zi = zipfile.ZipInfo(rel, date_time=FIXED_TIME)
                zi.create_system = 3                 # same on every OS
                zi.external_attr = 0o100644 << 16    # plain file, rw-r--r--
                zi.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(zi, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                rows.append((rel, len(data), sha256(data)))
        with zipfile.ZipFile(tmp) as z:  # read back: every entry must decompress to the same bytes
            bad = z.testzip()
            if bad:
                raise RuntimeError("entry does not read back: %s" % bad)
            infos = z.infolist()
            if len(infos) != len(rows):
                raise RuntimeError("zip has %d entries, expected %d" % (len(infos), len(rows)))
            for (name, size, h), info in zip(rows, infos):
                if info.filename != name or sha256(z.read(info)) != h:
                    raise RuntimeError("entry differs after writing: %s" % name)
                # zipfile sets the UTF-8 flag itself for every non-ASCII name (it cannot be forced
                # on ASCII names, where it makes no difference); make sure it really did
                if not name.isascii() and not info.flag_bits & UTF8_FLAG:
                    raise RuntimeError("UTF-8 flag missing: %s" % name)
        os.replace(tmp, zpath)
    except Exception as e:
        if tmp.exists():
            tmp.unlink()
        print("FAIL: build failed, no zip written: %s: %s" % (type(e).__name__, e))
        return 1

    zhash = sha256(zpath.read_bytes())
    shapath.write_bytes(("%s  %s\n" % (zhash, zpath.name)).encode("utf-8"))
    lines = ["# %s  %d 個檔案  （路徑 / 大小（位元組） / SHA-256）" % (zpath.name, len(rows))]
    lines += ["%s\t%d\t%s" % r for r in rows]
    listpath.write_bytes(("\r\n".join(lines) + "\r\n").encode("utf-8"))

    print("== built")
    print("   zip:     %s" % zpath)
    print("   size:    %d bytes" % zpath.stat().st_size)
    print("   files:   %d (at the zip root, no top-level folder)" % len(rows))
    print("   sha256:  %s" % zhash)
    print("   list:    %s" % listpath.name)
    if skipped:
        print("   left out (stray): " + ", ".join(rel for rel, _ in skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
