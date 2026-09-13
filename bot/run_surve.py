"""
VIIMANE KANDIDAAT: VOLATIILSUSE KOKKUSURVE -> LABIMURRE.

MIKS SEE: rezhiimitestis oli see AINUS perekond, mille BRUTO-serv oli
selgelt positiivne — +1.42bp, 65% instrumentidest plussis. Koik teised
olid -0.9 .. +0.5bp ehk nullis.

Retail-kulu on 3.0bp => -1.6bp neto, kaotaja.
ECN-kulu on ~1.05bp (0.35x) => +0.37bp neto, VOITJA?

See on ainus koht kogu uurimistoos, kus serv ja kulu on samas
suurusjargus. Seepolikult saab ta taie protokolli.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "surve_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

rng = np.random.default_rng(2309)
PAARID = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
          "EURJPY","GBPJPY","EURGBP","EURAUD","AUDJPY","XAUUSD","WTI","SPX","NAS100"]
D = {s: E.lae(s) for s in PAARID}
D = {k: v for k, v in D.items() if v is not None}


def surve_signaal(d, ind, kitsus_lb=72, kitsus_q=0.25, murre_lb=12):
    a = ind["atr"]
    c, h, l = d["close"], d["high"], d["low"]
    kitsas = a < a.rolling(kitsus_lb).quantile(kitsus_q)
    return (((c >= h.rolling(murre_lb).max().shift(1)) & kitsas).astype(float)
            - ((c <= l.rolling(murre_lb).min().shift(1)) & kitsas).astype(float)).fillna(0.0)


w("=" * 100)
w("VOLATIILSUSE KOKKUSURVE -> LÄBIMURRE, täisprotokoll")
w("=" * 100)
w(f"  {'paar':8s} {'teh':>6s} {'teh/a':>7s} {'BRUTO bp':>10s} {'retail':>9s} "
  f"{'ECN':>8s} {'t(bruto)':>9s} {'1.pool':>9s} {'2.pool':>9s}")
w("  " + "-" * 82)
read = []
for sym, d in D.items():
    ind = P.valmista(d)
    kr, ke = E.KULU_RETAIL.get(sym, 1.5), E.KULU_ECN.get(sym, .5)
    sg = surve_signaal(d, ind)
    y = E.tulevik(d, 8)
    r = E.hinda(sg, y, kr)
    if r is None: continue
    re_ = E.hinda(sg, y, ke)
    t = r["t"] + 2*kr/1e4                    # bruto-seeria
    m = len(t)//2
    tb = float(t.mean()/t.std()*np.sqrt(len(t))) if t.std()>0 else 0
    read.append(dict(sym=sym, n=r["n"], teh_a=r["teh_aastas"], bruto=r["bruto"],
                     retail=r["keskm"], ecn=re_["keskm"], tb=tb,
                     p1=float(t[:m].mean()), p2=float(t[m:].mean())))
    w(f"  {sym:8s} {r['n']:6d} {r['teh_aastas']:7.0f} {1e4*r['bruto']:+10.2f} "
      f"{1e4*r['keskm']:+9.2f} {1e4*re_['keskm']:+8.2f} {tb:+9.2f} "
      f"{1e4*float(t[:m].mean()):+9.2f} {1e4*float(t[m:].mean()):+9.2f}")

df = pd.DataFrame(read)
w("")
w(f"  BRUTO plussis {int((df['bruto']>0).sum())}/{len(df)}, keskmine {1e4*df['bruto'].mean():+.2f}bp")
w(f"  ECN   plussis {int((df['ecn']>0).sum())}/{len(df)}, keskmine {1e4*df['ecn'].mean():+.2f}bp")
w(f"  retail plussis {int((df['retail']>0).sum())}/{len(df)}, keskmine {1e4*df['retail'].mean():+.2f}bp")
w(f"  MÕLEMAD pooled bruto-plussis: {int(((df['p1']>0)&(df['p2']>0)).sum())}/{len(df)}")

# ── AUS BASELINE ────────────────────────────────────────────────
w("")
w("=" * 100)
w("AUS BASELINE — juhuslik sisenemine, sama tehingute arv, sama horisont")
w("=" * 100)
w(f"  {'paar':8s} {'strat BRUTO':>12s} {'juhuslik (20x)':>16s} {'p-väärtus':>11s}")
w("  " + "-" * 52)
parem = 0
for _, r in df.iterrows():
    d = D[r["sym"]]; y = E.tulevik(d, 8); kr = E.KULU_RETAIL.get(r["sym"], 1.5)
    juh = []
    for _ in range(20):
        s2 = pd.Series(0.0, index=d.index)
        ix = rng.choice(np.arange(300, len(d)-1), size=int(r["n"]), replace=False)
        s2.iloc[np.sort(ix)] = rng.choice([-1.0,1.0], size=int(r["n"]))
        rr = E.hinda(s2, y, kr)
        if rr: juh.append(rr["bruto"])
    if not juh: continue
    p = float(np.mean([x >= r["bruto"] for x in juh]))
    parem += (p < 0.10)
    w(f"  {r['sym']:8s} {1e4*r['bruto']:+11.2f} {1e4*np.mean(juh):+15.2f} {p:11.3f}")
w("")
w(f"  p<0.10 paaride arv: {parem}/{len(df)}")

# ── PARAMEETRITUNDLIKKUS ────────────────────────────────────────
w("")
w("=" * 100)
w("PARAMEETRITUNDLIKKUS — platoo või üksik tipp?")
w("=" * 100)
w(f"  {'kitsus_lb':>10s} {'kvantiil':>9s} {'murre_lb':>9s} {'BRUTO bp':>10s} "
  f"{'plussis':>9s} {'ECN bp':>9s}")
w("  " + "-" * 60)
plat = 0; kokku_p = 0
for klb in (48, 72, 120):
    for kq in (0.15, 0.25, 0.35):
        for mlb in (6, 12, 24):
            bs, es = [], []
            for sym, d in D.items():
                ind = P.valmista(d)
                kr, ke = E.KULU_RETAIL.get(sym,1.5), E.KULU_ECN.get(sym,.5)
                sg = surve_signaal(d, ind, klb, kq, mlb)
                if int((sg!=0).sum()) < 100: continue
                r = E.hinda(sg, E.tulevik(d,8), kr)
                r2 = E.hinda(sg, E.tulevik(d,8), ke)
                if r: bs.append(r["bruto"]); es.append(r2["keskm"])
            if not bs: continue
            kokku_p += 1
            if np.mean(bs) > 0: plat += 1
            w(f"  {klb:10d} {kq:9.2f} {mlb:9d} {1e4*np.mean(bs):+10.2f} "
              f"{sum(1 for x in bs if x>0):6d}/{len(bs):<2d} {1e4*np.mean(es):+9.2f}")
w("")
w(f"  BRUTO plussis {plat}/{kokku_p} parameetrikombinatsioonist")
w("VALMIS")
