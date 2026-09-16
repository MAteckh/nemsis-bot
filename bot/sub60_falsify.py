"""
sub60_falsify.py — KATSE PRIMAARTULEMUS KATKI TEHA.

Primaarne test andis +11,14 pip / 90% / t=3,22. See on FX-i 30 sekundi
kohta ebatavaliselt tugev. Enne kui seda kuidagi uskuda, tuleb proovida
see UMBER LUKATA. Koik siinne on DIAGNOSTIKA — primaartulemust ei muudeta
ega valita siit midagi valja.

KONTROLLID
  P1  PLATSEEBO ENNE TEADET. Sama suund, sama masinavark, aga sisenemine
      T-60 / T-120 / T-300 s. Kui "serv" on olemas ka ENNE teadet, siis
      suund lekib voi ajatemplid on nihkes ja +11 pip ei ole kaubeldav.
  P2  KLASTRID. 30 sundmust, aga ainult 21 unikaalset (aeg, paar).
      Kolm 07-14 EURUSD sundmust on SAMA hinnarada. Aus N on 21.
  P3  KESKHINNA LIIKUMINE ENNE TEADET, signaalisuunas.
  P4  ESIMESE TICKI SPREAD vs paeva tavaline spread — kas sisenemishind
      on "pseudo-hind" (lai/seisev kotatsioon).
  P5  JAOTUS. Kas tulemuse veab 2-3 vaatlust?
  P6  KAS SUUND ON TEADAOLEV ENNE T? actual-vs-forecast pohine suund
      eeldab, et 'actual' on ESIALGNE trukk. Loendame, palju sundmusi
      on samal ajatemplil (uheaegsed teated ei ole soltumatud).
"""
import numpy as np
import pandas as pd

import sub60_tick as S


def pre_release(T, r, D_enne, H):
    """Sisenemine T - D_enne sekundit, hoid H. Sama taitmisloogika."""
    paev = str(r["ts"].date())
    P = T.get((r["paar"], paev))
    if P is None:
        return np.nan
    ts = P["ts"]
    t0 = np.datetime64(r["ts"].tz_convert("UTC").tz_localize(None), "ns")
    i = S.esimene_alates(ts, t0 - np.timedelta64(int(D_enne), "s"))
    if i < 0:
        return np.nan
    j = S.esimene_alates(ts, ts[i] + np.timedelta64(int(H), "s"))
    if j < 0:
        return np.nan
    s = int(r["suund"])
    pl = (P["bid"][j] - P["ask"][i]) if s > 0 else (P["bid"][i] - P["ask"][j])
    return pl / S.pip(r["paar"])


def mid_enne(T, r, D_enne):
    """Signaalisuunaga keskhinna liikumine T-D_enne -> T."""
    paev = str(r["ts"].date())
    P = T.get((r["paar"], paev))
    if P is None:
        return np.nan
    ts = P["ts"]
    t0 = np.datetime64(r["ts"].tz_convert("UTC").tz_localize(None), "ns")
    i = S.esimene_alates(ts, t0 - np.timedelta64(int(D_enne), "s"))
    j = S.esimene_alates(ts, t0)
    if i < 0 or j < 0:
        return np.nan
    m0 = (P["bid"][i] + P["ask"][i]) / 2
    m1 = (P["bid"][j] + P["ask"][j]) / 2
    return int(r["suund"]) * (m1 - m0) / S.pip(r["paar"])


