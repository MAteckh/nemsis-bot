"""Havimisriski analuus: keskmine tulemus ei utle vaikese konto kohta midagi.
Kordame ajaloolisi tehinguid juhuslikus jarjekorras ja loeme, kui sageli
konto sureb."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S
from config import GRID_CONFIG as G

MK = 0.030; BAL0 = 214.0; RISK = 0.015; MINLOT = 0.01
SIG = {"donchian": S.sig_donchian, "bollinger_fade": S.sig_bollinger_reversion,
       "donchian_trend": S.sig_donchian_trendfiltered, "ts_momentum": S.sig_ts_momentum}
SPREAD = {"XAUUSD": 0.40, "SPX": 0.50, "USDJPY": 0.15, "EURUSD": 0.12}
NOT = {"XAUUSD": lambda l,p: l*100*p, "SPX": lambda l,p: l*100*p,
       "USDJPY": lambda l,p: l*100000, "EURUSD": lambda l,p: l*100000*p}

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

# 1) kogu koik tehingud R-uhikutes (tulemus riskitud summa kordsena)
pool = []
for leg in G["portfolio_legs"]:
    nm = leg["name"]; d = load(nm); rates = R.load_rates(d.index)
    cfg = dict(G); cfg.update(leg.get("params", {})); cfg["risk_pct"]=RISK; cfg["max_positions"]=1
    res = S.simulate(d, SIG[leg["signal"]], cfg, account_balance=BAL0, pip_value=leg["pip_value"])
    for t in res["trades"]:
        risk_amt = abs(t.entry - t.sl) * leg["pip_value"] * t.lot
        if risk_amt <= 0: continue
        days = max(1, (t.closed_at - t.opened_at).days)
        pool.append(dict(sym=nm, r=t.pnl/risk_amt, sl=abs(t.entry-t.sl),
                         pv=leg["pip_value"], px=t.entry, days=days,
                         rate=float(rates.asof(t.opened_at))))
pool = pd.DataFrame(pool)
print(f"Tehinguid kokku: {len(pool)}   keskmine R: {pool.r.mean():+.3f}   "
      f"voidumaar: {100*(pool.r>0).mean():.1f}%")
print(f"R jaotus: 5% {pool.r.quantile(.05):+.2f}  mediaan {pool.r.median():+.2f}  "
      f"95% {pool.r.quantile(.95):+.2f}  parim {pool.r.max():+.2f}\n")

def replay(seq, bal0=BAL0, minlot=MINLOT):
    bal = bal0; peak = bal0; mdd = 0.0
    for _, t in seq.iterrows():
        if bal <= 20: return 0.0, mdd, False      # surnud
        lot = max(minlot, min(round(bal*RISK/(t.sl*t.pv), 3), 0.5))
        risk_amt = t.sl * t.pv * lot
        pnl = t.r * risk_amt
        fin = NOT[t.sym](lot, t.px) * (t.rate + MK) * t.days / 365.0
        bal += pnl - SPREAD[t.sym]*(lot/0.01) - fin
        peak = max(peak, bal); mdd = min(mdd, bal/peak - 1)
    return bal, mdd, True

rng = np.random.default_rng(7)
print("=" * 112)
print(f"MONTE CARLO — 3000 juhuslikku jarjekorda, konto {BAL0:.0f} EUR, 10 aasta jagu tehinguid")
print("=" * 112)
for label, minlot in [("PARIS broker (min lot 0.01)", 0.01),
                      ("hupoteetiline (murdosa-lot lubatud)", 0.0001)]:
    outs, dds, ruin = [], [], 0
    for _ in range(3000):
        seq = pool.sample(frac=1.0, replace=False, random_state=int(rng.integers(1e9)))
        b, dd, alive = replay(seq, minlot=minlot)
        outs.append(b); dds.append(dd)
        if b < BAL0*0.5: ruin += 1
    outs = np.array(outs); dds = np.array(dds)
    print(f"\n  {label}")
    print(f"    mediaan loppsaldo      : {np.median(outs):10.0f} EUR")
    print(f"    5. protsentiil         : {np.percentile(outs,5):10.0f} EUR")
    print(f"    95. protsentiil        : {np.percentile(outs,95):10.0f} EUR")
    print(f"    keskmine max drawdown  : {100*np.mean(dds):9.1f}%")
    print(f"    KONTO KAOTAS >50%      : {100*ruin/len(outs):9.1f}% juhtudest")
    print(f"    konto suri (<20 EUR)   : {100*(outs<=0).mean():9.1f}% juhtudest")

print()
print("=" * 112)
print("SAMA, AGA SUUREMA STARDIKAPITALIGA (min lot 0.01 piirang jaab)")
print("=" * 112)
for b0 in (214, 500, 1000, 2000, 5000):
    outs, ruin = [], 0
    for _ in range(1500):
        seq = pool.sample(frac=1.0, replace=False, random_state=int(rng.integers(1e9)))
        b, dd, alive = replay(seq, bal0=b0)
        outs.append(b/b0)
        if b < b0*0.5: ruin += 1
    outs = np.array(outs)
    print(f"  {b0:5d} EUR  ->  mediaan {np.median(outs):7.2f}x   "
          f"5%-kvantiil {np.percentile(outs,5):6.2f}x   "
          f"kaotas >50%: {100*ruin/len(outs):5.1f}%")
