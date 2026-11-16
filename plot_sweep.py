"""Figure for section 4: rank and magnitude separation across the lambda sweep.

Reads results/ceiling_sweep.csv (experiment_ceiling.py) and writes
results/figures/fig_d_lambda_sweep.{pdf,png}. Thin lines are treebanks, thick
lines the median across treebanks. No network; seconds.
"""
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent
df = pd.read_csv(ROOT / "results" / "ceiling_sweep.csv")
df["divergence"] = df["magnitude_sep"] - df["rank_sep"]
plt.rcParams.update({"font.size": 9, "font.family": "serif", "axes.spines.top": False, "axes.spines.right": False})
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.5), sharex=True)
panels = [("rank_sep", "rank separation\n(head minus word, P(adv))", "#2a6fb0"),
          ("magnitude_sep", "magnitude separation\n(head minus word, median rel. red.)", "#e08a2e"),
          ("divergence", "divergence\n(magnitude minus rank)", "#555555")]
for ax, (col, lab, c) in zip(axes, panels):
    for _, g in df.groupby("treebank_id"):
        ax.plot(g["lam"], g[col], color=c, alpha=0.18, lw=0.7)
    med = df.groupby("lam")[col].median()
    ax.plot(med.index, med.values, color=c, lw=2)
    ax.axhline(0, color="k", lw=0.6, ls=":")
    ax.set_title(lab, fontsize=8)
    ax.set_xlabel("λ")
axes[0].set_ylabel("separation")
fig.supxlabel("λ = share of nodes kept in the attested order (0 = B1 uniform, 1 = attested sentence)", fontsize=8)
fig.tight_layout()
out = ROOT / "results" / "figures"
fig.savefig(out / "fig_d_lambda_sweep.pdf", metadata={"CreationDate": None})
fig.savefig(out / "fig_d_lambda_sweep.png", dpi=200)
print("wrote", out / "fig_d_lambda_sweep.pdf")
