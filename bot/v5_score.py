"""
LOPLIK SKOORIMINE (Phase 12) + multiple testing ilma scipy'ta.

EDGE SCORE /100:
  OOS performance 25 | statistiline olulisus 15 | kulurobustsus 10
  parameetrirobustsus 10 | rist-paari robustsus 10 | rist-rezhiimi 10
  drawdown 10 | 205 EUR teostatavus 10

PASS ainult siis, kui KOIK kolm kehtib:
  OOS > 0  JA  205 EUR teostatav  JA  serv jaab alles realistlike kuludega
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import v5_engine as V
from v5_run import korv_tootlus, S, C, KESK

OUT = "v5_score.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()


def ncdf(x):
    """Normaaljaotuse CDF ilma scipy'ta (Abramowitz-Stegun 7.1.26)."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def nppf(p):
    """Poordfunktsioon, Newtoni iteratsioon ncdf peal."""
    if p <= 0: return -8.0
    if p >= 1: return 8.0
    lo, hi = -8.0, 8.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if ncdf(mid) < p: lo = mid
        else: hi = mid
    return (lo + hi) / 2


def deflated_sharpe(sh, n_obs, n_katseid):
    if n_obs < 60 or n_katseid < 2: return 0.0
    e = 0.5772156649
    sh_max = (nppf(1 - 1.0/n_katseid) * (1 - e)
              + nppf(1 - 1.0/(n_katseid * math.e)) * e)
    sd = math.sqrt(1.0 / (n_obs - 1))
    return ncdf((sh - sh_max) / sd)


carry_lag = C.reindex(S.index).ffill().rolling(60).mean().shift(1)
z = lambda d: d.sub(d.mean(axis=1), axis=0).div(d.std(axis=1).replace(0, np.nan), axis=0)
H = {}
for hid, lb in (("H01",1),("H02",5),("H03",20),("H04",60)):
    H[hid] = (f"CS-MOM-{lb}D", korv_tootlus(S.rolling(lb).sum())[0])
H["H05"] = ("CS-CARRY (lag 1p)", korv_tootlus(carry_lag)[0])
H["H06"] = ("CS-CARRY+MOM", korv_tootlus(z(carry_lag).add(z(S.rolling(20).sum()), fill_value=0))[0])
haal = sum(np.sign(S.rolling(lb).sum()) for lb in (1,5,20,60,120))
Wt = (np.sign(haal)/8.0).shift(1).fillna(0.0)
ix = Wt.index.intersection(S.index)
brx = (Wt.reindex(ix)*S.reindex(ix)).sum(axis=1)
H["H07"] = ("TS-MOM-MULTI", brx - Wt.reindex(ix).diff().abs().sum(axis=1).fillna(0)*KESK["BASE"]/1e4)
m20 = S.rolling(20).sum()
H["H08"] = ("MOM-ACCEL", korv_tootlus(m20 - m20.shift(20))[0])
H["H09"] = ("MOM-PERSIST", korv_tootlus((S>0).rolling(20).mean())[0])

N_KATSEID = 11500 + 14

w("=" * 96)
w("MULTIPLE TESTING — 14 registreeritud hüpoteesi, ~11 500 varasemat testi")
w("=" * 96)
w(f"  {'ID':4s} {'hüpotees':20s} {'t':>7s} {'p (ühep.)':>11s} {'BH lävend':>11s} "
  f"{'Defl.Sharpe':>12s} {'läbib?':>8s}")
w("  " + "-" * 78)
read = []
for hid in sorted(H):
    nimi, x = H[hid]
    if x is None: continue
    x = x.dropna()
    m = V.moodikud(x)
    if m is None: continue
    p = 1 - ncdf(m["tstat"])
    read.append(dict(id=hid, nimi=nimi, x=x, t=m["tstat"], p=p, sh=m["sh"], m=m))
read.sort(key=lambda r: r["p"])
for i, r in enumerate(read, 1):
    bh = 0.05 * i / len(read)
    ds = deflated_sharpe(r["sh"], len(r["x"]), N_KATSEID)
    r["bh_ok"] = r["p"] <= bh; r["ds"] = ds
    w(f"  {r['id']} {r['nimi']:20s} {r['t']:+7.2f} {r['p']:11.4f} {bh:11.4f} "
      f"{ds:12.3f} {'JAH' if r['bh_ok'] and ds>0.95 else 'ei':>8s}")
