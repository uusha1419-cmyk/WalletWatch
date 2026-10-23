"""Polite PDF downloader + manifest builder.

Usage:
  python tools/download.py url.txt   # download listed PDFs, then rebuild manifest
  python tools/download.py           # only rebuild manifest from data/raw/**/*.pdf

url.txt: one line per report, format  company,year,direct_pdf_url
  paytm,fy2026,https://.../report.pdf
Lines starting with # are skipped.
"""
import csv
import hashlib
import pathlib
import sys
import time
from datetime import date
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import fitz  # pip install pymupdf
import requests

RAW = pathlib.Path("data/raw")
MANIFEST = pathlib.Path("data/manifest.csv")
HEADERS = {"User-Agent": "WalletWatchStudentProject/1.0 (learning project; contact: your-email@example.com)"}
DELAY = 2  # seconds between requests: be polite
FIELDS = ["file", "company", "year", "source_url", "pages", "bytes", "sha256", "downloaded_on"]
robots = {}


def allowed(url):
    root = "{0.scheme}://{0.netloc}".format(urlparse(url))
    if root not in robots:
        rp = RobotFileParser(root + "/robots.txt")
        try:
            rp.read()
        except Exception:
            rp = None
        robots[root] = rp
    rp = robots[root]
    return rp is None or rp.can_fetch(HEADERS["User-Agent"], url)


def download(list_file):
    """Download every PDF in list_file. Returns {file_path: source_url}."""
    sources = {}
    for line in open(list_file, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [x.strip() for x in line.split(",", 2)]
        if len(parts) != 3:
            print("skip (use company,year,url):", line)
            continue
        company, year, url = parts
        path = RAW / company / f"{company}_ar_{year}.pdf"
        if path.exists():
            print("skip (already have)", path)
            continue
        if not allowed(url):
            print("BLOCKED by robots.txt, download manually in browser:", url)
            continue
        r = requests.get(url, headers=HEADERS, timeout=60)
        if r.status_code != 200:
            print("failed", r.status_code, url)
            continue
        if not r.content.startswith(b"%PDF"):
            print("NOT a PDF (probably a web page), skipped:", url)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(r.content)
        sources[path.as_posix()] = url
        print("saved", path, len(r.content), "bytes")
        time.sleep(DELAY)
    return sources


def rebuild_manifest(new_sources):
    old = {}
    if MANIFEST.exists():
        with open(MANIFEST, newline="", encoding="utf-8") as f:
            old = {row.get("file", ""): row for row in csv.DictReader(f)}
    rows = []
    for p in sorted(RAW.rglob("*.pdf")):
        key = p.as_posix()
        prev = old.get(key, {})
        data = p.read_bytes()
        rows.append({
            "file": key,
            "company": p.parent.name,
            "year": p.stem.split("_")[-1],
            "source_url": new_sources.get(key) or prev.get("source_url", ""),
            "pages": len(fitz.open(p)),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest()[:16],
            "downloaded_on": prev.get("downloaded_on") or date.today().isoformat(),
        })
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(len(rows), "files,", sum(r["pages"] for r in rows), "pages")


if __name__ == "__main__":
    new = download(sys.argv[1]) if len(sys.argv) > 1 else {}
    rebuild_manifest(new)