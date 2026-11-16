"""Record the licence of every analysed treebank, as UD v2.14 states it.

Reads the machine-readable "License:" line from each treebank's README at the
r2.14 tag on GitHub and writes results/treebank_licences.csv. Network needed;
the CSV is committed so nothing downstream depends on running this.
"""
from __future__ import annotations

import csv
import re
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
TAG = "r2.14"


def readme(repo: str) -> str:
    for name in ("README.md", "README.txt"):
        url = f"https://raw.githubusercontent.com/UniversalDependencies/{repo}/{TAG}/{name}"
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            continue
    raise RuntimeError(f"no README for {repo} at {TAG}")


def main() -> None:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    status = {r["treebank_id"]: r["status"] for r in csv.DictReader((ROOT / "results" / "treebank_manifest.csv").open(encoding="utf-8"))}
    rows = []
    for t in cfg["treebanks"]:
        if status.get(t["id"]) != "ANALYZED":
            continue
        m = re.search(r"^License:\s*(.+?)\s*$", readme(t["repo"]), re.M)
        rows.append({"treebank_id": t["id"], "repo": t["repo"], "family": t["family"],
                     "licence": m.group(1) if m else "NOT FOUND", "source": f"{t['repo']}@{TAG}/README"})
        print(rows[-1]["treebank_id"], rows[-1]["licence"])
    with (ROOT / "results" / "treebank_licences.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
