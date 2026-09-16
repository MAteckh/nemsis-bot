"""sub60_tick_run.py — jooksutab eelregistreeritud sub-60 testi."""
import os
import numpy as np
import pandas as pd

import sub60_tick as S

pd.set_option("display.width", 200)


def rida(k, silt):
    if k.get("n", 0) == 0:
        return f"  {silt:<16s}{'N/A':>8s}"
    return (f"  {silt:<16s}{k['n']:>6d}{k['keskm']:>10.3f}{k['mediaan']:>10.3f}"
            f"{k['kokku']:>11.2f}{k['voidu_osa']*100:>9.1f}%"
            f"{k['sd']:>9.2f}{k['t']:>8.2f}{k['p']:>9.4f}")


if __name__ == "__main__":
    os.makedirs(S.VALJUND, exist_ok=True)
    T = S.lae_tikid()
    x = S.sundmused()
    rng = np.random.default_rng(S.SEEME)

    print("=" * 112)
    print("NEMSIS — SUB-60 TICK EXECUTION TEST")
    print("=" * 112)
    print("  UURIMISTEST. Live koodi ei puudutatud. Parameetreid ei optimeeritud.")
    print(f"  sundmusi: {len(x)}   paare: {x['paar'].nunique()}"
          f"   ({', '.join(sorted(x['paar'].unique()))})")
    print(f"  unikaalseid (aeg, paar) klastreid: "
          f"{x.groupby(['ts','paar']).ngroups} — 30 sundmust EI OLE soltumatud")
    print(f"  taitmine: PARIS bid/ask   seeme: {S.SEEME}")

    # ---------------------------------------------------- SUNDMUSTE TASE --
    read = []
    for _, r in x.iterrows():
        for D in S.VIIVITUSED_S:
            for H in S.HOIUD_S:
                t = S.tehing(T, r, D, H)
                read.append(dict(
                    ts_utc=str(r["ts"])[:19], paar=r["paar"], valuuta=r["cur"],
                    indikaator=r["indicator"], z=round(float(r["z"]), 3),
                    suund=int(r["suund"]), siht_viivitus_s=D, siht_hoid_s=H,
                    **t))
    E = pd.DataFrame(read)
    E.to_csv(os.path.join(S.VALJUND, "sub60_event_level.csv"), index=False)

    # ------------------------------------------------------- PRIMAARNE ----
    P = E[(E["siht_viivitus_s"] == S.PRIMARY_VIIVITUS)
          & (E["siht_hoid_s"] == S.PRIMARY_HOID)]
    k = S.kokkuvote(P["pl_pip"])
    print()
    print("-" * 112)
    print("PRIMAARNE EELREGISTREERITUD TEST — sisenemine 0 s, hoid 30 s")
    print("-" * 112)
    print(f"  N (kehtivaid) ............ {k['n']} / {len(P)}")
    print(f"  keskmine ................. {k['keskm']:+.3f} pip")
    print(f"  mediaan .................. {k['mediaan']:+.3f} pip")
    print(f"  kokku .................... {k['kokku']:+.2f} pip")
    print(f"  voiduprotsent ............ {k['voidu_osa']*100:.1f}%")
    print(f"  standardhalve ............ {k['sd']:.3f} pip")
    print(f"  t-statistik .............. {k['t']:+.3f}")
    print(f"  p-vaartus (t, kahepoolne)  {k['p']:.4f}")
    print(f"  keskmine voit ............ {k['keskm_voit']:+.3f} pip")
    print(f"  keskmine kaotus .......... {k['keskm_kaotus']:+.3f} pip")
    print(f"  suurim voit .............. {k['max_voit']:+.3f} pip")
    print(f"  suurim kaotus ............ {k['max_kaotus']:+.3f} pip")
    print(f"  sisenemisspread mediaan .. {P['spread_sisse_pip'].median():.3f} pip")
    print(f"  release->sisenemine med .. {P['viivitus_s'].median():.3f} s"
          f"   max {P['viivitus_s'].max():.3f} s")
    n0 = int((P["viivitus_s"] == 0.0).sum())
    print(f"  sisenemisi TAPSELT t=0 ... {n0}"
          f"   (need on release'i hetke tickid, mitte eelnevad)")

    # --------------------------------------------- JUHUSLIK BASELINE -----
    v = P["pl_pip"].to_numpy(float)
    kehtiv = np.isfinite(v)
    abs_v = np.where(kehtiv, np.abs(v), np.nan)
    mark = np.where(kehtiv, np.sign(v), np.nan)
    sim = np.empty(S.N_PERM)
    for i in range(S.N_PERM):
        f = rng.choice([-1.0, 1.0], size=len(v))
        # sama sundmus, sama hind, juhuslik suund: P/L margi poord
        # ei ole summeetriline (spread!), seega arvutame otse
        sim[i] = np.nanmean(np.where(f > 0, v, -v - 2 * P["spread_sisse_pip"]
                                     .to_numpy(float)))
    p_perm = float((np.abs(sim - np.nanmean(sim))
                    >= abs(k["keskm"] - np.nanmean(sim))).mean())
    print()
    print("  JUHUSLIKU SUUNA BASELINE (sama sundmused/hinnad, "
          f"{S.N_PERM} permutatsiooni, seeme {S.SEEME})")
    print(f"    baseline keskmine ...... {np.nanmean(sim):+.3f} pip")
    print(f"    baseline sd ............ {np.nanstd(sim):.3f} pip")
    print(f"    baseline 5%/95% ........ {np.nanpercentile(sim,5):+.3f} / "
          f"{np.nanpercentile(sim,95):+.3f} pip")
    print(f"    signaali pertsentiil ... "
          f"{float((sim < k['keskm']).mean())*100:.1f}%")
    print(f"    p (permutatsioon) ...... {p_perm:.4f}")
    pd.DataFrame(dict(sim=sim)).to_csv(
        os.path.join(S.VALJUND, "sub60_random_baseline.csv"), index=False)

    # ----------------------------------------------------------- MAATRIKS -
    print()
    print("-" * 112)
    print("VIIVITUS x HOID MAATRIKS — KIRJELDAV, mitte strateegiavalik")
    print("-" * 112)
    M = []
    for D in S.VIIVITUSED_S:
        for H in S.HOIUD_S:
            kk = S.kokkuvote(E[(E["siht_viivitus_s"] == D)
                               & (E["siht_hoid_s"] == H)]["pl_pip"])
            M.append(dict(siht_viivitus_s=D, siht_hoid_s=H, **kk))
    MM = pd.DataFrame(M)
    MM.to_csv(os.path.join(S.VALJUND, "sub60_matrix.csv"), index=False)

    for mo, sil in [("keskm", "KESKMINE pip"), ("n", "N"),
                    ("voidu_osa", "VOIDUPROTSENT"), ("kokku", "KOKKU pip"),
                    ("mediaan", "MEDIAAN pip")]:
        print(f"\n  {sil}")
        print("  viiv \\ hoid" + "".join(f"{str(h)+'s':>10s}" for h in S.HOIUD_S))
        for D in S.VIIVITUSED_S:
            rw = f"  {str(D)+'s':<11s}"
            for H in S.HOIUD_S:
                c = MM[(MM["siht_viivitus_s"] == D) & (MM["siht_hoid_s"] == H)].iloc[0]
                if c.get("n", 0) == 0 or not np.isfinite(c.get(mo, np.nan)):
                    rw += f"{'N/A':>10s}"
                elif mo == "n":
                    rw += f"{int(c[mo]):>10d}"
                elif mo == "voidu_osa":
                    rw += f"{c[mo]*100:>9.1f}%"
                else:
                    rw += f"{c[mo]:>10.2f}"
            print(rw)

    # --------------------------------------------------- TAITMISKVALITEET -
    print()
    print("-" * 112)
    print("TAITMISKVALITEET")
    print("-" * 112)
    sp = E[E["siht_hoid_s"] == S.PRIMARY_HOID]["spread_sisse_pip"].dropna()
    print(f"  sisenemisspread  mediaan {sp.median():.3f}  keskm {sp.mean():.3f}"
          f"  p90 {sp.quantile(0.90):.3f}  max {sp.max():.3f} pip")
    sx = E[E["siht_hoid_s"] == S.PRIMARY_HOID]["spread_valja_pip"].dropna()
    print(f"  valjumisspread   mediaan {sx.median():.3f}  keskm {sx.mean():.3f}"
          f"  p90 {sx.quantile(0.90):.3f}  max {sx.max():.3f} pip")
    pp = P.dropna(subset=["pl_pip"])
    if len(pp) > 2:
        c = np.corrcoef(pp["spread_sisse_pip"], pp["pl_pip"].abs())[0, 1]
        print(f"  korrelatsioon sisenemisspread vs |P/L| : {c:+.3f}")
        suur = pp.reindex(pp["pl_pip"].abs().sort_values(ascending=False).index)
        print("  5 suurimat |P/L| ja nende spread:")
        for _, q in suur.head(5).iterrows():
            print(f"    {q['ts_utc']}  {q['paar']}  P/L {q['pl_pip']:+8.2f} pip"
                  f"   sisse-spread {q['spread_sisse_pip']:.2f} pip"
                  f"   tikke {int(q['tikke_aknas'])}")

    # ------------------------------------------------------ ANDMEKVALITEET -
    print()
    print("-" * 112)
    print("ANDMEKVALITEET — puuduvad vaatlused")
    print("-" * 112)
    puu = E[E["pl_pip"].isna()]
    print(f"  kokku lahtreid: {len(E)}   puuduvaid: {len(puu)}")
    if len(puu):
        for (po), g in puu.groupby("pohjus"):
            print(f"    {po}: {len(g)}")
        print("  puuduvad sundmuse kaupa:")
        for (t_, p_), g in puu.groupby(["ts_utc", "paar"]):
            komb = ", ".join(f"D{int(a)}/H{int(b)}"
                             for a, b in zip(g["siht_viivitus_s"], g["siht_hoid_s"]))
            print(f"    {t_}  {p_}: {len(g)} kombinatsiooni -> {komb[:90]}")

    # ------------------------------------------------------- KRONOLOOGIA --
    print()
    print("-" * 112)
    print("KRONOLOOGIA — KIRJELDAV, mitte parameetrivalik")
    print("-" * 112)
    Ps = P.sort_values("ts_utc")
    pool = len(Ps) // 2
    for sil, g in [("esimene pool", Ps.iloc[:pool]), ("teine pool", Ps.iloc[pool:])]:
        kk = S.kokkuvote(g["pl_pip"])
        print(f"  {sil:<14s} n={kk['n']:<3d} keskm {kk['keskm']:+7.3f} pip"
              f"  mediaan {kk['mediaan']:+7.3f}  kokku {kk['kokku']:+8.2f}"
              f"  voit {kk['voidu_osa']*100:.1f}%")

    # ------------------------------------------- DIAGNOSTIKA: KESKHIND ----
    print()
    print("-" * 112)
    print("DIAGNOSTIKA — SIGNAALISUUNAGA KESKHINNA LIIKUMINE (enne kulusid)")
    print("-" * 112)
    print("  See EI OLE kaubeldav tulemus. Naitab, kas serv on olemas ENNE spreadi.")
    print(f"  {'horisont':<12s}{'n':>5s}{'keskm pip':>12s}{'mediaan':>10s}"
          f"{'>0 osa':>9s}{'t':>8s}{'p':>9s}")
    dg = []
    for h in S.MID_HORISONDID:
        v2 = [S.mid_liikumine(T, r, h) for _, r in x.iterrows()]
        kk = S.kokkuvote(v2)
        dg.append(dict(horisont_s=h, **kk))
        if kk["n"]:
            print(f"  {str(h)+'s':<12s}{kk['n']:>5d}{kk['keskm']:>12.3f}"
                  f"{kk['mediaan']:>10.3f}{kk['voidu_osa']*100:>8.1f}%"
                  f"{kk['t']:>8.2f}{kk['p']:>9.4f}")
    pd.DataFrame(dg).to_csv(os.path.join(S.VALJUND, "sub60_mid_diagnostic.csv"),
                            index=False)

    print()
    print(f"  kirjutatud: {S.VALJUND}/")
