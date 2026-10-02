"""Download EdiabasLib's drop-in EDIABAS API DLLs into vendor/ediabaslib/ (gitignored).

    python tools/install_ediabaslib.py            # latest "Binaries-*" release
    python tools/install_ediabaslib.py --tag binaries_20260607
    python tools/install_ediabaslib.py --zip path/to/Binaries-YYYYMMDD.zip   # offline

EdiabasLib (https://github.com/uholeschak/ediabaslib) is GPL-3. It isn't redistributed in
this repo; this script fetches it from the project's GitHub releases. From the release zip
it extracts EdiabasLibConfigTool/Api32/{Api32.dll, Api64.dll}. These are self-contained
mixed-mode .NET Framework 4.x assemblies that export the standard EDIABAS C API.
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from r53diag import config  # noqa: E402

REPO = "uholeschak/ediabaslib"
MEMBERS = ("EdiabasLibConfigTool/Api32/Api32.dll", "EdiabasLibConfigTool/Api32/Api64.dll")


def latest_release(tag: str | None) -> tuple[str, str]:
    url = f"https://api.github.com/repos/{REPO}/releases" + (f"/tags/{tag}" if tag else "?per_page=10")
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    releases = [data] if tag else data
    for rel in releases:
        for a in rel.get("assets", []):
            if a["name"].lower().startswith("binaries") and a["name"].lower().endswith(".zip"):
                return rel["tag_name"], a["browser_download_url"]
    raise SystemExit("no Binaries-*.zip asset found in EdiabasLib releases")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", help="release tag, e.g. binaries_20260607 (default: latest)")
    ap.add_argument("--zip", type=Path, help="use an already-downloaded Binaries zip")
    args = ap.parse_args()

    if args.zip:
        tag, blob = args.zip.stem, args.zip.read_bytes()
    else:
        tag, url = latest_release(args.tag)
        print(f"downloading {url} …", file=sys.stderr)
        with urllib.request.urlopen(url, timeout=600) as r:
            blob = r.read()

    dest = config.ediabaslib_dir()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for m in MEMBERS:
            (dest / Path(m).name).write_bytes(z.read(m))
    (dest / "VERSION").write_text(f"{tag}\nhttps://github.com/{REPO}\nlicense: GPL-3.0\n", encoding="utf-8")

    rel = config.dotnet_framework_release()
    print(json.dumps({
        "installed": tag,
        "dir": str(dest),
        "dll": str(config.ediabaslib_dll()),
        "dotnet_framework_4x_release": rel,
        "dotnet_ok": bool(rel and rel >= 461808),   # 4.7.2+
        "next": "python -m r53diag doctor --backend ediabaslib",
    }, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
