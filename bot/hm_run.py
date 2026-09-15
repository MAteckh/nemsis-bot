"""
hm_run.py — jooksutab HEAT MAP v1 taisbacktesti ja kirjutab CSV-d.
"""
import os
import sys

import numpy as np
import pandas as pd

import hm_engine as H

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAJAD = {"A_H1": dict(tf="H1", ctx="4h", jaotus=H.JAOTUS_H1, lae=H.lae_h1),
         "B_D1": dict(tf="D1", ctx="W",  jaotus=H.JAOTUS_D1, lae=H.lae_d1)}


def aastaid(ix):
    return max((ix[-1] - ix[0]).days / 365.25, 1e-9)


def koik_tehingud():
    read = []
    for rada, cfg in RAJAD.items():
        for paar in H.PAARID:
            d = cfg["lae"](paar)
            if d is None or len(d) < 500:
                print(f"  {rada} {paar}: INSUFFICIENT DATA", flush=True)
                continue
            k = H.kontekst(d, cfg["ctx"])
            for strat in H.STRAT:
                t = H.simuleeri(d, k, strat, cfg["tf"], H.KULU_BP[paar])
                if len(t) == 0:
                    continue
                t.insert(0, "paar", paar)
                t.insert(0, "rada", rada)
                read.append(t)
            print(f"  {rada} {paar}: {d.index.min().date()} .. "
                  f"{d.index.max().date()}  {len(d)} baari", flush=True)
    return pd.concat(read, ignore_index=True)


def lisa_jaotus(T):
    T = T.copy()
    T["jaotus"] = "VALJAS"
    for rada, cfg in RAJAD.items():
        m0 = T["rada"] == rada
        for nimi, a, b in cfg["jaotus"]:
            m = m0 & (T["aeg"] >= pd.Timestamp(a)) & (T["aeg"] <= pd.Timestamp(b))
            T.loc[m, "jaotus"] = nimi
    return T


def moodikud_read(T):
    read = []
    for (rada, paar, strat), g in T.groupby(["rada", "paar", "strateegia"]):
        plokid = [("ALL", g)]
        for j in ("TRAIN", "VALID", "OOS"):
            plokid.append((j, g[g["jaotus"] == j]))
        oos = g[g["jaotus"] == "OOS"]
        for rz in H.REZIIMID:
            plokid.append((f"OOS_{rz}", oos[oos[rz]]))
            plokid.append((f"ALL_{rz}", g[g[rz]]))
        for silt, x in plokid:
            if len(x) == 0:
                continue
            a = aastaid(pd.DatetimeIndex(sorted(x["aeg"])))
            s = H.stat(x, a)
            if s is None:
                continue
            s.update(rada=rada, paar=paar, strateegia=strat, ulatus=silt,
                     algus=str(x["aeg"].min().date()),
                     lopp=str(x["aeg"].max().date()), aastaid=round(a, 2),
                     p=H.p_kahepoolne(s["t"]))
            read.append(s)
    v = ["rada", "paar", "strateegia", "ulatus", "algus", "lopp", "aastaid",
         "n", "wr", "bruto_r", "neto_r", "oodatav", "pf", "sharpe", "maxdd",
         "avg_win", "avg_loss", "avg_r", "kokku", "aastane", "teh_aastas",
         "t", "p"]
    return pd.DataFrame(read)[v]


