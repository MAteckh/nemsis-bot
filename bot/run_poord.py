"""
KOIGE PALJUTOOTAVAM LEID: PDF-I SETUPID TAGURPIDI.

MIDA LEITI: PDF-i trend-pullback setup annab bruto -1.3bp. Sama setup
VASTUPIDISES suunas annab +2.5bp. See tahendab, et H1 FX-is
tagasitomme EI JATKU trendi suunas — ta jatkub tagasitomme suunas.

MEHHANISM, mis seda toetab: luhiajaline poordumine (short-horizon
reversal) on FX-is dokumenteeritud. "Pullback to EMA20 in an uptrend"
on tegelikult varske luhiajaline langus; selle OSTMINE on momentumi
vastu kauplemine tunniskaalal.

AGA ETTEVAATUST: ma vaatasin nelja perekonna vastupidiseid ja valisin
parima. See on valik. Seepolikult labib see leid nuud TAIELIKU
protokolli, mitte ainult "vaata kui ilus".

  1) koik 15 paari, ainult vastupidine suund
  2) 60/20/20 — valik ainult A-st, moot C-l
  3) AUS baseline: juhuslik labib sama valiku
  4) kaks kulutaset: retail ja ECN
  5) kas see tootab ka siis, kui ADX/RSI filtrid ara votta?
     (kui jah, ei ole tegu PDF-i setupiga vaid lihtsalt poordumisega)
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P, paar_config as C
from run_paarid import variandid, signaal

rng = np.random.default_rng(1609)
OUT = "poord_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

TP_PAARID = [s for s, c in C.PAARID.items() if c["rezim"] == "trend_pullback"]

w("=" * 100)
w("PDF-i TREND-PULLBACK SETUP, SUUND ÜMBER PÖÖRATUD")
w("=" * 100)
w(f"   paarid, millel PDF määrab trend_pullback: {', '.join(TP_PAARID)}")
w("")
w(f"   {'paar':8s} {'teh':>5s} {'võit%':>7s} {'BRUTO bp':>9s} "
  f"{'retail NETO':>12s} {'ECN NETO':>10s} {'t':>6s}")
w("   " + "-" * 62)
read = []
for sym in TP_PAARID:
    cfg = C.PAARID[sym]
    d = E.lae(sym)
    if d is None: continue
    ind = P.valmista(d)
    sess = C.SESS[cfg["sess"]]
    kr, ke = E.KULU_RETAIL.get(sym, 1.5), E.KULU_ECN.get(sym, 0.5)
    n = len(d); i60, i80 = int(n*.60), int(n*.80)
    p60, p80 = d.index[i60], d.index[i80]
    for v in variandid(sym, cfg):
        sg = -signaal(d, cfg, v, ind)          # <<< PÖÖRATUD
        if int((sg != 0).sum()) < 40: continue
        t = P.simuleeri(d, sg, v["sl"], v["tp"], kr, ind, sess)
        if t is None or len(t) < 40: continue
        x = t["tulem"].values; b = t["bruto"].values
        ecn = b - 2 * ke / 1e4
        tA = t[t["aeg"] < p60]["bruto"].values - 2*ke/1e4
        tB = t[(t["aeg"]>=p60)&(t["aeg"]<p80)]["bruto"].values - 2*ke/1e4
        tC = t[t["aeg"] >= p80]["bruto"].values - 2*ke/1e4
        read.append(dict(sym=sym, adx=v["adx"], sl=v["sl"], tp=v["tp"], n=len(t),
                         wr=100*float((x>0).mean()), bruto=float(b.mean()),
                         retail=float(x.mean()), ecn=float(ecn.mean()),
                         tstat=float(x.mean()/x.std()*np.sqrt(len(x))) if x.std()>0 else 0,
                         A=float(tA.mean()) if len(tA)>=15 else np.nan, nA=len(tA),
                         B=float(tB.mean()) if len(tB)>=10 else np.nan, nB=len(tB),
                         Cc=float(tC.mean()) if len(tC)>=10 else np.nan, nC=len(tC)))
df = pd.DataFrame(read)
for sym in TP_PAARID:
    g = df[df["sym"] == sym]
    if not len(g): continue
    r = g.iloc[len(g)//2]                      # KESKMINE variant, mitte parim
    w(f"   {r['sym']:8s} {r['n']:5d} {r['wr']:6.1f}% {1e4*r['bruto']:+9.1f} "
      f"{1e4*r['retail']:+12.1f} {1e4*r['ecn']:+10.1f} {r['tstat']:+6.2f}")

w("")
w(f"   variante {len(df)};  BRUTO plussis {int((df['bruto']>0).sum())} "
  f"({100*(df['bruto']>0).mean():.0f}%);  retail NETO plussis "
  f"{int((df['retail']>0).sum())} ({100*(df['retail']>0).mean():.0f}%);  "
  f"ECN NETO plussis {int((df['ecn']>0).sum())} ({100*(df['ecn']>0).mean():.0f}%)")
w(f"   keskmine: BRUTO {1e4*df['bruto'].mean():+.1f}bp   "
  f"retail {1e4*df['retail'].mean():+.1f}bp   ECN {1e4*df['ecn'].mean():+.1f}bp")

# ── 60/20/20 ────────────────────────────────────────────────────
w("")
w("=" * 100)
w("60/20/20 — vali A-st, MÕÕDA C-l (ECN-kuludega, et anda leiule parim võimalus)")
w("=" * 100)
w(f"   {'paar':8s} {'ADX/SL/TP':>14s} {'A (valik)':>11s} {'B':>9s} "
  f"{'C (FINAL OOS)':>14s} {'C teh':>7s}")
w("   " + "-" * 68)
cc, pos = [], 0
for sym in TP_PAARID:
    g = df[(df["sym"] == sym) & df["A"].notna() & df["Cc"].notna()]
    if not len(g): 
        w(f"   {sym:8s} — liiga vähe tehinguid"); continue
    r = g.loc[g["A"].idxmax()]
    cc.append(r["Cc"]); pos += (r["Cc"] > 0)
    w(f"   {sym:8s} {f'{r.adx:.0f}/{r.sl:.2f}/{r.tp:.1f}':>14s} {1e4*r['A']:+10.1f} "
      f"{1e4*r['B']:+8.1f} {1e4*r['Cc']:+13.1f} {int(r['nC']):7d}"
      f"{'  <<<' if r['Cc']>0 else ''}")
if cc:
    w("")
    w(f"   FINAL OOS plussis {pos}/{len(cc)}, keskmine {1e4*np.nanmean(cc):+.1f}bp")

# ── AUS BASELINE ────────────────────────────────────────────────
w("")
w("=" * 100)
w("AUS BASELINE — juhuslik sisenemine läbib SAMA valiku (parim N seast)")
w("=" * 100)
w(f"   {'paar':8s} {'strat ECN':>10s} {'juhu ECN (parim)':>17s} {'vahe':>8s}")
w("   " + "-" * 48)
vahed = []
for sym in TP_PAARID:
    g = df[df["sym"] == sym]
    if not len(g): continue
    r = g.loc[g["ecn"].idxmax()]
    d = E.lae(sym); ind = P.valmista(d)
    ke = E.KULU_ECN.get(sym, .5); sess = C.SESS[C.PAARID[sym]["sess"]]
    n = len(d); juh = []
    for _ in range(len(g)):
        m = max(int(r["n"]), 40)
        idx = rng.choice(np.arange(250, n-1), size=m, replace=False)
        s2 = pd.Series(0.0, index=d.index)
        s2.iloc[np.sort(idx)] = rng.choice([-1.0, 1.0], size=m)
        t2 = P.simuleeri(d, s2, r["sl"], r["tp"], ke, ind, sess)
        if t2 is not None and len(t2) >= 30:
            juh.append(float((t2["bruto"] - 2*ke/1e4).mean()))
    if not juh: continue
    jm = max(juh)
    vahed.append(r["ecn"] - jm)
    w(f"   {sym:8s} {1e4*r['ecn']:+9.1f} {1e4*jm:+16.1f} {1e4*(r['ecn']-jm):+7.1f}")
w("")
w(f"   Juhuslikust parem: {sum(1 for v in vahed if v>0)}/{len(vahed)}   "
  f"keskmine vahe {1e4*np.mean(vahed):+.1f}bp")

# ── KAS FILTRID ÜLDSE LOEVAD? ───────────────────────────────────
w("")
w("=" * 100)
w("KAS PDF-i FILTRID (ADX, RSI, EMA) ÜLDSE ANNAVAD MIDAGI?")
w("=" * 100)
w("   Võrdlus: pööratud setup KÕIGI filtritega vs PALJAS pöördumine")
w("   (lihtsalt: hind ristub EMA20-ga -> mine vastassuunda)")
w("")
w(f"   {'paar':8s} {'PDF filtritega':>15s} {'PALJAS pööre':>14s} {'filtrite panus':>16s}")
w("   " + "-" * 58)
for sym in TP_PAARID:
    cfg = C.PAARID[sym]
    d = E.lae(sym); ind = P.valmista(d)
    ke = E.KULU_ECN.get(sym, .5); sess = C.SESS[cfg["sess"]]
    v = variandid(sym, cfg)[len(variandid(sym, cfg))//2]
    t1 = P.simuleeri(d, -signaal(d, cfg, v, ind), v["sl"], v["tp"], ke, ind, sess)
    c_ = d["close"]; ef = c_.ewm(span=cfg["ema"][0]).mean()
    paljas = (((c_ > ef) & (c_.shift(1) <= ef.shift(1))).astype(float)
              - ((c_ < ef) & (c_.shift(1) >= ef.shift(1))).astype(float))
    t2 = P.simuleeri(d, -paljas, v["sl"], v["tp"], ke, ind, sess)
    a = float(t1["tulem"].mean()) if t1 is not None and len(t1) > 30 else np.nan
    b = float(t2["tulem"].mean()) if t2 is not None and len(t2) > 30 else np.nan
    w(f"   {sym:8s} {1e4*a:+14.1f} {1e4*b:+13.1f} {1e4*(a-b):+15.1f}")
w("VALMIS")
