"""
hm_plot.py — HEAT MAP v1 maatriksid ja PNG-d. Iga lahter naitab
mootu JA tehingute arvu — valimi suurust ei peideta.
"""
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import hm_engine as H

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = pd.read_csv(os.path.join(JUUR, "HEAT_MAP_V1_RESULTS.csv"))
T = pd.read_csv(os.path.join(JUUR, "HEAT_MAP_V1_TRADES.csv"))
# CSV-st tulevad ajad segavormingus (D1 kuupaev, H1 kuupaev+kell) ja
# rezhiimilipud tekstina -> teisendame selgesonaliselt
T["aeg"] = pd.to_datetime(T["aeg"], format="mixed")
for _rz in H.REZIIMID:
    T[_rz] = T[_rz].astype(str).str.strip().str.lower().eq("true")
MIN_N = 20


def maatriks(rada, ulatus, moot):
    v = pd.DataFrame(index=H.PAARID, columns=H.STRAT, dtype=float)
    n = pd.DataFrame(index=H.PAARID, columns=H.STRAT, dtype=float)
    s = R[(R["rada"] == rada) & (R["ulatus"] == ulatus)]
    for _, r in s.iterrows():
        if r["paar"] in v.index and r["strateegia"] in v.columns:
            v.loc[r["paar"], r["strateegia"]] = r[moot]
            n.loc[r["paar"], r["strateegia"]] = r["n"]
    return v, n


def joonista(v, n, pealkiri, fail, ymm="RdYlGn", vmin=None, vmax=None,
             fmt="{:+.3f}"):
    fig, ax = plt.subplots(figsize=(9.5, 0.45 * len(v) + 2.6))
    A = v.values.astype(float)
    lim = np.nanmax(np.abs(A)) if vmin is None else None
    im = ax.imshow(A, cmap=ymm, aspect="auto",
                   vmin=vmin if vmin is not None else -lim,
                   vmax=vmax if vmax is not None else lim)
    ax.set_xticks(range(len(v.columns)))
    ax.set_xticklabels([c.replace("_", "\n") for c in v.columns], fontsize=9)
    ax.set_yticks(range(len(v.index)))
    ax.set_yticklabels(v.index, fontsize=9)
    for i in range(A.shape[0]):
        for j in range(A.shape[1]):
            if np.isfinite(A[i, j]):
                nn = n.values[i, j]
                ax.text(j, i, fmt.format(A[i, j]) +
                        (f"\nn={int(nn)}" if np.isfinite(nn) else ""),
                        ha="center", va="center", fontsize=7.2)
            else:
                ax.text(j, i, "n/a", ha="center", va="center",
                        fontsize=7.2, color="grey")
    ax.set_title(pealkiri, fontsize=11, pad=12)
    fig.colorbar(im, ax=ax, fraction=0.035)
    fig.tight_layout()
    fig.savefig(os.path.join(JUUR, fail), dpi=140)
    plt.close(fig)
    print(f"  kirjutatud {fail}")


def rezhiimi_maatriksid(rada, ulatus_eesliide="OOS_"):
    """paar x rezhiim ja strateegia x rezhiim, neto oodatav vaartus."""
    pr = pd.DataFrame(index=H.PAARID, columns=H.REZIIMID, dtype=float)
    prn = pd.DataFrame(index=H.PAARID, columns=H.REZIIMID, dtype=float)
    sr = pd.DataFrame(index=H.STRAT, columns=H.REZIIMID, dtype=float)
    srn = pd.DataFrame(index=H.STRAT, columns=H.REZIIMID, dtype=float)
    t = T[T["rada"] == rada].copy()
    algus = [x for x in (H.JAOTUS_H1 if rada == "A_H1" else H.JAOTUS_D1)
             if x[0] == "OOS"][0][1]
    if ulatus_eesliide == "OOS_":
        t = t[t["aeg"] >= pd.Timestamp(algus)]
    for rz in H.REZIIMID:
        g = t[t[rz]]
        for p in H.PAARID:
            x = g[g["paar"] == p]["neto_r"]
            if len(x) >= MIN_N:
                pr.loc[p, rz], prn.loc[p, rz] = x.mean(), len(x)
        for s in H.STRAT:
            x = g[g["strateegia"] == s]["neto_r"]
            if len(x) >= MIN_N:
                sr.loc[s, rz], srn.loc[s, rz] = x.mean(), len(x)
    return pr, prn, sr, srn


