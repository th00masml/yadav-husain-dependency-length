"""The family-level robustness check reads committed results and must agree with them."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def fs():
    import experiment_family_sensitivity as efs
    return efs.main()


def test_every_analysed_treebank_has_a_family(fs):
    assert fs["n_treebanks"] == 26
    assert sum(fs["treebanks_per_family"].values()) == 26


def test_trend_negative_in_every_family(fs):
    assert all(v["r"] < -0.8 and v["slope"] < 0 for v in fs["per_family"].values())


def test_no_family_drives_the_pooled_result(fs):
    assert all(v["r"] < -0.9 for v in fs["leave_one_family_out"].values())


def test_mixed_model_slope_excludes_zero(fs):
    lo, hi = fs["mixed_model"]["lam_ci95"]
    assert hi < 0 and fs["mixed_model"]["converged"]


def test_committed_json_matches_recomputation(fs):
    committed = json.loads((ROOT / "results" / "family_sensitivity.json").read_text(encoding="utf-8"))
    assert committed["pooled_centred"]["r"] == pytest.approx(fs["pooled_centred"]["r"])
    assert committed["mixed_model"]["lam_coef"] == pytest.approx(fs["mixed_model"]["lam_coef"], rel=1e-6)


def test_every_analysed_treebank_has_a_recorded_licence():
    import csv
    lic = list(csv.DictReader((ROOT / "results" / "treebank_licences.csv").open(encoding="utf-8")))
    assert len(lic) == 26 and all(r["licence"].startswith("CC BY") for r in lic)
