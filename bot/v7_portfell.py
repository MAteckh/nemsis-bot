"""
v7 TAIS TEST: binaarsed filtrid + mitu signaaliperekonda + A/B/C vordlus.

EELMINE TULEMUS: liitkvaliteediskoor ei ennustanud (TOP-detsiil -3.02bp).
AGA kaks asja jai katmata:
  1. binaarsed komponendid (trendi joondus, suhteline tugevus) — qcut ei
     suutnud neid 5 ossa jagada
  2. testisin ainult UHT signaaliperekonda (24h murre)

Siin teen molemad ara, ja seejarel kasutaja punkti 19 vordluse:
  A) uks parim FX-paar
  B) koik paarid eraldi
  C) MULTI-PAAR PORTFELL paris taitmisega (miinimum-lot, reject kui ei mahu)
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "v7_portfell.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

FX22 = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
        "EURGBP","EURJPY","EURCHF","EURAUD","EURNZD","GBPJPY","GBPCHF",
        "GBPAUD","GBPCAD","AUDJPY","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"]
KULU = {p: E.KULU_RETAIL.get(p, 1.8) for p in FX22}
for p in ("EURNZD","GBPCHF","GBPCAD","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"):
    KULU[p] = 2.2
D = {s: E.lae(s) for s in FX22}
D = {k: v for k, v in D.items() if v is not None}
BAAS = {p: (p[:3], p[3:]) for p in D}

S = pd.read_pickle("data/v7_signaalid.pkl")

w("=" * 96)
w("1) BINAARSED FILTRID — trendi joondus ja suhteline tugevus")
w("=" * 96)
w("  Need on kasutaja punkti 7 põhifiltrid. Eelmises tabelis puudusid,")
w("  sest qcut ei suutnud binaarset muutujat 5 ossa jagada.")
w("")
w(f"  {'filter':32s} {'signaale':>10s} {'BRUTO bp':>10s} {'NETO bp':>10s} {'võit%':>8s}")
w("  " + "-" * 74)
for nimi, m in (("kõik signaalid", S["neto"].notna()),
                ("trendi joondus JAH", S["joondus"] > 0.5),
                ("trendi joondus EI", S["joondus"] <= 0.5),
                ("suht. tugevus kooskõlas", S["rs"] > 0.5),
                ("suht. tugevus vastu", S["rs"] <= 0.5),
                ("MÕLEMAD kooskõlas", (S["joondus"] > 0.5) & (S["rs"] > 0.5)),
                ("mõlemad + ATR laienemine", (S["joondus"] > 0.5) & (S["rs"] > 0.5)
                                             & (S["atr_exp"] > 1.2)),
                ("mõlemad + selge murre", (S["joondus"] > 0.5) & (S["rs"] > 0.5)
                                          & (S["selgus"] > 0.3))):
    g = S[m]
    if len(g) < 100: 
        w(f"  {nimi:32s} {len(g):10d}   liiga vähe"); continue
    w(f"  {nimi:32s} {len(g):10d} {1e4*g['y'].mean():+10.2f} "
      f"{1e4*g['neto'].mean():+10.2f} {100*(g['neto']>0).mean():7.1f}%")

# ── 2) MITU SIGNAALIPEREKONDA x SELEKTIIVSUS ───────────────────
w("")
w("=" * 96)
w("2) TEISED SIGNAALIPEREKONNAD — kas mõni reageerib selektiivsusele?")
w("=" * 96)

def perekonnad(d, ind):
    c, h, l = d["close"], d["high"], d["low"]
    a, adx = ind["atr"], ind["adx"]
    out = {}
    # A murre + vol laienemine
    kitsas = a < a.rolling(120).quantile(0.30)
    up6 = c >= h.rolling(12).max().shift(1); dn6 = c <= l.rolling(12).min().shift(1)
    out["A murre+vol"] = ((up6 & kitsas).astype(float) - (dn6 & kitsas).astype(float))
    # B trendi jatkumine parast tagasitommet
    ef, es = c.ewm(span=20).mean(), c.ewm(span=100).mean()
    tous, lang = (ef > es), (ef < es)
    tag_up = (c > ef) & (c.shift(1) <= ef.shift(1))
    tag_dn = (c < ef) & (c.shift(1) >= ef.shift(1))
    out["B trend+tagasitõmme"] = ((tous & tag_up).astype(float)
                                  - (lang & tag_dn).astype(float))
    # C poore ainult selges range'is
    m_, sd_ = c.rolling(40).mean(), c.rolling(40).std()
    z = (c - m_) / sd_
    range_ = adx < 20
    out["C pööre range'is"] = ((-np.sign(z) * (z.abs() > 2.0)) * range_).fillna(0.0)
    # E sessioonimurre
    tund = d.index.hour; grp = pd.Series(d.index.normalize(), index=d.index)
    aasia = (tund >= 0) & (tund < 7)
    ah = h.where(aasia).groupby(grp).transform("max")
    al = l.where(aasia).groupby(grp).transform("min")
    aken = (tund >= 7) & (tund < 16)
    sg = ((c > ah) & aken).astype(float) - ((c < al) & aken).astype(float)
    esim = sg.ne(0) & (~sg.ne(0).groupby(grp).cumsum().gt(1))
    out["E sessioonimurre"] = sg.where(esim, 0.0)
    # F momentum parast kokkusurvet
    surve = a.rolling(24).mean() / a.rolling(240).mean()
    out["F surve+momentum"] = (np.sign(c / c.shift(24) - 1)
                               * (surve < 0.75)).fillna(0.0)
    return {k: v.fillna(0.0) for k, v in out.items()}

w(f"  {'perekond':22s} {'signaale':>9s} {'BRUTO':>9s} {'NETO':>9s} "
  f"{'TOP-25% NETO':>13s} {'vahe':>8s}")
w("  " + "-" * 74)
for pnimi in ("A murre+vol", "B trend+tagasitõmme", "C pööre range'is",
              "E sessioonimurre", "F surve+momentum"):
    read = []
    for sym, d in D.items():
        ind = P.valmista(d)
        sg = perekonnad(d, ind)[pnimi]
        if int((sg != 0).sum()) < 50: continue
        c, o, a, adx = d["close"], d["open"], ind["atr"], ind["adx"]
        y = (c.shift(-8) / o.shift(-1) - 1)
        atr_exp = (a / a.rolling(240).mean()).fillna(1.0)
        ef, es = c.ewm(span=50).mean(), c.ewm(span=200).mean()
        joond = (np.sign(sg) == np.sign(ef - es)).astype(float)
        kv = ((atr_exp - 1) + joond + (adx/50).clip(0,2))
        m = (sg != 0) & y.notna() & kv.notna()
        if int(m.sum()) < 50: continue
        read.append(pd.DataFrame(dict(
            y=(np.sign(sg[m]) * y[m]).values,
            neto=(np.sign(sg[m]) * y[m] - 2*KULU[sym]/1e4).values,
            kv=kv[m].values)))
    if not read: continue
    G = pd.concat(read, ignore_index=True).dropna()
    G = G[np.isfinite(G["neto"])]
    if len(G) < 200: continue
    lav = G["kv"].quantile(0.75)
    top = G[G["kv"] >= lav]
    w(f"  {pnimi:22s} {len(G):9d} {1e4*G['y'].mean():+9.2f} {1e4*G['neto'].mean():+9.2f} "
      f"{1e4*top['neto'].mean():+13.2f} {1e4*(top['neto'].mean()-G['neto'].mean()):+8.2f}")

# ── 3) A / B / C VORDLUS ───────────────────────────────────────
w("")
w("=" * 96)
w("3) KASUTAJA PUNKT 19 — A (üks paar) vs B (kõik eraldi) vs C (PORTFELL)")
w("=" * 96)
w("  Kõik kolm kasutavad SAMA signaali (24h murre) ja SAMU kulusid.")
w("  Erinevus on ainult selles, mitu paari korraga ja kas valitakse.")
w("")

# ehita paevane tootlusmaatriks paaride kaupa
PAEV = {}
for sym, d in D.items():
    c, h, l, o = d["close"], d["high"], d["low"], d["open"]
    hi = h.rolling(24).max().shift(1); lo = l.rolling(24).min().shift(1)
    sg = (c > hi).astype(float) - (c < lo).astype(float)
    pos = sg.replace(0.0, np.nan).ffill(limit=8).fillna(0.0)
    r_next = c.shift(-1) / c - 1
    vah = pos.diff().abs().fillna(pos.abs())
    PAEV[sym] = (pos * r_next - vah * KULU[sym] / 1e4).fillna(0.0)
M = pd.DataFrame(PAEV).fillna(0.0)

def sh(x, per=6000):
    x = np.asarray(x); x = x[np.isfinite(x)]
    return float(x.mean()/x.std()*np.sqrt(per)) if len(x)>100 and x.std()>0 else 0.0
def dd(x):
    eq = np.cumprod(1+np.asarray(x)); return float((eq/np.maximum.accumulate(eq)-1).min())

w(f"  {'variant':34s} {'paare':>6s} {'keskm bp':>10s} {'Sharpe':>8s} "
  f"{'maxDD':>9s} {'tulu/DD':>9s}")
w("  " + "-" * 80)
# A) parim uks paar (valitud KOGU perioodi pealt = optimistlik)
parim = M.mean().idxmax()
xa = M[parim]
w(f"  {'A) parim üks paar (' + parim + ')':34s} {1:6d} {1e4*float(xa.mean()):+10.2f} "
  f"{sh(xa):+8.2f} {100*dd(xa):+8.1f}% {abs(xa.sum()/dd(xa)) if dd(xa)<0 else 0:8.2f}")
# B) koik paarid eraldi = keskmine
w(f"  {'B) kõik paarid eraldi (keskm)':34s} {M.shape[1]:6d} "
  f"{1e4*float(M.mean().mean()):+10.2f} {np.mean([sh(M[c]) for c in M]):+8.2f} "
  f"{100*np.mean([dd(M[c]) for c in M]):+8.1f}% {'':>9s}")
# C) portfell: koik vordselt
xc = M.mean(axis=1)
w(f"  {'C1) portfell, kõik võrdselt':34s} {M.shape[1]:6d} {1e4*float(xc.mean()):+10.2f} "
  f"{sh(xc):+8.2f} {100*dd(xc):+8.1f}% {abs(xc.sum()/dd(xc)) if dd(xc)<0 else 0:8.2f}")
# C2) portfell: ainult TOP-N kvaliteedi jargi (paevane valik)
for topn in (1, 2, 3, 5):
    # kvaliteet = ATR laienemine x trendi joondus, arvutatud eelmise baari seisuga
    kv = {}
    for sym, d in D.items():
        ind = P.valmista(d)
        a = ind["atr"]; c = d["close"]
        ef, es = c.ewm(span=50).mean(), c.ewm(span=200).mean()
        kv[sym] = ((a/a.rolling(240).mean()).fillna(1.0)
                   + (np.sign(ef-es)).fillna(0.0)).reindex(M.index).ffill()
    KV = pd.DataFrame(kv).reindex(M.index)
    akt = (M != 0)
    KVm = KV.where(akt, -9e9)
    rank = KVm.rank(axis=1, ascending=False)
    W = (rank <= topn).astype(float)
    W = W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    xt = (W.shift(1).fillna(0.0) * M).sum(axis=1)
    w(f"  {'C2) portfell, TOP-' + str(topn) + ' kvaliteedi järgi':34s} {topn:6d} "
      f"{1e4*float(xt.mean()):+10.2f} {sh(xt):+8.2f} {100*dd(xt):+8.1f}% "
      f"{abs(xt.sum()/dd(xt)) if dd(xt)<0 else 0:8.2f}")

w("")
w("  NB: variant A on OPTIMISTLIK — parim paar valiti kogu perioodi pealt,")
w("      mis on valikunihe. Päris elus seda paari ette ei tea.")
w("VALMIS")
