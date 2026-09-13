"""
REZIIMIPOHINE RAAMISTIK + TURUSTRUKTUUR (kasutaja punktid 1E ja 2).

MIKS SEE ON AINUS USUTAV TESTIMATA IDEE:
koik senine motis strateegiaid KESKMISELT ule koigi turutingimuste.
Kui trend-following toimib ainult trendis ja mean reversion ainult
rangis, siis keskmine ule koigi tingimuste on ~0 ka siis, kui MOLEMAD
toovad oma rezhiimis raha. See test lahutab need.

REZIIMID (arvutatud AINULT moodunud baaridest):
  tugev trend    ADX > 30
  nork trend     ADX 20-30
  range          ADX < 20
  korge vol      ATR / ATR(240) > 80. protsentiil
  madal vol      ATR / ATR(240) < 20. protsentiil
  kokkusurve     ATR(24) / ATR(240) < 0.7
  ebanormaalne   |tootlus| > 4 x hiljutine std (uudise jalg)

TURUSTRUKTUUR (perekond E, seni testimata):
  likviidsuse pyhkimine  — vurr ule swing-tipu, sulgemine tagasi alla
  BOS (break of structure) — sulgemine ule viimase swing-tipu
  CHOCH (change of character) — BOS vastassuunas parast vastupidist BOS-i
  ebaonnestunud murre    — murre, mis 3 baari jooksul tagasi tuleb
  nouldus/pakkumine      — tagasitulek tsooni, kust tuli impulss
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "rezim_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

rng = np.random.default_rng(2209)
PAARID = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
          "EURJPY","GBPJPY","EURGBP","XAUUSD","WTI","SPX","NAS100"]
D = {s: E.lae(s) for s in PAARID}
D = {k: v for k, v in D.items() if v is not None}


def rezimid(d, ind):
    """Dict {nimi: bool-seeria}. KOIK arvutatud moodunud baaridest."""
    adx = ind["adx"]
    a = ind["atr"]
    rel = a / a.rolling(240).mean()
    r1 = d["close"].pct_change()
    sd = r1.rolling(120).std()
    surve = a.rolling(24).mean() / a.rolling(240).mean()
    return {
        "tugev trend": adx > 30,
        "nõrk trend":  (adx >= 20) & (adx <= 30),
        "range":       adx < 20,
        "kõrge vol":   rel > rel.rolling(480).quantile(0.80),
        "madal vol":   rel < rel.rolling(480).quantile(0.20),
        "kokkusurve":  surve < 0.70,
        "ebanormaalne": r1.abs() > 4 * sd,
    }


def strateegiad(d, ind):
    """Signaaliperekonnad. Signaal baaril i, sisenemine i+1 avanemisel."""
    c, h, l, o = d["close"], d["high"], d["low"], d["open"]
    out = {}
    # A trend-following
    ef, es = c.ewm(span=20).mean(), c.ewm(span=50).mean()
    out["A trend EMA20/50"] = np.sign(ef - es).fillna(0.0)
    # B momentum
    out["B momentum 24h"] = pd.Series(np.sign((c/c.shift(24)-1).values), index=d.index).fillna(0.0)
    # C breakout
    out["C Donchian 24h"] = ((c >= h.rolling(24).max().shift(1)).astype(float)
                             - (c <= l.rolling(24).min().shift(1)).astype(float))
    # D mean reversion
    m_, sd_ = c.rolling(20).mean(), c.rolling(20).std()
    z = (c - m_) / sd_
    out["D pööre BB20"] = (-np.sign(z) * (z.abs() > 2.0)).fillna(0.0)
    # F volatiilsuse laienemine
    a = ind["atr"]
    kitsas = a < a.rolling(72).quantile(0.25)
    out["F surve->murre"] = (((c >= h.rolling(12).max().shift(1)) & kitsas).astype(float)
                             - ((c <= l.rolling(12).min().shift(1)) & kitsas).astype(float))
    # ── E TURUSTRUKTUUR ────────────────────────────────────────
    N = 12
    sw_h = h.rolling(N).max().shift(1)
    sw_l = l.rolling(N).min().shift(1)
    # likviidsuse pyhkimine: vurr ule tipu, sulgemine tagasi alla => luhike
    out["E likv. pühkimine"] = (((l <= sw_l) & (c > sw_l)).astype(float)
                                - ((h >= sw_h) & (c < sw_h)).astype(float))
    # BOS: SULGEMINE ule swing-tipu (mitte ainult vurr)
    bos_up = (c > sw_h)
    bos_dn = (c < sw_l)
    out["E BOS"] = (bos_up.astype(float) - bos_dn.astype(float))
    # CHOCH: BOS vastassuunas parast vastupidist BOS-i
    viim = pd.Series(np.nan, index=d.index)
    viim[bos_up] = 1.0; viim[bos_dn] = -1.0
    viim = viim.ffill()
    choch = ((bos_up & (viim.shift(1) == -1)).astype(float)
             - (bos_dn & (viim.shift(1) == 1)).astype(float))
    out["E CHOCH"] = choch
    # ebaonnestunud murre: murdis ules, 3 baari jooksul tagasi alla => luhike
    murre_up = (c > sw_h)
    tagasi = murre_up.shift(3).fillna(False) & (c < sw_h)
    murre_dn = (c < sw_l)
    tagasi2 = murre_dn.shift(3).fillna(False) & (c > sw_l)
    out["E ebaõnn. murre"] = (tagasi2.astype(float) - tagasi.astype(float))
    # noudlus/pakkumine: impulss (>2 ATR 3 baariga), siis tagasitulek tsooni
    imp_up = (c - c.shift(3)) > 2 * a
    imp_dn = (c.shift(3) - c) > 2 * a
    tsoon_lo = l.shift(3).where(imp_up).ffill(limit=48)
    tsoon_hi = h.shift(3).where(imp_dn).ffill(limit=48)
    out["E nõudl./pakkum."] = (((l <= tsoon_lo) & (c > tsoon_lo)).astype(float)
                               - ((h >= tsoon_hi) & (c < tsoon_hi)).astype(float))
    return {k: v.fillna(0.0) for k, v in out.items()}


# ══ 1) EXPECTANCY REZIIMI KAUPA ════════════════════════════════
w("=" * 108)
w("1) IGA PEREKOND x IGA REŽIIM — keskmine tootlus tehingu kohta (bp), kulud maha")
w("=" * 108)
w("   Küsimus: kas mõni perekond töötab MINGIS režiimis, isegi kui keskmiselt ei tööta?")
w("")

kogu = {}
for sym, d in D.items():
    ind = P.valmista(d)
    rz = rezimid(d, ind)
    st = strateegiad(d, ind)
    kulu = E.KULU_RETAIL.get(sym, 1.5)
    y = E.tulevik(d, 8)                      # 8h horisont
    for s_nimi, sg in st.items():
        for r_nimi, mask in rz.items():
            sgr = sg.where(mask.fillna(False), 0.0)
            r = E.hinda(sgr, y, kulu)
            if r is None: continue
            kogu.setdefault((s_nimi, r_nimi), []).append((r["keskm"], r["bruto"], r["n"]))

REZ = ["tugev trend","nõrk trend","range","kõrge vol","madal vol","kokkusurve","ebanormaalne"]
STR = ["A trend EMA20/50","B momentum 24h","C Donchian 24h","D pööre BB20",
       "F surve->murre","E likv. pühkimine","E BOS","E CHOCH",
       "E ebaõnn. murre","E nõudl./pakkum."]
w("   " + f"{'perekond':20s}" + "".join(f"{r[:11]:>12s}" for r in REZ))
w("   " + "-" * (20 + 12*len(REZ)))
parimad = []
for s_nimi in STR:
    rida = f"   {s_nimi:20s}"
    for r_nimi in REZ:
        v = kogu.get((s_nimi, r_nimi))
        if not v:
            rida += f"{'-':>12s}"; continue
        keskm = np.mean([x[0] for x in v])
        n_plus = sum(1 for x in v if x[0] > 0)
        rida += f"{1e4*keskm:>+9.1f}({n_plus:>1d})" if len(v) < 10 else f"{1e4*keskm:>+9.1f}({n_plus:>2d})"
        parimad.append((s_nimi, r_nimi, keskm, n_plus, len(v)))
    w(rida)
w("")
w("   sulgudes = mitu instrumenti 14-st on selles lahtris plussis")

w("")
w("=" * 108)
w("2) PARIMAD LAHTRID — kus on keskmine PLUSSIS ja enamik instrumente plussis?")
w("=" * 108)
kand = [p for p in parimad if p[2] > 0 and p[3] >= p[4] * 0.6]
w(f"   kandidaate: {len(kand)} / {len(parimad)} lahtrist")
if kand:
    w("")
    w(f"   {'perekond':20s} {'režiim':14s} {'keskm bp':>10s} {'plussis':>10s}")
    w("   " + "-" * 58)
    for s_, r_, k_, np_, nt_ in sorted(kand, key=lambda x: -x[2]):
        w(f"   {s_:20s} {r_:14s} {1e4*k_:+10.2f} {np_:6d}/{nt_:<3d}")

# ══ 3) BRUTO vs NETO — kas kulu voi signaal? ═══════════════════
w("")
w("=" * 108)
w("3) KAS PROBLEEM ON KULUDES VÕI SIGNAALIS? (bruto = enne kulusid)")
w("=" * 108)
w(f"   {'perekond':20s} {'BRUTO bp':>10s} {'NETO bp':>10s} {'kulu bp':>9s} "
  f"{'BRUTO plussis':>15s}")
w("   " + "-" * 68)
for s_nimi in STR:
    vs = [x for (sn, rn), v in kogu.items() if sn == s_nimi for x in v]
    if not vs: continue
    b = np.mean([x[1] for x in vs]); n_ = np.mean([x[0] for x in vs])
    w(f"   {s_nimi:20s} {1e4*b:+10.2f} {1e4*n_:+10.2f} {1e4*(b-n_):9.2f} "
      f"{100*np.mean([x[1]>0 for x in vs]):14.0f}%")

# ══ 4) REZIIMILULITI — kas parim-per-rezhiim korv toimib? ══════
w("")
w("=" * 108)
w("4) REŽIIMILÜLITI — vali igas režiimis parim perekond 1. POOLE pealt, testi 2. poolel")
w("=" * 108)
oos = []
for sym, d in D.items():
    ind = P.valmista(d); rz = rezimid(d, ind); st = strateegiad(d, ind)
    kulu = E.KULU_RETAIL.get(sym, 1.5); y = E.tulevik(d, 8)
    m = len(d) // 2
    iA, iB = d.index[:m], d.index[m:]
    val = {}
    for r_nimi, mask in rz.items():
        parim, parim_v = None, -9e9
        for s_nimi, sg in st.items():
            sgr = sg.where(mask.fillna(False), 0.0).reindex(iA).fillna(0.0)
            r = E.hinda(sgr, y.reindex(iA), kulu)
            if r and r["keskm"] > parim_v:
                parim, parim_v = s_nimi, r["keskm"]
        if parim: val[r_nimi] = parim
    # ehita OOS-signaal: igas rezhiimis valitud perekond
    sg_oos = pd.Series(0.0, index=iB)
    for r_nimi, s_nimi in val.items():
        mask = rz[r_nimi].reindex(iB).fillna(False)
        sg_oos = sg_oos.where(~mask, st[s_nimi].reindex(iB).fillna(0.0))
    r = E.hinda(sg_oos, y.reindex(iB), kulu)
    if r:
        oos.append(r["keskm"])
        w(f"   {sym:8s} OOS {1e4*r['keskm']:+8.2f}bp  ({r['n']:5d} teh)   "
          f"valitud: {', '.join(f'{k[:8]}={v[:10]}' for k,v in list(val.items())[:3])}")
w("")
if oos:
    w(f"   OOS plussis {sum(1 for x in oos if x>0)}/{len(oos)}  "
      f"(mündivisega oodatav {len(oos)/2:.1f}),  keskmine {1e4*np.mean(oos):+.2f}bp")
w("VALMIS")
