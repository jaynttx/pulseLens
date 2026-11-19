"""
Benchmark: deep rPPG (FacePhys) vs classical rPPG (POS / pulse)
against a reference heart-rate reading (smartwatch / phone PPG).

The two apps cannot share the webcam, so they are run one at a time and
each has its own reference reading:
    FacePhys error = facephys_bpm - ref_facephys_bpm
    pulse error    = pulse_bpm    - ref_pulse_bpm
A row may have only one method filled in.

Usage:
    pip install -r requirements.txt
    python analyze.py                 # reads results.csv
    python analyze.py my_results.csv  # or any CSV with the same columns

Outputs (in benchmark/output/):
    summary.csv        MAE, RMSE, mean bias per method and condition
    error_by_condition.png   bar chart of MAE per condition
    agreement.png      estimate vs its own reference (ideal = diagonal)
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "output"
# estimate column -> (reference column, display name)
METHODS = {
    "facephys_bpm": ("ref_facephys_bpm", "FacePhys (deep SSM)"),
    "pulse_bpm": ("ref_pulse_bpm", "pulse (classical POS)"),
}
COLORS = ["#5b5bd6", "#e5484d"]


def metrics(err: pd.Series) -> dict:
    err = err.dropna()
    if err.empty:
        return {"n": 0, "MAE": np.nan, "RMSE": np.nan, "bias": np.nan}
    return {
        "n": int(err.size),
        "MAE": float(err.abs().mean()),          # mean absolute error, bpm
        "RMSE": float(np.sqrt((err ** 2).mean())),  # penalises big misses more
        "bias": float(err.mean()),               # + = over-estimates, - = under
    }


def main(csv_path: Path) -> None:
    df = pd.read_csv(csv_path)
    needed = {"condition", "trial", *METHODS, *(ref for ref, _ in METHODS.values())}
    missing = needed - set(df.columns)
    if missing:
        sys.exit(f"{csv_path.name} is missing columns: {', '.join(sorted(missing))}")
    for col in [*METHODS, *(ref for ref, _ in METHODS.values())]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # error per method, only where both estimate and its own reference exist
    for col, (ref, _) in METHODS.items():
        df[col + "_err"] = df[col] - df[ref]
    err_cols = [c + "_err" for c in METHODS]
    df = df.dropna(subset=err_cols, how="all")
    if df.empty:
        sys.exit("No rows with an estimate and its matching reference yet. Fill results.csv first.")
    OUT.mkdir(exist_ok=True)

    rows = []
    for col, (_, name) in METHODS.items():
        rows.append({"method": name, "condition": "ALL", **metrics(df[col + "_err"])})
        for cond, g in df.groupby("condition", sort=False):
            rows.append({"method": name, "condition": cond, **metrics(g[col + "_err"])})
    summary = pd.DataFrame(rows)
    summary.to_csv(OUT / "summary.csv", index=False)

    pd.set_option("display.width", 120)
    print("\n=== Error vs each method's own reference (bpm) ===")
    print(summary.round(2).to_string(index=False))

    # Chart 1: MAE per condition, both methods side by side
    per_cond = summary[summary.condition != "ALL"].pivot(
        index="condition", columns="method", values="MAE"
    ).reindex(index=df.condition.unique(), columns=[name for _, name in METHODS.values()])
    ax = per_cond.plot(kind="bar", figsize=(8, 4.5), rot=0, color=COLORS)
    ax.set_ylabel("Mean absolute error (bpm)  - lower is better")
    ax.set_xlabel("")
    ax.set_title("Heart-rate error by condition: deep vs classical")
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "error_by_condition.png", dpi=160)
    plt.close()

    # Chart 2: agreement scatter
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    vals = []
    for (col, (ref, name)), color in zip(METHODS.items(), COLORS):
        ok = df[[col, ref]].dropna()
        if ok.empty:
            continue
        ax.scatter(ok[ref], ok[col], label=f"{name} (n={len(ok)})", color=color, s=50, alpha=0.85)
        vals.extend(ok[ref].tolist() + ok[col].tolist())
    lo = min(vals) - 5
    hi = max(vals) + 5
    ax.plot([lo, hi], [lo, hi], "k--", lw=1, label="perfect agreement")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Reference heart rate for that run (bpm)")
    ax.set_ylabel("Camera estimate (bpm)")
    ax.set_title("Camera estimate vs reference")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "agreement.png", dpi=160)
    plt.close()

    print(f"\nSaved: {OUT / 'summary.csv'}")
    print(f"Saved: {OUT / 'error_by_condition.png'}")
    print(f"Saved: {OUT / 'agreement.png'}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "results.csv")
