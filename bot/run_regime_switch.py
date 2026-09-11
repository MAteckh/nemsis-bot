"""
REŽIIMIPÕHINE LÜLITUMINE — kasutaja algne idee (juuli).

Loogika: ADX järgi määra turu režiim.
  trend      (ADX >= 25) -> Donchian breakout (trendijärgimine)
  range      (ADX <= 18) -> Bollinger fade (mean reversion)
  transition (vahepeal)  -> ÄRA KAUPLE

Me ehitasime detect_regime() juulis, aga ei ole seda kunagi
täiskuludega ja robustsuskontrolliga lõpuni valideerinud. See test
sulgeb selle lünga.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R, strategies as S, gold_logic

MK = 0.030

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

def cost(w, sym):
    turn = (w-w.shift(1)).abs().fillna(0.0)
    sp = turn * R.COST_BP.get(sym, 3.0)/10000.0
    rate = R.load_rates(w.index).reindex(w.index).ffill()
    fin = w.shift(1).clip(lower=0)*rate/252.0 + w.shift(1).abs()*MK/252.0
    return sp.fillna(0.0), fin.fillna(0.0)

def regime_weights(d, adx_trend=25.0, adx_range=18.0, don_lb=20, bb_lb=20, bb_k=2.0):
    """Positsioonikaal iga päev: režiimist sõltuv signaal."""
    c = d["close"]
    r = c.pct_change()
    # ADX arvuta gold_logic funktsiooniga, jooksvalt
    adx = pd.Series(np.nan, index=d.index)
    hv, lv, cv = d["high"].values, d["low"].values, d["close"].values
    for i in range(40, len(d)):
        s = max(0, i-60)
        adx.iloc[i] = gold_logic.calc_adx(hv[s:i+1], lv[s:i+1], cv[s:i+1])
    # Donchian signaal (trend)
    hi = c.rolling(don_lb).max().shift(1)
    lo = c.rolling(don_lb).min().shift(1)
    don = pd.Series(0.0, index=d.index)
    don[c > hi] = 1.0
    don[c < lo] = -1.0
    don = don.replace(0.0, np.nan).ffill().fillna(0.0)
    # Bollinger fade (range)
    ma = c.rolling(bb_lb).mean()
    sd = c.rolling(bb_lb).std()
    bb = pd.Series(0.0, index=d.index)
    bb[c > ma + bb_k*sd] = -1.0
    bb[c < ma - bb_k*sd] = 1.0
    # lülitu režiimi järgi
    w = pd.Series(0.0, index=d.index)
    trend_mask = adx >= adx_trend
    range_mask = adx <= adx_range
    w[trend_mask] = don[trend_mask]
    w[range_mask] = bb[range_mask]
    return w.shift(1).fillna(0.0), adx

print("=" * 112)
print("REŽIIMIPÕHINE LÜLITUMINE — täiskuludega, 10 aastat")
print("=" * 112)
print(f"{'instrument':10s} {'trend%':>7s} {'range%':>7s} {'CAGR':>8s} {'Sharpe':>7s}  "
      f"{'vs osta-hoia':>13s}")
print("-" * 112)

rows = []
for sym in sorted(R.COST_BP):
    p = os.path.join(R.DATA, f"{sym}_d.csv")
    if not os.path.exists(p): continue
    d = load(sym)
    if len(d) < 300: continue
    w, adx = regime_weights(d)
    r = d["close"].pct_change()
    sp, fin = cost(w, sym)
    net = (w*r - sp - fin).fillna(0.0)
    eq = (1+net).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() > 0 else 0
    bh = (1+r.fillna(0)).cumprod(); bh_cagr = bh.iloc[-1]**(1/yrs)-1
    tpct = 100*(adx >= 25).mean(); rpct = 100*(adx <= 18).mean()
    rows.append((sym, cagr, sh, bh_cagr))
    print(f"{sym:10s} {tpct:6.1f}% {rpct:6.1f}% {100*cagr:+7.1f}% {sh:+7.2f}  "
          f"{100*bh_cagr:+12.1f}%")

print("-" * 112)
pos = sum(1 for x in rows if x[1] > 0)
beat_bh = sum(1 for x in rows if x[1] > x[3])
print(f"  Positiivse CAGR-iga: {pos}/{len(rows)}   Osta-ja-hoia löövad: {beat_bh}/{len(rows)}")
print(f"  Keskmine Sharpe: {np.mean([x[2] for x in rows]):+.2f}")
