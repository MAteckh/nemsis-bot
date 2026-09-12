"""
OTSUSTAV TEST SKANNI KOHTA: mitu "labijat" annaks PUHAS MURA?

run_intraday_scan.py leidis 220 paarist 3 labijat. See arv on mottetu,
kuni pole teada null-jaotus. Meetod: asenda ennustaja signaal
juhusliku, SAMA STRUKTUURIGA seeriaga (sama tehingute arv, sama
ajastus, juhuslik suund) ja jooksuta TAPSELT sama sool labi. Korda.

Kui muraga tuleb tupiliselt 3 labijat, on meie 3 vaartusetud.
Kui muraga tuleb 0-1, on leid paris.

Teeb ka: kas sihtmargi paevabaar uldse SISALDAB suletud perioodi?
Kui ei (nt kuld kaupleb 23h), siis "paevasisene" hoidmine labib
rollover'i ja finantseerimiskulu EI OLE null — mis oli kogu
selle idee ainus struktuurne eelis.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(11092026)
SYMS = ["SPX","NAS100","GER40","JP225","UK100","XAUUSD","XAGUSD","WTI","NGAS",
        "COPPER","US10Y","VIX","EURUSD","USDJPY","GBPUSD","AUDUSD","NZDUSD",
        "USDCAD","USDCHF","EURJPY","BTCUSD","ETHUSD"]

def load(sym):
    p = os.path.join(R.DATA, f"{sym}_d.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"):
        if c not in d.columns: return None
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

D = {s: load(s) for s in SYMS}
D = {k: v for k, v in D.items() if v is not None and len(v) > 1200}
TGT = ["BTCUSD","COPPER","ETHUSD","GER40","JP225","NAS100","NGAS","SPX",
       "WTI","XAGUSD","XAUUSD"]

print("=" * 100)
print("1) KAS SIHTMÄRGI PÄEVABAARIS ON ÜLDSE SULETUD PERIOOD?")
print("=" * 100)
print("   Kui lünk ~0, kaupleb instrument ~24h => 'päevasisene' positsioon läbib")
print("   rollover'i => SWAP KEHTIB => idee ainus struktuurne eelis kaob.")
print()
print(f"   {'sümbol':10s} {'|lünk| med':>12s} {'|päevasisene| med':>19s} {'lünk/päevasisene':>18s} {'otsus':>12s}")
print("   " + "-" * 76)
fin_free = []
for s in TGT:
    d = D[s]
    g = (d["Open"]/d["Close"].shift(1)-1).abs().median()*1e4
    i = (d["Close"]/d["Open"]-1).abs().median()*1e4
    ratio = g/max(i,1e-9)
    good = ratio > 0.30
    if good: fin_free.append(s)
    print(f"   {s:10s} {g:11.1f}bp {i:18.1f}bp {ratio:18.2f} "
          f"{'PÄRIS PAUS' if good else 'EI, ~24h':>12s}")
print(f"\n   Tõeliselt finantseerimisvabad sihtmärgid: {', '.join(fin_free) if fin_free else 'MITTE ÜKSKI'}")

def sharpe(x):
    return float(x.mean()/x.std()*np.sqrt(252)) if len(x) > 5 and x.std() > 0 else 0.0

def parts(pred, tgt, thr=1.0, lb=60):
    p, t = D[pred], D[tgt]
    ix = p.index.intersection(t.index)
    if len(ix) < 1200: return None
    p, t = p.reindex(ix), t.reindex(ix)
    y = t["Close"]/t["Open"]-1
    y = y[y.abs() < 0.25]
    r = p["Close"]/p["Close"].shift(1)-1
    z = (r/r.rolling(lb).std()).shift(1).reindex(y.index)
    w = (np.sign(z)*(z.abs() > thr)).fillna(0.0)
    rt = 2*R.COST_BP.get(tgt, 5.0)/1e4
    return y, w, rt

def screen_count(randomize=False):
    """Loeb, mitu paari labib range soela. randomize=True => juhuslikud suunad."""
    cnt, names = 0, []
    for pred in D:
        for tgt in TGT:
            if pred == tgt: continue
            pp = parts(pred, tgt)
            if pp is None: continue
            y, w, rt = pp
            if int((w != 0).sum()) < 150: continue
            mid = len(y)//2
            ws = {}
            for t_ in (0.5,0.75,1.0,1.25,1.5):
                q = parts(pred, tgt, thr=t_)
                if q is None: continue
                ws[t_] = q[1]
            if randomize:
                for k in ws:
                    v = ws[k].values.copy()
                    nz = v != 0
                    v[nz] = rng.choice([-1.0,1.0], size=int(nz.sum()))
                    ws[k] = pd.Series(v, index=ws[k].index)
                w = ws[1.0]
            nets = {k: (v*y - (v != 0).astype(float)*rt).fillna(0.0) for k, v in ws.items()}
            net = nets[1.0]
            s_all, s1, s2 = sharpe(net), sharpe(net.iloc[:mid]), sharpe(net.iloc[mid:])
            bt, bs = None, -9e9
            for k, nv in nets.items():
                if int((ws[k].iloc[:mid] != 0).sum()) < 80: continue
                sv = sharpe(nv.iloc[:mid])
                if sv > bs: bs, bt = sv, k
            oos = sharpe(nets[bt].iloc[mid:]) if bt is not None else 0.0
            if s_all > 0.5 and s1 > 0 and s2 > 0 and oos > 0.5:
                cnt += 1; names.append(f"{pred}->{tgt}")
    return cnt, names

real, rnames = screen_count(False)
print()
print("=" * 100)
print("2) NULL-JAOTUS — mitu läbijat annab MÜRA?")
print("=" * 100)
print(f"   PÄRIS andmed: {real} läbijat  ({', '.join(rnames)})")
N = 40
sims = []
for i in range(N):
    c, _ = screen_count(True)
    sims.append(c)
sims = np.array(sims)
print(f"   MÜRA ({N} katset): keskmine {sims.mean():.2f}  mediaan {np.median(sims):.0f}  "
      f"max {sims.max()}  jaotus {np.bincount(sims)}")
p = float((sims >= real).mean())
print(f"\n   p-väärtus (kui tihti müra annab >= {real} läbijat): {p:.3f}")
if p < 0.05:
    print("   => LEID ON PÄRIS: müra ei tekita nii palju läbijaid.")
else:
    print("   => LEID EI OLE ERISTATAV MÜRAST. Need 3 on tõenäoliselt juhus.")
