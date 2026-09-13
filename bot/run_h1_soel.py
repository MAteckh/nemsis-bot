"""
LAI SOEL: 10 strateegiaperekonda x 21 instrumenti, H1-andmetel.

EESMARK (kasutaja sonastus): palju vaikseid tehinguid paevas, enamikul
valuutadel, ja IGALE instrumendile TEMA OMA strateegia — mitte uks
uhine reegel koigile.

METOODIKA — miks nii ja mitte teisiti:
  * Esmalt TOORES ENNUSTUSVOIME fikseeritud horisondiga, ILMA TP/SL-ita.
    Kui signaal ei ennusta jargmist 1/4/8/24 tundi, ei paasta teda ukski
    TP/SL. TP/SL jagab tulemuse umber, ei loo raha juurde. Seda opiti
    190 S/R-variandi peal.
  * Sisenemine jargmise baari AVANEMISEL, signaal jooksva baari
    SULGEMISELT. Ei mingit jooksva baari high/low kasutamist.
  * Kulu EDASI-TAGASI iga tehingu peal, kahel tasemel (retail ja ECN).
  * Koik tulemused salvestatakse; Bonferroni tehakse TEHTUD testide
    arvu jargi, mitte labijate arvu jargi.

PEREKONNAD:
  A KELLAAEG    — kas mingi UTC-tund kannab endas suunda?
                  (kirjandus: FX-fixingud tekitavad W-kujulise mustri)
  B ORB         — sessiooni avamisvahemiku labimurre
  C DONCHIAN    — N tunni tipu/pohja labimurre
  D MOMENTUM    — N tunni tootluse mark
  E POORE       — z-skoori vastu kauplemine
  F SESS-ULEK   — Aasia vahemik murtakse Londonis
  G PAEVASISENE MOMENTUM — paeva esimene tund ennustab viimast
                  (Gao, Han, Li, Zhou 2018, Journal of Financial Economics)
  H SURVE       — volatiilsuse kokkutombumine, siis labimurre
  I TAGASITOMME — trendis tagasitomme EMA-le
  J JUHT-JARGI  — teise instrumendi eelmine tund ennustab seda
"""
import warnings; warnings.filterwarnings("ignore")
import math, itertools
import numpy as np, pandas as pd
import h1engine as E

OUT = "h1_soel_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

D = E.lae_koik()
w(f"instrumente: {len(D)}   periood ~{min(v.index[0] for v in D.values()).date()} .. "
  f"{max(v.index[-1] for v in D.values()).date()}")

HOR = (1, 4, 8, 24)          # valjumishorisondid tundides
read = []                    # koik tulemused


def lisa(sym, perekond, nimi, sg, d):
    """Hindab uhe signaali koigil horisontidel ja kogub tulemused."""
    kr = E.KULU_RETAIL.get(sym, 2.0)
    ke = E.KULU_ECN.get(sym, 0.7)
    for k in HOR:
        y = E.tulevik(d, k)
        r = E.hinda(sg, y, kr)
        if r is None:
            continue
        re_ = E.hinda(sg, y, ke)
        read.append(dict(sym=sym, per=perekond, nimi=nimi, hor=k,
                         n=r["n"], teh_a=r["teh_aastas"],
                         bruto=r["bruto"], keskm=r["keskm"], sh=r["sh"],
                         wr=r["wr"], p1=r["p1"], p2=r["p2"], tstat=r["tstat"],
                         ecn=re_["keskm"], ecn_sh=re_["sh"]))