if __name__ == "__main__":
    print("=== PNG-d ===")
    v, n = maatriks("B_D1", "OOS", "oodatav")
    joonista(v, n, "HEAT MAP v1 — RADA B (D1) OOS 2018-2026\n"
                   "neto oodatav vaartus R-uhikutes tehingu kohta",
             "HEAT_MAP_V1_OOS_HEATMAP.png")
    vA, nA = maatriks("A_H1", "OOS", "oodatav")
    fig, axes = plt.subplots(2, 2, figsize=(17, 13))
    plokid = [("B_D1", "ALL", "oodatav", "A) neto oodatav R/tehing (D1 KOGU valim)", "{:+.3f}"),
              ("B_D1", "OOS", "sharpe", "B) OOS Sharpe (D1)", "{:+.2f}"),
              ("B_D1", "OOS", "pf", "C) OOS Profit Factor (D1)", "{:.2f}"),
              ("B_D1", "OOS", "maxdd", "D) OOS max drawdown % (D1, 1% risk)", "{:.1f}")]
    for ax, (rd, ul, mt, pk, fm) in zip(axes.ravel(), plokid):
        vv, nn = maatriks(rd, ul, mt)
        A = vv.values.astype(float)
        if mt == "pf":
            A2, cm, lo, hi = A, "RdYlGn", 0.5, 1.5
        elif mt == "maxdd":
            A2, cm, lo, hi = A, "RdYlGn", float(np.nanmin(A)), 0.0
        else:
            lim = np.nanmax(np.abs(A))
            A2, cm, lo, hi = A, "RdYlGn", -lim, lim
        im = ax.imshow(A2, cmap=cm, aspect="auto", vmin=lo, vmax=hi)
        ax.set_xticks(range(len(vv.columns)))
        ax.set_xticklabels([c.replace("_", "\n") for c in vv.columns], fontsize=8)
        ax.set_yticks(range(len(vv.index)))
        ax.set_yticklabels(vv.index, fontsize=8)
        for i in range(A.shape[0]):
            for j in range(A.shape[1]):
                if np.isfinite(A[i, j]):
                    ax.text(j, i, fm.format(A[i, j]) +
                            f"\nn={int(nn.values[i,j])}", ha="center",
                            va="center", fontsize=6.3)
                else:
                    ax.text(j, i, "n/a", ha="center", va="center",
                            fontsize=6.3, color="grey")
        ax.set_title(pk, fontsize=10)
        fig.colorbar(im, ax=ax, fraction=0.035)
    fig.suptitle("NEMSIS HEAT MAP v1 — 15 paari x 4 strateegiat, "
                 "paris tehingud, kuludega", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(JUUR, "HEAT_MAP_V1_HEATMAP.png"), dpi=130)
    plt.close(fig)
    print("  kirjutatud HEAT_MAP_V1_HEATMAP.png")

    print("\n=== MAATRIKS: PAAR x STRATEEGIA, OOS neto oodatav (R/tehing) ===")
    for rada in ("B_D1", "A_H1"):
        vv, nn = maatriks(rada, "OOS", "oodatav")
        print(f"\n{rada}:")
        print(f"{'paar':<9s}" + "".join(f"{c[:12]:>16s}" for c in vv.columns))
        for p in vv.index:
            rida = f"{p:<9s}"
            for c in vv.columns:
                x, k = vv.loc[p, c], nn.loc[p, c]
                rida += (f"{x:>+10.3f}/{int(k):<5d}" if np.isfinite(x) else f"{'n/a':>16s}")
            print(rida)

    for rada in ("B_D1", "A_H1"):
        pr, prn, sr, srn = rezhiimi_maatriksid(rada)
        print(f"\n=== {rada}: PAAR x REZHIIM (OOS, neto R/tehing, min n={MIN_N}) ===")
        print(f"{'paar':<9s}" + "".join(f"{c[:14]:>17s}" for c in pr.columns))
        for p in pr.index:
            rida = f"{p:<9s}"
            for c in pr.columns:
                x, k = pr.loc[p, c], prn.loc[p, c]
                rida += (f"{x:>+10.3f}/{int(k):<6d}" if np.isfinite(x) else f"{'n/a':>17s}")
            print(rida)
        print(f"\n=== {rada}: STRATEEGIA x REZHIIM (OOS, neto R/tehing) ===")
        print(f"{'strateegia':<18s}" + "".join(f"{c[:14]:>17s}" for c in sr.columns))
        for s in sr.index:
            rida = f"{s:<18s}"
            for c in sr.columns:
                x, k = sr.loc[s, c], srn.loc[s, c]
                rida += (f"{x:>+10.3f}/{int(k):<6d}" if np.isfinite(x) else f"{'n/a':>17s}")
            print(rida)
