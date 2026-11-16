"""Write the LaTeX tables the paper \\inputs, from committed results only.

paper/tab_treebanks.tex   26 analysed treebanks: family, sentences analysed,
                          non-projective rate, licence (UD v2.14 README).
paper/tab_family.tex      lambda-sweep robustness by language family
                          (results/family_sensitivity.json).
Run from the repository root:  python paper/make_tables.py
"""
import csv
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
order = [t["id"] for t in cfg["treebanks"]]
man = {r["treebank_id"]: r for r in csv.DictReader((ROOT / "results/treebank_manifest.csv").open(encoding="utf-8"))}
lic = {r["treebank_id"]: r for r in csv.DictReader((ROOT / "results/treebank_licences.csv").open(encoding="utf-8"))}
rows, tot = [], 0
for tb in order:
    m = man.get(tb)
    if not m or m["status"] != "ANALYZED":
        continue
    n = int(m["n_analyzed"]); tot += n
    rows.append(f"{tb.replace('_', chr(92) + '_')} & {lic[tb]['family']} & {n:,} & {100 * float(m['nonprojective_rate']):.1f} & {lic[tb]['licence']} \\\\")
rows.append("\\midrule")
rows.append(f"total ({len(rows) - 1} treebanks) & & {tot:,} & & \\\\")
head = ["\\begin{tabular}{llrrl}", "\\toprule", "treebank & family & sentences & non-proj.\\ \\% & licence \\\\", "\\midrule"]
(ROOT / "paper/tab_treebanks.tex").write_text("\n".join(head + rows + ["\\bottomrule", "\\end{tabular}"]) + "\n", encoding="utf-8")

fs = json.loads((ROOT / "results/family_sensitivity.json").read_text(encoding="utf-8"))
fr = [f"{f} & {v['n_treebanks']} & {v['r']:.2f} & {v['slope']:.2f} & {fs['leave_one_family_out'][f]['r']:.3f} \\\\"
      for f, v in sorted(fs["per_family"].items(), key=lambda kv: -kv[1]["n_treebanks"])]
fh = ["\\begin{tabular}{lrrrr}", "\\toprule", "family & treebanks & $r$ & slope & $r$ without family \\\\", "\\midrule"]
(ROOT / "paper/tab_family.tex").write_text("\n".join(fh + fr + ["\\bottomrule", "\\end{tabular}"]) + "\n", encoding="utf-8")
print("total sentences", tot, "treebanks", len(rows) - 2)
