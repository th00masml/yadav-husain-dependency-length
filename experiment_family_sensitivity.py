"""Does the lambda-sweep result survive the uneven typological sample?

15 of the 26 analysed treebanks are Indo-European, so "the trend holds in 26/26
treebanks" counts one family many times. This script re-reads the committed
sweep (results/ceiling_sweep.csv, written by experiment_ceiling.py) and asks the
same question with language family as the unit. Added 2026-11, after the main
analysis; it is a robustness check, not a pre-registered test.

Outcome: divergence = magnitude_sep - rank_sep at each (treebank, lambda).

1. Per family: correlation of lambda with divergence after centring each
   treebank on its own mean (the within-language coordinate of section 4.3).
2. Leave one family out: the same centred correlation with each family removed.
3. Mixed model: divergence ~ lambda, random intercept and lambda slope by
   family, plus a variance component for treebank within family.
4. Family-level cluster bootstrap of the pooled within-treebank slope:
   resample families with replacement, keep all their treebanks.

Writes results/family_sensitivity.json and prints a summary. Needs pandas,
numpy, statsmodels, PyYAML; no network, runs in seconds.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parent
SEED = 20260919


def load() -> pd.DataFrame:
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    fam = {t["id"]: t["family"] for t in cfg["treebanks"]}
    df = pd.read_csv(ROOT / "results" / "ceiling_sweep.csv")
    df["family"] = df["treebank_id"].map(fam)
    if df["family"].isna().any():
        raise ValueError(f"no family for {sorted(df.loc[df.family.isna(), 'treebank_id'].unique())}")
    df["divergence"] = df["magnitude_sep"] - df["rank_sep"]
    df["div_c"] = df["divergence"] - df.groupby("treebank_id")["divergence"].transform("mean")
    df["lam_c"] = df["lam"] - df.groupby("treebank_id")["lam"].transform("mean")
    return df


def centred_r(d: pd.DataFrame) -> float:
    return float(np.corrcoef(d["lam_c"], d["div_c"])[0, 1])


def centred_slope(d: pd.DataFrame) -> float:
    return float((d["lam_c"] * d["div_c"]).sum() / (d["lam_c"] ** 2).sum())


def main() -> dict:
    df = load()
    fams = sorted(df["family"].unique())
    out: dict = {"note": "post hoc robustness check of section 4.3 by language family; see module docstring",
                 "n_treebanks": int(df["treebank_id"].nunique()), "n_families": len(fams),
                 "treebanks_per_family": {f: int(df.loc[df.family == f, "treebank_id"].nunique()) for f in fams}}

    out["pooled_centred"] = {"r": centred_r(df), "slope": centred_slope(df)}
    out["per_family"] = {f: {"n_treebanks": out["treebanks_per_family"][f], "r": centred_r(df[df.family == f]),
                             "slope": centred_slope(df[df.family == f])} for f in fams}
    out["leave_one_family_out"] = {f: {"r": centred_r(df[df.family != f]), "slope": centred_slope(df[df.family != f])}
                                   for f in fams}
    ie = df.family == "Indo-European"
    out["indo_european_vs_rest"] = {"indo_european": {"n_treebanks": int(df[ie].treebank_id.nunique()), "r": centred_r(df[ie]), "slope": centred_slope(df[ie])},
                                    "other": {"n_treebanks": int(df[~ie].treebank_id.nunique()), "r": centred_r(df[~ie]), "slope": centred_slope(df[~ie])}}

    rng = np.random.default_rng(SEED)
    by_f = {f: df[df.family == f] for f in fams}
    boots = [centred_slope(pd.concat([by_f[f] for f in rng.choice(fams, len(fams))])) for _ in range(5000)]
    out["family_cluster_bootstrap_slope"] = {"n_resamples": 5000, "ci95": [float(x) for x in np.percentile(boots, [2.5, 97.5])],
                                             "share_negative": float(np.mean(np.array(boots) < 0))}

    import statsmodels.formula.api as smf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.mixedlm("divergence ~ lam", df, groups=df["family"], re_formula="~lam",
                        vc_formula={"treebank": "0 + C(treebank_id)"}).fit(reml=True)
    ci = m.conf_int().loc["lam"]
    out["mixed_model"] = {"formula": "divergence ~ lam + (1 + lam | family) + (1 | treebank:family)",
                          "lam_coef": float(m.params["lam"]), "lam_se": float(m.bse["lam"]),
                          "lam_ci95": [float(ci[0]), float(ci[1])], "lam_p": float(m.pvalues["lam"]),
                          "converged": bool(m.converged)}

    (ROOT / "results" / "family_sensitivity.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    o = main()
    print(f"pooled centred r = {o['pooled_centred']['r']:.3f}, slope = {o['pooled_centred']['slope']:.3f}")
    for f, v in o["per_family"].items():
        print(f"  {f:14s} n={v['n_treebanks']:2d}  r = {v['r']:+.3f}  slope = {v['slope']:+.3f}")
    lofo = o["leave_one_family_out"]
    print(f"leave-one-family-out r in [{min(v['r'] for v in lofo.values()):.3f}, {max(v['r'] for v in lofo.values()):.3f}]")
    print("IE vs rest:", {k: round(v["r"], 3) for k, v in o["indo_european_vs_rest"].items()})
    print("family cluster bootstrap slope CI:", o["family_cluster_bootstrap_slope"])
    print("mixed model:", o["mixed_model"])