for sym, d in D.items():
    c, h, l, o = d["close"], d["high"], d["low"], d["open"]
    tund = d.index.hour
    paev = d.index.normalize()
    r1 = c / c.shift(1) - 1

    # ── A) KELLAAEG ──────────────────────────────────────────────
    for hh in range(24):
        sg = pd.Series(np.where(tund == hh, 1.0, 0.0), index=d.index)
        if int((sg != 0).sum()) < 200:
            continue
        lisa(sym, "A KELLAAEG", f"tund {hh:02d} PIKK", sg, d)
        lisa(sym, "A KELLAAEG", f"tund {hh:02d} LÜHIKE", -sg, d)

    # ── B) ORB — sessiooni avamisvahemiku läbimurre ──────────────
    for algus, nimi_s in ((0, "Aasia"), (7, "London"), (13, "NY")):
        for pikkus in (1, 2, 3):
            # vahemik = sessiooni esimesed 'pikkus' tundi
            on_vahemik = (tund >= algus) & (tund < algus + pikkus)
            grp = pd.Series(paev, index=d.index)
            hi = h.where(on_vahemik).groupby(grp).transform("max")
            lo = l.where(on_vahemik).groupby(grp).transform("min")
            # kaubeldav aken: parast vahemikku, sama sessioon +6h
            aken = (tund >= algus + pikkus) & (tund < algus + pikkus + 6)
            up = (c > hi) & aken
            dn = (c < lo) & aken
            sg = (up.astype(float) - dn.astype(float)).fillna(0.0)
            # ainult ESIMENE labimurre paevas
            esim = sg.ne(0) & (~sg.ne(0).groupby(grp).cumsum().gt(1))
            sg = sg.where(esim, 0.0)
            if int((sg != 0).sum()) < 150:
                continue
            lisa(sym, "B ORB", f"{nimi_s} {pikkus}h murre", sg, d)
            lisa(sym, "B ORB", f"{nimi_s} {pikkus}h FADE", -sg, d)

    # ── C) DONCHIAN ─────────────────────────────────────────────
    for lb in (6, 12, 24, 48, 96, 168):
        up = c >= h.rolling(lb).max().shift(1)
        dn = c <= l.rolling(lb).min().shift(1)
        sg = (up.astype(float) - dn.astype(float)).fillna(0.0)
        if int((sg != 0).sum()) < 150:
            continue
        lisa(sym, "C DONCHIAN", f"{lb}h murre", sg, d)
        lisa(sym, "C DONCHIAN", f"{lb}h FADE", -sg, d)

    # ── D) MOMENTUM ─────────────────────────────────────────────
    for lb in (4, 12, 24, 72, 168):
        sg = pd.Series(np.sign((c / c.shift(lb) - 1).values), index=d.index).fillna(0.0)
        lisa(sym, "D MOMENTUM", f"{lb}h märk", sg, d)

    # ── E) POORE (z-skoor) ──────────────────────────────────────
    for lb in (12, 24, 72):
        for lv in (1.0, 2.0):
            m_, sd = c.rolling(lb).mean(), c.rolling(lb).std()
            z = ((c - m_) / sd)
            sg = (-np.sign(z) * (z.abs() > lv)).fillna(0.0)
            if int((sg != 0).sum()) < 150:
                continue
            lisa(sym, "E PÖÖRE", f"z{lb}h >{lv}", sg, d)

    # ── F) SESSIOONI-ULEKANNE: Aasia vahemik murtakse Londonis ──
    grp = pd.Series(paev, index=d.index)
    aasia = (tund >= 0) & (tund < 7)
    a_hi = h.where(aasia).groupby(grp).transform("max")
    a_lo = l.where(aasia).groupby(grp).transform("min")
    lon = (tund >= 7) & (tund < 16)
    up = (c > a_hi) & lon
    dn = (c < a_lo) & lon
    sg = (up.astype(float) - dn.astype(float)).fillna(0.0)
    esim = sg.ne(0) & (~sg.ne(0).groupby(grp).cumsum().gt(1))
    sg = sg.where(esim, 0.0)
    if int((sg != 0).sum()) >= 150:
        lisa(sym, "F SESS-ÜLEK", "Aasia→London murre", sg, d)
        lisa(sym, "F SESS-ÜLEK", "Aasia→London FADE", -sg, d)

    # ── G) PAEVASISENE MOMENTUM (Gao et al. 2018) ───────────────
    # paeva esimese tunni tootlus -> kauple paeva viimasel tunnil
    for algus, lopp, nimi_s in ((0, 22, "UTC 00→22"), (7, 20, "UTC 07→20"),
                                (13, 20, "NY 13→20")):
        esim_r = (c.where(tund == algus) / o.where(tund == algus) - 1)
        esim_p = esim_r.groupby(grp).transform("max")
        sg = pd.Series(np.where(tund == lopp, np.sign(esim_p.values), 0.0),
                       index=d.index)
        sg = sg.fillna(0.0)
        if int((sg != 0).sum()) < 150:
            continue
        lisa(sym, "G PÄEVASIS-MOM", nimi_s, sg, d)
        lisa(sym, "G PÄEVASIS-MOM", nimi_s + " FADE", -sg, d)

    # ── H) SURVE: volatiilsuse kokkutombumine, siis labimurre ───
    a = E.atr(d, 14)
    for lb in (24, 72):
        kitsas = a < a.rolling(lb).quantile(0.25)
        up = (c >= h.rolling(6).max().shift(1)) & kitsas
        dn = (c <= l.rolling(6).min().shift(1)) & kitsas
        sg = (up.astype(float) - dn.astype(float)).fillna(0.0)
        if int((sg != 0).sum()) < 150:
            continue
        lisa(sym, "H SURVE", f"kitsas {lb}h + murre", sg, d)

    # ── I) TAGASITOMME trendis ──────────────────────────────────
    for tr_lb, pb in ((200, 20), (100, 12)):
        ema = c.ewm(span=tr_lb).mean()
        ema_s = c.ewm(span=pb).mean()
        tous = c > ema
        lang = c < ema
        # tagasitomme: hind ristub luhikese EMA-ga trendi suunas
        alla = (c < ema_s) & (c.shift(1) >= ema_s.shift(1))
        ules = (c > ema_s) & (c.shift(1) <= ema_s.shift(1))
        sg = ((tous & alla).astype(float) - (lang & ules).astype(float)).fillna(0.0)
        if int((sg != 0).sum()) < 150:
            continue
        lisa(sym, "I TAGASITÕMME", f"EMA{tr_lb}/{pb}", sg, d)

