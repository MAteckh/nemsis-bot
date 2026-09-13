"""
KOIK EELREGISTREERITUD VARIANDID.
3 impulssi x 2 kinnitust x 3 hoidmisaega x 3 stoppi x 2 suunda = 108.
Ei lisata uhtegi varianti juurde, ei eemaldata uhtegi.
"""
import warnings; warnings.filterwarnings("ignore")
import math, itertools, pickle
import numpy as np, pandas as pd
import h1engine as E, impulss_engine as I

OUT = "impulss_run.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

FX22 = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
        "EURGBP","EURJPY","EURCHF","EURAUD","EURNZD","GBPJPY","GBPCHF",
        "GBPAUD","GBPCAD","AUDJPY","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"]
MAJORID = FX22[:7]
KULU = {p: E.KULU_RETAIL.get(p, 1.8) for p in FX22}
for p in ("EURNZD","GBPCHF","GBPCAD","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"):
    KULU[p] = 2.2
D = {s: E.lae(s) for s in FX22}
D = {k: v for k, v in D.items() if v is not None}

w("=" * 100)
w("ANDMESTIK (kasutaja punkt 2)")
w("=" * 100)
w(f"  paare: {len(D)}  (majorid {len(MAJORID)}, ristpaarid {len(D)-len(MAJORID)})")
w(f"  ajaskaala: H1")
per_min = min(v.index[0] for v in D.values()); per_max = max(v.index[-1] for v in D.values())
w(f"  periood: {per_min.date()} .. {per_max.date()}")
w(f"  baare kokku: {sum(len(v) for v in D.values()):,}")
w(f"  baare paari kohta: {int(np.median([len(v) for v in D.values()])):,} (mediaan)")
w(f"  bid/ask andmed: EI OLE (ainult OHLC). Tick-andmed: EI OLE.")
w(f"  spread-eeldus: fikseeritud paari kohta, majorid 1.0-1.8bp/pool,")
w(f"                 ristpaarid 2.2bp/pool (uhesuunaline)")
w(f"  komisjon: sisaldub ulaltoodud numbrites (retail-CFD mudel)")
w(f"  slippage: modelleeritud kulu-sweepi kaudu (0-3bp round-trip)")
w("  puuduvad andmed: nadalavahetused puuduvad (normaalne), laupaeva-baare 0")

# ── jooksuta koik variandid ────────────────────────────────────
VARIANDID = list(itertools.product(("A","B","C"), ("JATK","TAGASI"),
                                   (1,2,4), (None,0.75,1.0), (+1,-1)))
w("")
w(f"  eelregistreeritud variante: {len(VARIANDID)}")

read = []
CACHE = {}
for sym, d in D.items():
    for v in ("A","B","C"):
        CACHE[(sym,v)] = I.impulss(d, v)

for (var, kin, hoia, stop, suund) in VARIANDID:
    kogu = []
    for sym, d in D.items():
        sg, tug = CACHE[(sym, var)]
        sg2, nihe = I.kinnitus(d, sg, kin)
        if int((sg2 != 0).sum()) < 20: continue
        t = I.simuleeri(d, sg2, hoia, stop, suund, nihe)
        if t is None or len(t) < 20: continue
        t["sym"] = sym
        t["neto"] = t["bruto"] - 2*KULU[sym]/1e4
        t["tug"] = tug.reindex(t["aeg"]).values
        kogu.append(t)
    if not kogu: continue
    G = pd.concat(kogu, ignore_index=True)
    G = G[np.isfinite(G["bruto"])]
    if len(G) < 200: continue
    b = float(G["bruto"].mean()); n_ = float(G["neto"].mean())
    tt = float(G["bruto"].mean()/G["bruto"].std()*np.sqrt(len(G))) if G["bruto"].std()>0 else 0
    read.append(dict(var=var, kin=kin, hoia=hoia, stop=stop or 0,
                     suund="JATK" if suund>0 else "POOR",
                     n=len(G), bruto=b, neto=n_, t=tt,
                     wr=100*float((G["neto"]>0).mean()),
                     paare=G["sym"].nunique(), data=G))
R = pd.DataFrame([{k: v for k, v in r.items() if k != "data"} for r in read])
DATA = {(r["var"],r["kin"],r["hoia"],r["stop"],r["suund"]): r["data"] for r in read}
with open("data/impulss_tulemused.pkl","wb") as f:
    pickle.dump({"R": R, "DATA": DATA}, f)

w("")
w("=" * 100)
w("KOIK VARIANDID — BRUTO (enne kulusid), sorteeritud")
w("=" * 100)
w(f"  {'var':>4s} {'kinnitus':>9s} {'hoia':>5s} {'stopp':>6s} {'suund':>6s} "
  f"{'tehinguid':>10s} {'BRUTO bp':>10s} {'NETO bp':>9s} {'t':>7s} {'võit%':>7s}")
w("  " + "-" * 88)
for _, r in R.sort_values("bruto", ascending=False).iterrows():
    w(f"  {r['var']:>4s} {r['kin']:>9s} {r['hoia']:>5d} "
      f"{(str(r['stop']) if r['stop'] else '-'):>6s} {r['suund']:>6s} "
      f"{r['n']:10d} {1e4*r['bruto']:+10.2f} {1e4*r['neto']:+9.2f} "
      f"{r['t']:+7.2f} {r['wr']:6.1f}%")

w("")
w("=" * 100)
w("JATKUVUS vs POORDUMINE — kumb on tugevam? (kasutaja punkt 7)")
w("=" * 100)
w(f"  {'suund':>8s} {'variante':>9s} {'keskm BRUTO':>13s} {'parim BRUTO':>13s} "
  f"{'plussis':>9s} {'keskm NETO':>12s}")
w("  " + "-" * 70)
for s_ in ("JATK", "POOR"):
    g = R[R["suund"] == s_]
    w(f"  {s_:>8s} {len(g):9d} {1e4*g['bruto'].mean():+12.2f} "
      f"{1e4*g['bruto'].max():+12.2f} {int((g['bruto']>0).sum()):5d}/{len(g):<3d} "
      f"{1e4*g['neto'].mean():+11.2f}")

w("")
w("  Impulsi variandi kaupa:")
w(f"  {'variant':>8s} {'JATK bruto':>12s} {'POOR bruto':>12s} {'kumb tugevam':>14s}")
w("  " + "-" * 50)
for v in ("A","B","C"):
    j = R[(R["var"]==v)&(R["suund"]=="JATK")]["bruto"].mean()
    p_ = R[(R["var"]==v)&(R["suund"]=="POOR")]["bruto"].mean()
    w(f"  {v:>8s} {1e4*j:+11.2f} {1e4*p_:+11.2f} "
      f"{('JÄTKUVUS' if j>p_ else 'PÖÖRDUMINE'):>14s}")
w("VALMIS")
