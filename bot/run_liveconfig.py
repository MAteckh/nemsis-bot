"""Kas LIVE'is jooksev konfiguratsioon elab ule oise finantseerimise?"""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S
from config import GRID_CONFIG as G

MK = 0.030
# notsionaal USD-s uhe loti kohta (0.01 lot = miinimum)
NOTIONAL = {   # kordaja: notsionaal = lot * kordaja * hind  (v.a USDJPY: baasvaluuta USD)
    "XAUUSD": lambda lot, px: lot * 100 * px,
    "SPX":    lambda lot, px: lot * 100 * px,
    "USDJPY": lambda lot, px: lot * 100000,
    "EURUSD": lambda lot, px: lot * 100000 * px,
}
SIG = {"donchian": S.sig_donchian, "bollinger_fade": S.sig_bollinger_reversion,
       "donchian_trend": S.sig_donchian_trendfiltered, "ts_momentum": S.sig_ts_momentum}
SPREAD_EUR_PER_001 = {"XAUUSD": 0.40, "SPX": 0.50, "USDJPY": 0.15, "EURUSD": 0.12}

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

BAL = 214.0
print("=" * 122)
print(f"LIVE-KONFIGURATSIOON, jalg jala haaval — konto {BAL:.0f} EUR, 10 aastat paevabaare")
print("=" * 122)
print(f"{'jalg':10s} {'signaal':16s} {'tehinguid':>10s} {'voit%':>7s} "
      f"{'BRUTO EUR':>10s} {'spread':>9s} {'FINANTS':>9s} {'NETO EUR':>10s} {'kesk paevi':>11s}")
print("-" * 122)

tot_gross = tot_sp = tot_fin = 0.0
for leg in G["portfolio_legs"]:
    nm = leg["name"]
    d = load(nm)
    rates = R.load_rates(d.index)
    cfg = dict(G); cfg.update(leg.get("params", {}))
    cfg["risk_pct"] = 0.015; cfg["max_positions"] = 1
    res = S.simulate(d, SIG[leg["signal"]], cfg, account_balance=BAL, pip_value=leg["pip_value"])
    tr = res["trades"]
    if not tr:
        print(f"{nm:10s} {leg['signal']:16s} {'0':>10s}"); continue
    gross = sum(t.pnl for t in tr)
    sp = sum(SPREAD_EUR_PER_001[nm] * (t.lot / 0.01) for t in tr)
    fin = 0.0; days = []
    for t in tr:
        dd = max(1, (t.closed_at - t.opened_at).days)
        days.append(dd)
        notion = NOTIONAL[nm](t.lot, t.entry)
        rr = float(rates.asof(t.opened_at))
        fin += notion * (rr + MK) * dd / 365.0
    net = gross - sp - fin
    wins = sum(1 for t in tr if t.pnl > 0)
    tot_gross += gross; tot_sp += sp; tot_fin += fin
    print(f"{nm:10s} {leg['signal']:16s} {len(tr):10d} {100*wins/len(tr):6.1f}% "
          f"{gross:+10.2f} {-sp:+9.2f} {-fin:+9.2f} {net:+10.2f} {np.mean(days):10.1f}")

print("-" * 122)
net_all = tot_gross - tot_sp - tot_fin
print(f"{'KOKKU':10s} {'':16s} {'':>10s} {'':>7s} {tot_gross:+10.2f} {-tot_sp:+9.2f} "
      f"{-tot_fin:+9.2f} {net_all:+10.2f}")
print()
print(f"  Backtest ILMA finantseerimiseta : {tot_gross - tot_sp:+8.2f} EUR  "
      f"({100*(tot_gross-tot_sp)/BAL:+.1f}% / 10a)")
print(f"  Backtest KOOS finantseerimisega : {net_all:+8.2f} EUR  ({100*net_all/BAL:+.1f}% / 10a)")
print(f"  Finantseerimise mojo            : {-tot_fin:+8.2f} EUR")