w(f"testid perekondadest A-I: {len(read)}")

# ── J) JUHT-JARGI (rist-instrument) ──────────────────────────────
w("ehitan J JUHT-JÄRGI ...")
for sym, d in D.items():
    y1 = E.tulevik(d, 1)
    kr = E.KULU_RETAIL.get(sym, 2.0)
    for juht, dj in D.items():
        if juht == sym:
            continue
        rj = (dj["close"] / dj["close"].shift(1) - 1)
        z = (rj / rj.rolling(120).std())
        ix = d.index.intersection(dj.index)
        if len(ix) < 3000:
            continue
        zz = z.reindex(ix)
        for lv in (1.0, 2.0):
            sg = (np.sign(zz) * (zz.abs() > lv)).fillna(0.0)
            if int((sg != 0).sum()) < 200:
                continue
            lisa(sym, "J JUHT-JÄRGI", f"{juht} z>{lv}", sg, d)

df = pd.DataFrame(read)
df.to_csv("data/h1_soel.csv", index=False)
w(f"TESTE KOKKU: {len(df)}   (salvestatud data/h1_soel.csv)")

# ── TULEMUSED ───────────────────────────────────────────────────
w("")
w("=" * 100)
w("1) ULDPILT PEREKONNITI (retail-kulud, kõik horisondid koos)")
w("=" * 100)
w(f"  {'perekond':18s} {'teste':>7s} {'plussis':>9s} {'keskm bp':>10s} "
  f"{'parim bp':>10s} {'|t|>3':>7s}")
w("  " + "-" * 68)
for per, g in df.groupby("per"):
    w(f"  {per:18s} {len(g):7d} {100*(g['keskm']>0).mean():8.1f}% "
      f"{1e4*g['keskm'].mean():+10.2f} {1e4*g['keskm'].max():+10.2f} "
      f"{int((g['tstat'].abs()>3).sum()):7d}")

# Bonferroni TEHTUD testide arvu jargi
N = len(df)
t_krit = float(abs(pd.Series([0.0]).iloc[0]))
from math import sqrt
try:
    from scipy.stats import norm
    t_krit = float(norm.ppf(1 - 0.05 / (2 * N)))
except Exception:
    t_krit = 4.5
w("")
w("=" * 100)
w(f"2) BONFERRONI — {N} testi tehtud, lävend |t| > {t_krit:.2f}")
w("=" * 100)
labijad = df[df["tstat"].abs() > t_krit].sort_values("keskm", ascending=False)
w(f"   läbijaid: {len(labijad)}   (juhuslikult oodatav ~0.05)")
if len(labijad):
    w("")
    w(f"   {'instr':8s} {'perekond':16s} {'signaal':22s} {'h':>3s} {'n':>6s} "
      f"{'teh/a':>7s} {'keskm bp':>9s} {'t':>7s} {'1.pool':>8s} {'2.pool':>8s}")
    w("   " + "-" * 104)
    for _, r in labijad.head(40).iterrows():
        w(f"   {r['sym']:8s} {r['per']:16s} {r['nimi']:22s} {r['hor']:3d} "
          f"{r['n']:6d} {r['teh_a']:7.0f} {1e4*r['keskm']:+9.2f} {r['tstat']:+7.2f} "
          f"{1e4*r['p1']:+8.2f} {1e4*r['p2']:+8.2f}")

w("")
w("=" * 100)
w("3) PARIMAD 30 KESKMISE TOOTLUSE JÄRGI (ilma Bonferronita — NB: valikunihe!)")
w("=" * 100)
w(f"   {'instr':8s} {'perekond':16s} {'signaal':22s} {'h':>3s} {'n':>6s} "
  f"{'teh/a':>7s} {'keskm bp':>9s} {'t':>7s} {'1.pool':>8s} {'2.pool':>8s} {'ECN bp':>8s}")
w("   " + "-" * 112)
for _, r in df.sort_values("keskm", ascending=False).head(30).iterrows():
    w(f"   {r['sym']:8s} {r['per']:16s} {r['nimi']:22s} {r['hor']:3d} "
      f"{r['n']:6d} {r['teh_a']:7.0f} {1e4*r['keskm']:+9.2f} {r['tstat']:+7.2f} "
      f"{1e4*r['p1']:+8.2f} {1e4*r['p2']:+8.2f} {1e4*r['ecn']:+8.2f}")
w("VALMIS")
