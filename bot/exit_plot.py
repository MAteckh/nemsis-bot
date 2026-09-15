"""
exit_plot.py — EXIT STRUCTURE v1 heatmapid PARIS backtesti tulemustest.
Iga lahter naitab neto R/tehing JA tehingute arvu.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def joonista(csv, y_veerg, x_veerg, fail, pealkiri, y_silt, x_silt):
    d = pd.read_csv(os.path.join(JUUR, csv))
    y = sorted(d[y_veerg].unique())
    x = sorted(d[x_veerg].unique())
    V = np.full((len(y), len(x)), np.nan)
    N = np.full((len(y), len(x)), np.nan)
    for _, r in d.iterrows():
        i, j = y.index(r[y_veerg]), x.index(r[x_veerg])
        V[i, j] = r["neto"]
        N[i, j] = r["n"]
    lim = np.nanmax(np.abs(V))
    fig, ax = plt.subplots(figsize=(1.9 * len(x) + 3, 1.1 * len(y) + 3))
    im = ax.imshow(V, cmap="RdYlGn", aspect="auto", vmin=-lim, vmax=lim)
    ax.set_xticks(range(len(x)))
    ax.set_xticklabels([f"{v:g}" for v in x])
    ax.set_yticks(range(len(y)))
    ax.set_yticklabels([f"{v:g}" for v in y])
    ax.set_xlabel(x_silt)
    ax.set_ylabel(y_silt)
    for i in range(len(y)):
        for j in range(len(x)):
            if np.isfinite(V[i, j]):
                ax.text(j, i, f"{V[i, j]:+.4f}\nn={int(N[i, j]):,}".replace(",", " "),
                        ha="center", va="center", fontsize=8.5)
    ax.set_title(pealkiri, fontsize=11, pad=12)
    fig.colorbar(im, ax=ax, fraction=0.035, label="neto R / tehing")
    fig.tight_layout()
    fig.savefig(os.path.join(JUUR, fail), dpi=140)
    plt.close(fig)
    print(f"  kirjutatud {fail}")
    return V, N, y, x


if __name__ == "__main__":
    print("=== HEATMAPID (paris backtesti tulemused) ===")
    V1, N1, sl, tp = joonista(
        "EXIT_SL_TP_GRID.csv", "sl", "tp", "EXIT_SL_TP_HEATMAP.png",
        "EXIT STRUCTURE v1 — JUHUSLIK SISENEMINE, SL x TP (max hold 20)\n"
        "neto R/tehing, 15 paari, 2006-2026, kuludega",
        "SL (x ATR)", "TP (R)")
    V2, N2, hd, tp2 = joonista(
        "EXIT_HOLD_TP_GRID.csv", "hold", "tp", "EXIT_HOLD_TP_HEATMAP.png",
        "EXIT STRUCTURE v1 — JUHUSLIK SISENEMINE, MAX HOLD x TP (SL 1.5 ATR)\n"
        "neto R/tehing, 15 paari, 2006-2026, kuludega",
        "max hold (baari)", "TP (R)")
    print(f"\n  SLxTP: positiivseid ruute {int(np.nansum(V1 > 0))}/{V1.size}, "
          f"vahemik {np.nanmin(V1):+.4f} .. {np.nanmax(V1):+.4f} R")
    print(f"  HOLDxTP: positiivseid ruute {int(np.nansum(V2 > 0))}/{V2.size}, "
          f"vahemik {np.nanmin(V2):+.4f} .. {np.nanmax(V2):+.4f} R")
