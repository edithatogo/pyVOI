#!/usr/bin/env python3
"""Run a bounded VOP health-economic workflow with a released voiage wheel.

This is developer/same-author research use.  It is not independent adoption,
clinical advice, or a validated policy estimate.  The VOP scenario parameters
remain owned by their pinned public repository revision.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path

import numpy as np


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vop-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--draws", type=int, default=500)
    parser.add_argument("--seed", type=int, default=20260727)
    args = parser.parse_args()
    if args.draws < 2:
        raise ValueError("--draws must be at least two")

    # Imported only after an explicit public VOP source root is supplied.
    import sys

    sys.path.insert(0, str(args.vop_root / "src"))
    from vop_poc_nz.cea_model_core import run_cea
    from vop_poc_nz.pipeline.analysis import load_parameters

    from voiage import __version__
    from voiage.methods.basic import evpi

    parameter_path = args.vop_root / "src/vop_poc_nz/parameters.yaml"
    params = load_parameters(str(parameter_path))["hpv_vaccination"]
    rng = np.random.default_rng(args.seed)
    net_benefit = np.empty((args.draws, 2), dtype=float)
    wtp = 50_000.0
    for index in range(args.draws):
        draw = copy.deepcopy(params)
        draw["costs"]["health_system"]["new_treatment"] = [
            float(value * rng.lognormal(mean=0.0, sigma=0.10))
            for value in draw["costs"]["health_system"]["new_treatment"]
        ]
        draw["costs"]["health_system"]["standard_care"] = [
            float(value * rng.lognormal(mean=0.0, sigma=0.10))
            for value in draw["costs"]["health_system"]["standard_care"]
        ]
        draw["qalys"]["new_treatment"] = [
            float(value * rng.lognormal(mean=0.0, sigma=0.03))
            for value in draw["qalys"]["new_treatment"]
        ]
        draw["qalys"]["standard_care"] = [
            float(value * rng.lognormal(mean=0.0, sigma=0.03))
            for value in draw["qalys"]["standard_care"]
        ]
        result = run_cea(draw, perspective="health_system")
        net_benefit[index] = (
            wtp * result["qalys_standard_care"] - result["cost_standard_care"],
            wtp * result["qalys_new_treatment"] - result["cost_new_treatment"],
        )

    args.output.mkdir(parents=True, exist_ok=True)
    draws_path = args.output / "hpv_vaccination_net_benefit.csv"
    with draws_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["standard_care", "hpv_vaccination"])
        writer.writerows(net_benefit.tolist())
    result_path = args.output / "receipt.json"
    result_path.write_text(
        json.dumps(
            {
                "workflow": "vop_hpv_vaccination_same_author_research_use_v1",
                "source": "edithatogo/vop_poc_nz",
                "parameter_file": str(parameter_path),
                "parameter_sha256": _sha256(parameter_path),
                "analysis": "health-system HPV-vaccination Markov scenario with deterministic cost and QALY uncertainty draws",
                "seed": args.seed,
                "draws": args.draws,
                "willingness_to_pay_nzd_per_qaly": wtp,
                "voiage_version": __version__,
                "net_benefit_csv_sha256": _sha256(draws_path),
                "evpi_nzd_per_cohort": evpi(net_benefit),
                "scope": "Developer/same-author research use; not independent adoption, clinical advice, or a policy estimate.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