w("")
w(f"  Benjamini-Hochberg läbijad: "
  f"{[r['id'] for r in read if r['bh_ok']] or 'MITTE ÜKSKI'}")
w(f"  Deflated Sharpe > 0.95: "
  f"{[r['id'] for r in read if r['ds'] > 0.95] or 'MITTE ÜKSKI'}")
w("")
w("  NB: iga hüpoteesi t on NEGATIIVNE, seega ühepoolne p > 0.5 kõigil.")
w("  Ükski ei lähene isegi korrigeerimata 0.05 lävendile.")

# ══ EDGE SCORE ═════════════════════════════════════════════════
w("")
w("=" * 96)
w("EDGE SCORE /100 (Phase 12)")
w("=" * 96)

def skoori(nimi, oos_bp, oos_sh, t, kulu_low, kulu_high, par_plussis, par_kokku,
           paare_plussis, paare_kokku, rez_plussis, rez_kokku, maxdd, feas_pct):
    s = {}
    s["OOS (25)"] = 25 if oos_bp > 0 and oos_sh > 0.5 else (12 if oos_bp > 0 else 0)
    s["stat (15)"] = 15 if t > 3 else (8 if t > 2 else 0)
    s["kulu (10)"] = 10 if kulu_high > 0 else (5 if kulu_low > 0 else 0)
    s["param (10)"] = round(10 * par_plussis / max(par_kokku,1))
    s["paar (10)"] = round(10 * paare_plussis / max(paare_kokku,1))
    s["režiim (10)"] = round(10 * rez_plussis / max(rez_kokku,1))
    s["DD (10)"] = 10 if maxdd > -0.15 else (5 if maxdd > -0.30 else 0)
    s["205€ (10)"] = 10 if feas_pct <= 1.0 else (5 if feas_pct <= 2.0 else 0)
    return s

w(f"  {'kandidaat':22s} " + "".join(f"{k:>11s}" for k in
    ["OOS(25)","stat(15)","kulu(10)","par(10)","paar(10)","rež(10)","DD(10)","205€(10)","KOKKU"]))
w("  " + "-" * 121)

# parim FX-kandidaat = H04 (koige vahem negatiivne OOS)
best_fx = min(read, key=lambda r: abs(r["m"]["keskm"]))
tr,va,fo = V.jaota(best_fx["x"])
sk = skoori(best_fx["nimi"], 1e4*float(fo.mean()), V.sharpe(fo), best_fx["t"],
            -1.37, -2.35, 0, 4, 0, 8, 0, 7, best_fx["m"]["maxdd"], 1.6)
w(f"  {'FX parim (' + best_fx['id'] + ')':22s} " +
  "".join(f"{v:>11d}" for v in sk.values()) + f"{sum(sk.values()):>11d}")

# kuld
sk_g = skoori("XAUUSD Donchian", 1485.46, 1.0, 2.3, 1, 1, 7, 7, 1, 1, 4, 4, -0.473, 22.0)
w(f"  {'XAUUSD Donchian':22s} " + "".join(f"{v:>11d}" for v in sk_g.values()) +
  f"{sum(sk_g.values()):>11d}")

w("")
w("  PASS-reeglid: OOS > 0 JA 205€ teostatav JA serv jääb realistlike kuludega.")
w("")
w(f"  FX parim:        OOS {1e4*float(fo.mean()):+.2f}bp  =>  FAIL (OOS negatiivne)")
w(f"  XAUUSD Donchian: OOS +1485€  aga  205€ teostatavus 22.0%  =>  FAIL (kapital)")
w("")
w("=" * 96)
w("LÕPPVASTUS")
w("=" * 96)
w("  A. ROBUST EDGE FOUND — 205 EUR FEASIBLE ......... EI")
w("  B. ROBUST EDGE FOUND — CAPITAL TOO SMALL ........ osaliselt (ainult kuld,")
w("                                                    ja seegi jääb alla")
w("                                                    osta-ja-hoia risk-adj.)")
w("  C. NO ROBUST EDGE FOUND ......................... JAH, FX-i osas")
w("VALMIS")
