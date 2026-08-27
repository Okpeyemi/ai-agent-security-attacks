"""Generate the Working Note figures from the recorded experiment data.

Run: python docs/figures/make_figures.py  -> writes PNGs next to this file.
Reusable as-is in the final submission notebook.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parent
plt.rcParams.update({"figure.dpi": 130, "font.size": 11, "axes.grid": True,
                     "axes.axisbelow": True, "grid.alpha": 0.3})
BLUE, GREEN, RED, GREY = "#2563eb", "#059669", "#dc2626", "#9ca3af"


def fig1_public_trajectory():
    labels = ["baseline\n(no forge)", "forge", "+frac 0.95", "+frac 0.97", "+frac 0.98"]
    scores = [52.865, 75.420, 83.250, 86.895, 86.985]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    bars = ax.bar(labels, scores, color=[GREY, BLUE, BLUE, BLUE, GREEN])
    for b, s in zip(bars, scores):
        ax.text(b.get_x() + b.get_width() / 2, s + 1, f"{s:.1f}", ha="center", fontsize=9)
    ax.set_ylabel("public aggregate score")
    ax.set_title("Public score: lever stack (forge, then fill-fraction) — ceiling ~87")
    ax.set_ylim(0, 100)
    fig.tight_layout(); fig.savefig(OUT / "fig1_public_trajectory.png"); plt.close(fig)


def fig2_yield_fit():
    n = np.array([360, 400, 450]); s = np.array([32.4, 36.0, 40.5])
    xs = np.linspace(0, 500, 50)
    fig, ax = plt.subplots(figsize=(6.0, 3.6))
    ax.plot(xs, 0.09 * xs, color=BLUE, lw=2, label="S = 0.09 · N_eff")
    ax.scatter(n, s, color=RED, zorder=5, label="measured (local SDK scorer)")
    ax.set_xlabel("N_eff  (firing candidates within replay budget)")
    ax.set_ylabel("normalized score")
    ax.set_title("Yield model: score is linear in N_eff (R²=1.0)")
    ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "fig2_yield_fit.png"); plt.close(fig)


def fig3_forge_latency():
    groups = ["gpt_oss\nexfil", "gpt_oss\ndeputy", "gemma\nexfil", "gemma\ndeputy"]
    plain = [4.7, 3.8, 0.4, 0.7]; forge = [0.8, 1.2, 0.4, 0.7]
    x = np.arange(len(groups)); w = 0.38
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    ax.bar(x - w / 2, plain, w, label="plain", color=GREY)
    ax.bar(x + w / 2, forge, w, label="forged", color=GREEN)
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_ylabel("latency  (s / candidate, real GGUF)")
    ax.set_title("Forge latency: ~6× on gpt_oss, neutral on gemma (fire=100%)")
    ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "fig3_forge_latency.png"); plt.close(fig)


def fig4_survival():
    families = ["plaintext\nexfil", "encoded\nexfil", "confused\ndeputy"]
    guards = ["Naive", "Data-inspect", "Read→share", "Aggr-taint"]
    # 1 = fires (survives), 0 = blocked, -1 = never fires (n/a)
    M = np.array([[0, 0, 1, 0],
                  [-1, -1, -1, -1],
                  [1, 1, 1, 1]])
    cmap = matplotlib.colors.ListedColormap([GREY, RED, GREEN])  # -1 grey, 0 red, 1 green
    fig, ax = plt.subplots(figsize=(6.2, 3.2))
    ax.imshow(M, cmap=cmap, vmin=-1, vmax=1, aspect="auto")
    ax.set_xticks(range(len(guards))); ax.set_xticklabels(guards)
    ax.set_yticks(range(len(families))); ax.set_yticklabels(families)
    txt = {1: "fires", 0: "blocked", -1: "n/a"}
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, txt[M[i, j]], ha="center", va="center",
                    color="white", fontsize=9, fontweight="bold")
    ax.set_title("Survival vs strict-guardrail panel (held-out proxy)")
    ax.grid(False)
    fig.tight_layout(); fig.savefig(OUT / "fig4_survival.png"); plt.close(fig)


if __name__ == "__main__":
    fig1_public_trajectory(); fig2_yield_fit(); fig3_forge_latency(); fig4_survival()
    print("wrote:", ", ".join(p.name for p in sorted(OUT.glob("fig*.png"))))
