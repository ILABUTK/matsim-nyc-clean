#!/usr/bin/env python3
"""Publication-style mode-share and score-convergence charts from MATSim stats files."""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PALETTE = ["#3366cc", "#dc3912", "#ff9900", "#109618", "#990099",
           "#0099c6", "#dd4477", "#66aa00", "#b82e2e", "#316395", "#994499"]


def plot_mode_share(modestats_path, out_path):
    df = pd.read_csv(modestats_path, sep="\t")
    modes = [c for c in df.columns if c != "Iteration"]
    fig, ax = plt.subplots(figsize=(8, 5))
    for mode, color in zip(modes, PALETTE):
        ax.plot(df["Iteration"], df[mode] * 100, marker="o", label=mode, color=color)
    ax.set_xlabel("iteration")
    ax.set_ylabel("mode share (%)")
    ax.set_title("Mode share by iteration")
    ax.legend(loc="center left", bbox_to_anchor=(1.0, 0.5))
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_score_convergence(scorestats_path, out_path):
    df = pd.read_csv(scorestats_path, sep="\t")
    fig, ax = plt.subplots(figsize=(8, 5))
    for col, color in zip(["avg. EXECUTED", "avg. WORST", "avg. AVG", "avg. BEST"], PALETTE):
        ax.plot(df["ITERATION"], df[col], marker="o", label=col.replace("avg. ", ""), color=color)
    ax.set_xlabel("iteration")
    ax.set_ylabel("average agent score")
    ax.set_title("Score convergence")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path, help="MATSim output directory, e.g. output/bqx-8mph-newparams")
    parser.add_argument("--prefix", default="BUILT")
    parser.add_argument("--out", type=Path, default=Path("analysis/output"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    plot_mode_share(args.run_dir / f"{args.prefix}.modestats.txt", args.out / "mode_share.png")
    plot_score_convergence(args.run_dir / f"{args.prefix}.scorestats.txt", args.out / "score_convergence.png")
    print(f"wrote charts to {args.out}")


if __name__ == "__main__":
    main()