def p7_likviidsus(T, x):
    """P7 — millal spread normaliseerub ja mis siis P/L-ist jareb.

    DIAGNOSTIKA, MITTE STRATEEGIA. P4 naitas, et kogu tulemus istub
    sundmustes, kus sisenemiskotatsiooni spread on 2-5x paeva tavalisest.
    Kusimus: kas see hind on paris taidetav, voi on see uleminekuhetke
    'indikatiivne' kotatsioon, mis kaob enne kui order kohale jouab.
    """
    print()
    print("P7  MILLAL SPREAD NORMALISEERUB (diagnostika, mitte strateegia)")
    read = []
    for _, r in x.iterrows():
        paev = str(r["ts"].date())
        P = T.get((r["paar"], paev))
        if P is None:
            continue
        jag = S.pip(r["paar"])
        sp = (P["ask"] - P["bid"]) / jag
        med = float(np.median(sp))
        ts = P["ts"]
        t0 = np.datetime64(r["ts"].tz_convert("UTC").tz_localize(None), "ns")
        i0 = S.esimene_alates(ts, t0)
        if i0 < 0:
            continue
        # esimene tick parast T, mille spread <= 1.5x paeva mediaan
        k = i0
        while k < len(ts) and sp[k] > 1.5 * med:
            k += 1
        if k >= len(ts):
            continue
        ootus = float((ts[k] - ts[i0]) / np.timedelta64(1, "ms")) / 1000.0
        j = S.esimene_alates(ts, ts[k] + np.timedelta64(30, "s"))
        if j < 0:
            continue
        s = int(r["suund"])
        pl = ((P["bid"][j] - P["ask"][k]) if s > 0
              else (P["bid"][k] - P["ask"][j])) / jag
        t_kohe = S.tehing(T, r, 0, 30)
        read.append(dict(ts=str(r["ts"])[:19], paar=r["paar"],
                         sp_kohe=t_kohe["spread_sisse_pip"], sp_med=med,
                         ootus_s=ootus, pl_kohe=t_kohe["pl_pip"], pl_ootel=pl))
    D = pd.DataFrame(read)
    print(f"  aeg esimesest tickist kuni spread <= 1.5x paeva mediaan:")
    print(f"    mediaan {D['ootus_s'].median():.3f} s   p90 "
          f"{D['ootus_s'].quantile(0.9):.3f} s   max {D['ootus_s'].max():.3f} s")
    a = S.kokkuvote(D["pl_kohe"])
    b = S.kokkuvote(D["pl_ootel"])
    print(f"  sisenemine KOHE (esimene tick)        n={a['n']:<3d} "
          f"keskm {a['keskm']:+8.3f} pip  mediaan {a['mediaan']:+7.3f}"
          f"  >0 {a['voidu_osa']*100:.1f}%  t {a['t']:+.2f}")
    print(f"  sisenemine kui spread normaliseerub   n={b['n']:<3d} "
          f"keskm {b['keskm']:+8.3f} pip  mediaan {b['mediaan']:+7.3f}"
          f"  >0 {b['voidu_osa']*100:.1f}%  t {b['t']:+.2f}")
    print()
    print("  Sundmused, kus sisenemisspread oli >2x paeva mediaanist:")
    print(f"  {'aeg':<21s}{'paar':<8s}{'sp kohe':>9s}{'sp med':>8s}"
          f"{'ootus s':>9s}{'P/L kohe':>10s}{'P/L ootel':>11s}")
    for _, q in D[D["sp_kohe"] > 2 * D["sp_med"]].iterrows():
        print(f"  {q['ts']:<21s}{q['paar']:<8s}{q['sp_kohe']:>9.2f}"
              f"{q['sp_med']:>8.2f}{q['ootus_s']:>9.3f}"
              f"{q['pl_kohe']:>10.2f}{q['pl_ootel']:>11.2f}")
    return D


