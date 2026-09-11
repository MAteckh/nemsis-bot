"""
VIX-pohine SPX signaal — hirmuindeksi jars tous ennustab dokumenteeritult
luhiajalist SPX taastumist (volatiilsuse riskipreemia). UUS ANDMEALLIKAS,
mida me pole varem kasutanud - mitte lihtsalt hinnaandmete teisendus.

Klassikaline versioon: kui VIX toosb X% uhe paevaga voi uletab N-paevase
percentiili, osta SPX ja hoia kuni VIX normaliseerub voi fikseeritud
horisont taitub.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

def load_close(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    c = pd.to_numeric(d.get("Close", d.get("close")), errors="coerce")
    return c.dropna()

vix = load_close("VIX")
spx = load_close("SPX")
idx = vix.index.intersection(spx.index)
vix, spx = vix.reindex(idx), spx.reindex(idx)
r_spx = spx.pct_change()

MK = 0.030
def cost_full(w, sym, spread_bp):
    turn = (w - w.shift(1)).abs().fillna(0.0)
    sp = turn * spread_bp / 10000.0
    rate = R.load_rates(w.index).reindex(w.index).ffill()
    fin = w.shift(1).clip(lower=0) * rate / 252.0 + w.shift(1).abs() * MK / 252.0
    return sp.fillna(0.0), fin.fillna(0.0)

print("=" * 100)
print("A) VIX PERCENTIILI SIGNAAL — osta SPX kui VIX yle N-paeva X-percentiili")
print("=" * 100)
for lookback in (60, 120, 252):
    for pct in (80, 90, 95):
        thr = vix.rolling(lookback).quantile(pct/100)
        sig = (vix > thr).astype(float)
        w = sig.shift(1).fillna(0.0)
        sp, fin = cost_full(w, "SPX", R.COST_BP["SPX"])
        net = w*r_spx - sp - fin
        n_days = int(sig.sum())
        if n_days < 20: continue
        eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
        sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
        print(f"  lookback={lookback:3d} percentiil={pct}  ({100*n_days/len(sig):4.1f}% ajast)  "
              f"CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}")

print()
print("=" * 100)
print("B) VIX SPIKE SIGNAAL — osta kui VIX toosb >X% uhe paevaga, hoia N paeva")
print("=" * 100)
vix_chg = vix.pct_change()
for spike in (0.10, 0.15, 0.20, 0.25):
    for hold in (3, 5, 10, 20):
        trigger = vix_chg > spike
        w = pd.Series(0.0, index=idx)
        active_until = pd.Timestamp.min
        for i, t in enumerate(idx):
            if trigger.iloc[i] and t > active_until:
                active_until = idx[min(i+hold, len(idx)-1)]
            if t <= active_until and i > 0 and idx[i-1] <= active_until:
                w.iloc[i] = 1.0
        w = w.shift(1).fillna(0.0)
        sp, fin = cost_full(w, "SPX", R.COST_BP["SPX"])
        net = w*r_spx - sp - fin
        n_trig = int(trigger.sum())
        if n_trig < 10: continue
        eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
        sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
        print(f"  spike>{100*spike:.0f}%  hoia {hold:2d}p  ({n_trig} paastumist)  "
              f"CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}")