def robustsus(T, kand):
    """Spread +25%, +50%, libisemine 2x, parameetri norgendus."""
    read = []
    for _, r in kand.iterrows():
        rada, paar, strat = r["rada"], r["paar"], r["strateegia"]
        cfg = RAJAD[rada]
        d = cfg["lae"](paar)
        k = H.kontekst(d, cfg["ctx"])
        a0, b0 = [x for x in cfg["jaotus"] if x[0] == "OOS"][0][1:]
        variandid = [
            ("baseline", dict(kulu=H.KULU_BP[paar], slip=H.SLIP_BP)),
            ("spread+25%", dict(kulu=H.KULU_BP[paar] * 1.25, slip=H.SLIP_BP)),
            ("spread+50%", dict(kulu=H.KULU_BP[paar] * 1.50, slip=H.SLIP_BP)),
            ("slip 2x", dict(kulu=H.KULU_BP[paar], slip=H.SLIP_BP * 2)),
            ("spread+50% & slip 2x",
             dict(kulu=H.KULU_BP[paar] * 1.50, slip=H.SLIP_BP * 2)),
        ]
        for nimi, kw in variandid:
            t = H.simuleeri(d, k, strat, cfg["tf"], kw["kulu"], slip_bp=kw["slip"])
            t = t[(t["aeg"] >= pd.Timestamp(a0)) & (t["aeg"] <= pd.Timestamp(b0))]
            if len(t) == 0:
                continue
            s = H.stat(t, aastaid(pd.DatetimeIndex(sorted(t["aeg"]))))
            read.append(dict(rada=rada, paar=paar, strateegia=strat,
                             variant=nimi, n=s["n"], oodatav=s["oodatav"],
                             pf=s["pf"], sharpe=s["sharpe"], maxdd=s["maxdd"],
                             neto_r=s["neto_r"], t=s["t"]))
        # parameetri norgendus: SL 1.25 ja 1.75 ATR
        for sl in (1.25, 1.75):
            vana = H.SL_ATR
            H.SL_ATR = sl
            t = H.simuleeri(d, k, strat, cfg["tf"], H.KULU_BP[paar])
            H.SL_ATR = vana
            t = t[(t["aeg"] >= pd.Timestamp(a0)) & (t["aeg"] <= pd.Timestamp(b0))]
            if len(t) == 0:
                continue
            s = H.stat(t, aastaid(pd.DatetimeIndex(sorted(t["aeg"]))))
            read.append(dict(rada=rada, paar=paar, strateegia=strat,
                             variant=f"SL {sl}xATR", n=s["n"],
                             oodatav=s["oodatav"], pf=s["pf"],
                             sharpe=s["sharpe"], maxdd=s["maxdd"],
                             neto_r=s["neto_r"], t=s["t"]))
        # Monte Carlo: tehingute jarjekorra permutatsioon -> maxDD jaotus
        t = H.simuleeri(d, k, strat, cfg["tf"], H.KULU_BP[paar])
        t = t[(t["aeg"] >= pd.Timestamp(a0)) & (t["aeg"] <= pd.Timestamp(b0))]
        if len(t) >= 20:
            rs = np.random.RandomState(20260915)
            x = t["neto_r"].values
            dds = []
            for _ in range(1000):
                y = rs.permutation(x)
                eq = np.cumprod(1 + H.RISK * y)
                dds.append(100 * float((eq / np.maximum.accumulate(eq) - 1).min()))
            read.append(dict(rada=rada, paar=paar, strateegia=strat,
                             variant="MC maxDD 5% kvantiil", n=len(x),
                             oodatav=float(x.mean()), pf=np.nan, sharpe=np.nan,
                             maxdd=float(np.quantile(dds, 0.05)),
                             neto_r=float(x.sum()), t=np.nan))
    return pd.DataFrame(read)


if __name__ == "__main__":
    print("=== TEHINGUTE GENEREERIMINE ===", flush=True)
    T = lisa_jaotus(koik_tehingud())
    print(f"\nkokku {len(T)} tehingut, "
          f"{T.groupby('rada').size().to_dict()}")
    T.to_csv(os.path.join(JUUR, "HEAT_MAP_V1_TRADES.csv"), index=False)

    R = moodikud_read(T)
    R.to_csv(os.path.join(JUUR, "HEAT_MAP_V1_RESULTS.csv"), index=False)
    print(f"tulemuseridu {len(R)}")

    # robustsus tugevaimatele OOS-kandidaatidele
    oos = R[(R["ulatus"] == "OOS") & (R["n"] >= 30)].copy()
    kand = oos.sort_values("oodatav", ascending=False).head(10)
    RB = robustsus(T, kand)
    RB.to_csv(os.path.join(JUUR, "HEAT_MAP_V1_ROBUSTNESS.csv"), index=False)
    print(f"robustsuseridu {len(RB)}")
    print("\nfailid kirjutatud:")
    for f in ("HEAT_MAP_V1_TRADES.csv", "HEAT_MAP_V1_RESULTS.csv",
              "HEAT_MAP_V1_ROBUSTNESS.csv"):
        p = os.path.join(JUUR, f)
        print(f"  {f}  {os.path.getsize(p)/1024:.0f} KB")

    # --- mitme testimise korrektsioon, reprodutseeritav -------------------
    print("\n=== MITME TESTIMISE KORREKTSIOON ===")
    o = R[(R["ulatus"] == "OOS") & (R["n"] >= 30)]
    lavi, labi = H.bh(list(o["p"].values), 0.05)
    pos = o[o["oodatav"] > 0]
    print(f"  OOS-lahtreid n>=30: {len(o)}, positiivse ootusega {len(pos)}")
    print(f"  BH q=0.05: lavi p={lavi:.4f}, 'labis' {len(labi)} lahtrit")
    print(f"  NEIST POSITIIVSEID: "
          f"{sum(1 for i in labi if o.iloc[i]['oodatav'] > 0)}")
    print(f"  positiivsetest p<0.05: {int((pos['p'] < 0.05).sum())}")
    print(f"  parim positiivne toores p: {pos['p'].min():.4f}"
          if len(pos) else "  positiivseid ei ole")
    print(f"  Bonferroni lavi: {0.05/max(len(o),1):.5f}")
    piv = R[R["ulatus"].isin(["VALID", "OOS"])].pivot_table(
        index=["rada", "paar", "strateegia"], columns="ulatus",
        values="oodatav").dropna()
    for rada in RAJAD:
        x = piv.loc[rada]
        m = (x["VALID"] > 0) & (x["OOS"] > 0)
        print(f"  {rada}: VALID&OOS molemas positiivne {int(m.sum())}/{len(x)}"
              f"   korr(VALID,OOS) = {x['VALID'].corr(x['OOS']):+.3f}")