if __name__ == "__main__":
    T = S.lae_tikid()
    x = S.sundmused()
    print("=" * 108)
    print("SUB-60 FALSIFIKATSIOON — katse primaartulemus umber lukata")
    print("=" * 108)
    print("  DIAGNOSTIKA. Primaartulemust EI MUUDETA, siit ei valita midagi.")

    # ------------------------------------------------------------- P1 ----
    print()
    print("P1  PLATSEEBO ENNE TEADET (sama suund, sama taitmine, hoid 30 s)")
    print(f"  {'sisenemine':<22s}{'n':>5s}{'keskm pip':>12s}{'mediaan':>10s}"
          f"{'>0 osa':>9s}{'t':>8s}{'p':>9s}")
    for silt, v in [
            ("T-300 s (platseebo)", [pre_release(T, r, 300, 30) for _, r in x.iterrows()]),
            ("T-120 s (platseebo)", [pre_release(T, r, 120, 30) for _, r in x.iterrows()]),
            ("T-60 s  (platseebo)", [pre_release(T, r, 60, 30) for _, r in x.iterrows()]),
            ("T+0 s   (PRIMAARNE)", [S.tehing(T, r, 0, 30)["pl_pip"] for _, r in x.iterrows()])]:
        k = S.kokkuvote(v)
        if k["n"]:
            print(f"  {silt:<22s}{k['n']:>5d}{k['keskm']:>12.3f}"
                  f"{k['mediaan']:>10.3f}{k['voidu_osa']*100:>8.1f}%"
                  f"{k['t']:>8.2f}{k['p']:>9.4f}")

    # ------------------------------------------------------------- P2 ----
    print()
    print("P2  KLASTRID — 30 sundmust, aga mitu soltumatut hinnarada?")
    P = pd.DataFrame([dict(ts=str(r["ts"])[:19], paar=r["paar"],
                           suund=int(r["suund"]),
                           pl=S.tehing(T, r, 0, 30)["pl_pip"])
                      for _, r in x.iterrows()])
    g = P.groupby(["ts", "paar"])
    print(f"  sundmusi: {len(P)}   unikaalseid (aeg, paar): {g.ngroups}")
    mitu = g.size()[g.size() > 1]
    for (t_, p_), n in mitu.items():
        sub = P[(P["ts"] == t_) & (P["paar"] == p_)]
        print(f"    {t_}  {p_}: {n} sundmust, suunad {sorted(sub['suund'].unique())},"
              f" P/L {sorted(round(v,2) for v in sub['pl'].unique())}")
    kl = g["pl"].mean()
    k = S.kokkuvote(kl.values)
    print(f"  KLASTRITASE (keskmine klastri sees), aus N:")
    print(f"    n={k['n']}  keskm {k['keskm']:+.3f} pip  mediaan {k['mediaan']:+.3f}"
          f"  >0 {k['voidu_osa']*100:.1f}%  t {k['t']:+.2f}  p {k['p']:.4f}")

    # ------------------------------------------------------------- P3 ----
    print()
    print("P3  KESKHINNA LIIKUMINE ENNE TEADET (signaalisuunas)")
    print(f"  {'aken':<22s}{'n':>5s}{'keskm pip':>12s}{'mediaan':>10s}{'t':>8s}{'p':>9s}")
    for d in [300, 120, 60, 30, 10]:
        v = [mid_enne(T, r, d) for _, r in x.iterrows()]
        k = S.kokkuvote(v)
        if k["n"]:
            print(f"  {'T-'+str(d)+'s -> T':<22s}{k['n']:>5d}{k['keskm']:>12.3f}"
                  f"{k['mediaan']:>10.3f}{k['t']:>8.2f}{k['p']:>9.4f}")

    # ------------------------------------------------------------- P4 ----
    print()
    print("P4  SISENEMISTICKI SPREAD vs paeva mediaanspread")
    read = []
    for _, r in x.iterrows():
        paev = str(r["ts"].date())
        Pk = T.get((r["paar"], paev))
        if Pk is None:
            continue
        sp_kõik = (Pk["ask"] - Pk["bid"]) / S.pip(r["paar"])
        t = S.tehing(T, r, 0, 30)
        read.append(dict(ts=str(r["ts"])[:19], paar=r["paar"],
                         sp_sisse=t["spread_sisse_pip"],
                         sp_paev_med=float(np.median(sp_kõik)),
                         suhe=t["spread_sisse_pip"] / float(np.median(sp_kõik)),
                         pl=t["pl_pip"]))
    D = pd.DataFrame(read)
    print(f"  sisenemisspread / paeva mediaan: mediaan {D['suhe'].median():.2f}x"
          f"  p90 {D['suhe'].quantile(0.9):.2f}x  max {D['suhe'].max():.2f}x")
    print(f"  mitmel sundmusel on sisenemisspread >2x paeva mediaanist: "
          f"{int((D['suhe'] > 2).sum())} / {len(D)}")
    lai = D[D["suhe"] > 2]
    kitsas = D[D["suhe"] <= 2]
    for silt, g2 in [("lai spread (>2x)", lai), ("normaalne (<=2x)", kitsas)]:
        k = S.kokkuvote(g2["pl"])
        if k["n"]:
            print(f"    {silt:<20s} n={k['n']:<3d} keskm {k['keskm']:+8.3f} pip"
                  f"  mediaan {k['mediaan']:+7.3f}")

    # ------------------------------------------------------------- P5 ----
    print()
    print("P5  JAOTUS — kas tulemuse veab paar vaatlust?")
    v = np.sort(P["pl"].dropna().values)[::-1]
    k = S.kokkuvote(v)
    print(f"  koik            n={len(v)}  keskm {v.mean():+8.3f}  kokku {v.sum():+9.2f}")
    for n_ara in [1, 2, 3, 5]:
        vv = v[n_ara:]
        print(f"  ilma top-{n_ara}      n={len(vv)}  keskm {vv.mean():+8.3f}"
              f"  kokku {vv.sum():+9.2f}")
    print(f"  suurimad: {[round(q,1) for q in v[:6]]}")
    print(f"  vaikseimad: {[round(q,1) for q in v[-4:]]}")

    # ------------------------------------------------------------- P6 ----
    print()
    print("P6  UHEAEGSED TEATED")
    ug = x.groupby("ts").size()
    print(f"  ajatempleid: {len(ug)}   neist mitme teatega: {int((ug>1).sum())}")
    print(f"  suurim uheaegsete teadete arv: {int(ug.max())}")
    print()
    print("  MARKUS: cal_engine.py dokumenteerib, et allikas EI UTLE, kas")
    print("  'actual' on ESIALGNE trukk voi hiljem REVIDEERITUD vaartus.")
    print("  Kui see on revideeritud, siis suund sisaldab infot, mida")
    print("  teate hetkel ei olnud. Seda EI SAA selle andmeallikaga valistada.")

    p7_likviidsus(T, x)
