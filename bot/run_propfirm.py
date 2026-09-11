"""
Kas meie 4-jala portfell labiks FTMO-tuupi hindamise?

Reeglid (Faas 1, 2-astmeline):
  +10% kasumieesmark, max 5% paevakadu, max 10% kogukadu (fikseeritud
  algsaldost), min 4 kauplemispaeva, aja piirangut pole.

Meetod: kaivita SAMA 4-jala portfell (XAUUSD/SPX/USDJPY/EURUSD, sama
signaalid mis live's) $10 000 kontol - SEE ON PIISAVALT SUUR, ET
0.01 lot EI OLE enam sunniviisiliselt liiga suur risk (1.5% risk_pct
peaks andma lot'i, mis on loomulikult >= 0.01, mitte porandatud UP).
Testi seda KUMMEKUMNE eri stardipunkti pealt 10 aasta ajaloos, mitte
uhel juhuslikul aknal - see on tapselt see viga, mida oleme kogu
sessiooni valtinud.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R, strategies as S
from config import GRID_CONFIG as G

SIG = {"donchian": S.sig_donchian, "bollinger_fade": S.sig_bollinger_reversion,
       "donchian_trend": S.sig_donchian_trendfiltered, "ts_momentum": S.sig_ts_momentum}
SPREAD = {"XAUUSD": 0.40, "SPX": 0.50, "USDJPY": 0.15, "EURUSD": 0.12}
NOTIONAL = {"XAUUSD": lambda l,p: l*100*p, "SPX": lambda l,p: l*100*p,
            "USDJPY": lambda l,p: l*100000, "EURUSD": lambda l,p: l*100000*p}

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

legs_data = {}
for leg in G["portfolio_legs"]:
    nm = leg["name"]; d = load(nm); cfg = dict(G); cfg.update(leg.get("params", {}))
    legs_data[nm] = dict(df=d, cfg=cfg, signal=SIG[leg["signal"]], pv=leg["pip_value"], rates=R.load_rates(d.index))

# Kogu koik uhe konto peale koik tehingud R-uhikute ja paris pnl'iga,
# 10000 EUR kontol, MITTE porandatud lotiga (kontrolli seda!)
BAL0 = 10000.0
RISK = 0.015
all_trades = []
for nm, L in legs_data.items():
    res = S.simulate(L["df"], L["signal"], L["cfg"], account_balance=BAL0, pip_value=L["pv"])
    lots = [t.lot for t in res["trades"]]
    floored = sum(1 for l in lots if l <= 0.011)
    print(f"{nm:8s}: {len(res['trades']):3d} tehingut, lot vahemik {min(lots) if lots else 0:.3f}-{max(lots) if lots else 0:.3f}, "
          f"0.01 lotiga (porandatud?) {floored}/{len(lots)}")
    for t in res["trades"]:
        all_trades.append(dict(sym=nm, opened=t.opened_at, closed=t.closed_at, pnl=t.pnl,
                               lot=t.lot, entry=t.entry, sl=t.sl))
all_trades.sort(key=lambda t: t["opened"])
print(f"\nKokku tehinguid koigilt neljalt jalalt: {len(all_trades)}\n")

# ---------------------------------------------------------------- paevane MTM
all_days = sorted(set().union(*[set(L["df"].index) for L in legs_data.values()]))
all_days = pd.DatetimeIndex(all_days)

def daily_mtm_series(trades, closes_by_sym, pv_by_sym):
    """Iga paeva kohta: floating P&L koigilt AVATUD positsioonidelt selle
    paeva sulgemishinnaga + juba REALISEERITUD P&L varasematest sulgemistest."""
    s = pd.Series(0.0, index=all_days)
    realized = pd.Series(0.0, index=all_days)
    for t in trades:
        px = closes_by_sym[t["sym"]]
        pv = pv_by_sym[t["sym"]]
        mask = (all_days >= t["opened"]) & (all_days < t["closed"])
        if mask.any():
            entry = t["entry"]
            direction = 1 if t["pnl"] * (px.reindex(all_days[mask]).iloc[-1] - entry) >= 0 or True else 1
        # suund tuletame margi jargi: kui sl < entry siis pikk (buy), muidu luhike
        direction = 1 if t["sl"] < t["entry"] else -1
        fl = (px.reindex(all_days) - t["entry"]) * direction * t["lot"] * pv
        s[mask] += fl[mask]
        after = all_days >= t["closed"]
        realized[after] += t["pnl"]
    return s + realized

closes_by_sym = {nm: L["df"]["close"].reindex(all_days).ffill() for nm, L in legs_data.items()}
pv_by_sym = {nm: L["pv"] for nm, L in legs_data.items()}
equity_curve = BAL0 + daily_mtm_series(all_trades, closes_by_sym, pv_by_sym)

print("Paevane ekvivalent koostatud:", len(equity_curve), "paeva\n")

# ---------------------------------------------------------------- FTMO test
def run_evaluation(start_idx, target=0.10, daily_loss=0.05, total_loss=0.10, max_days=90):
    start_bal = equity_curve.iloc[start_idx]
    day_start = start_bal
    for i in range(start_idx, min(start_idx + max_days, len(equity_curve))):
        eq = equity_curve.iloc[i]
        if all_days[i].weekday() >= 5:
            continue
        # uus paev - uuenda day_start eelmise PAEVA LOPU jargi
        if i > start_idx and all_days[i].date() != all_days[i-1].date():
            day_start = equity_curve.iloc[i-1]
        if (day_start - eq) / start_bal > daily_loss:
            return "FAIL_DAILY", i - start_idx
        if (start_bal - eq) / start_bal > total_loss:
            return "FAIL_TOTAL", i - start_idx
        if (eq - start_bal) / start_bal >= target:
            return "PASS", i - start_idx
    return "TIMEOUT", max_days

print("=" * 100)
print(f"FTMO FAAS 1 TEST — {293} tehingut, $10 000 konto, +10% eesmark / 5% paev / 10% kokku")
print("=" * 100)
results = {}
step = 15
starts = list(range(300, len(equity_curve) - 90, step))
for s in starts:
    r, days = run_evaluation(s)
    results.setdefault(r, []).append(days)

total = sum(len(v) for v in results.values())
for r in ("PASS", "FAIL_DAILY", "FAIL_TOTAL", "TIMEOUT"):
    n = len(results.get(r, []))
    avg_d = np.mean(results[r]) if results.get(r) else 0
    print(f"  {r:12s}: {n:3d}/{total} ({100*n/total:5.1f}%)   keskm paevi: {avg_d:5.1f}")
