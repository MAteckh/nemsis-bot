"""
BREAKOUT-STRADDLE AUS TEST H1-ANDMETEGA.

run_vol_breakout.py andis Sharpe +4.0, mis on ebausutav. Pohjus:
paevabaar (O/H/L/C) EI UTLE, kumb tase tabati ESIMESENA. Kui molemad
tabati, eeldasin fikseeritud vaikest kahjumit — see peidab paris
kahjumid ara.

Siin simuleerin TUNNIBAARIDEGA: kaia paev labi tund-tunnilt, vaata
mis tegelikult juhtus, mis jarjekorras. See on aus.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

def load_h1(s):
    p = os.path.join(R.DATA, f"{s}_h1.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

def simulate(sym, k, reverse_on_opposite=True):
    h1 = load_h1(sym)
    if h1 is None: return None
    cost = 2*R.COST_BP.get(sym, 5.0)/1e4
    days = list(h1.groupby(h1.index.normalize()))
    # ATR eelmiste paevade pealt
    dd = h1.groupby(h1.index.normalize()).agg(
        Open=("Open","first"), High=("High","max"),
        Low=("Low","min"), Close=("Close","last"))
    pc = dd["Close"].shift(1)
    tr = pd.concat([dd["High"]-dd["Low"], (dd["High"]-pc).abs(),
                    (dd["Low"]-pc).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().shift(1)
    out = []
    for day, bars in days:
        a = atr.get(day, np.nan)
        if not np.isfinite(a) or len(bars) < 3: continue
        o = float(bars["Open"].iloc[0])
        up, dn = o + k*a, o - k*a
        pos, entry, pnl, ntr = 0, 0.0, 0.0, 0
        for _, b in bars.iterrows():
            hi, lo = float(b["High"]), float(b["Low"])
            if pos == 0:
                if hi >= up:                       # konservatiivne: up esimesena
                    pos, entry, ntr = 1, up, ntr+1
                    if lo <= dn and reverse_on_opposite:
                        pnl += (dn-entry)/entry - cost
                        pos, entry, ntr = -1, dn, ntr+1
                elif lo <= dn:
                    pos, entry, ntr = -1, dn, ntr+1
            elif pos == 1 and lo <= dn and reverse_on_opposite:
                pnl += (dn-entry)/entry - cost
                pos, entry, ntr = -1, dn, ntr+1
            elif pos == -1 and hi >= up and reverse_on_opposite:
                pnl += (entry-up)/entry - cost
                pos, entry, ntr = 1, up, ntr+1
        if pos != 0:
            c = float(bars["Close"].iloc[-1])
            pnl += ((c-entry)/entry if pos == 1 else (entry-c)/entry) - cost
        out.append((day, pnl, ntr))
    if not out: return None
    r = pd.Series([x[1] for x in out], index=[x[0] for x in out])
    ntr = sum(x[2] for x in out)
    return r, ntr

print("=" * 100)
print("BREAKOUT-STRADDLE H1-ANDMETEGA (päris teekond, päris järjekord)")
print("=" * 100)
print(f"  {'sümbol':9s} {'k':>5s} {'päevi':>7s} {'tehinguid':>10s} {'NETO/p':>10s} "
      f"{'CAGR':>9s} {'Sharpe':>8s}")
print("  " + "-" * 62)
for sym in ("XAUUSD", "NAS100", "SPX", "WTI"):
    for k in (0.25, 0.5, 0.75, 1.0):
        res = simulate(sym, k)
        if res is None:
            continue
        r, ntr = res
        if len(r) < 200: continue
        eq = (1+r).cumprod(); yrs = len(r)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
        sh = r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else 0
        print(f"  {sym:9s} {k:5.2f} {len(r):7d} {ntr:10d} {1e4*r.mean():+9.2f}bp "
              f"{100*cagr:+8.1f}% {sh:+8.2f}")

print()
print("=" * 100)
print("VÕRDLUS: mida päevabaari-versioon SAMA perioodi kohta väitis")
print("=" * 100)
h1 = load_h1("XAUUSD")
d = pd.read_csv(os.path.join(R.DATA, "XAUUSD_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
d = d[~d.index.duplicated(keep="last")]
for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna()
d = d[(d.index >= h1.index[0].normalize()) & (d.index <= h1.index[-1].normalize())]
o,hh,l,c = d["Open"],d["High"],d["Low"],d["Close"]
pc = c.shift(1)
tr = pd.concat([hh-l,(hh-pc).abs(),(l-pc).abs()],axis=1).max(axis=1)
atr = tr.rolling(14).mean().shift(1)
cost = 2*R.COST_BP["XAUUSD"]/1e4
for k in (0.25, 0.5):
    up,dn = o+k*atr, o-k*atr
    L,S = hh>=up, l<=dn
    ret = pd.Series(0.0, index=o.index)
    ret[L&~S] = (c/up-1)[L&~S]; ret[S&~L] = (1-c/dn)[S&~L]
    ret[L&S] = -(2*k*atr/o)[L&S]
    net = (ret-(L|S).astype(float)*cost).fillna(0.0)
    sh = net.mean()/net.std()*np.sqrt(252)
    print(f"  päevabaar k={k:.2f}: Sharpe {sh:+.2f}  NETO {1e4*net.mean():+.2f}bp/p  "
          f"({len(net)} päeva)")
