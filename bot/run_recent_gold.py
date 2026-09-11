import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S
from config import GRID_CONFIG as G

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns = [c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

df = load("XAUUSD")
print(f"Andmed: {df.index[0].date()} .. {df.index[-1].date()}  ({len(df)} päevabaari)\n")

print("=" * 100)
print("A) VOLATIILSUS — viimased perioodid vs 10a keskmine (päevane tootlus, annualiseeritud)")
print("=" * 100)
ret = df["close"].pct_change()
windows = [("Viimased 30 päeva", 30), ("Viimased 90 päeva", 90), ("Viimased 180 päeva", 180),
           ("Viimane 1 aasta", 252), ("Kõik 10 aastat", len(df))]
for lbl, n in windows:
    r = ret.iloc[-n:]
    vol_ann = r.std() * np.sqrt(252) * 100
    move = df["close"].iloc[-1] - df["close"].iloc[max(0, len(df)-n)]
    print(f"  {lbl:22s}  annualiseeritud vol {vol_ann:5.1f}%   "
          f"perioodi hinnaliikumine {move:+7.1f}$   "
          f"(${df['close'].iloc[max(0,len(df)-n)]:.0f} -> ${df['close'].iloc[-1]:.0f})")

print()
print("=" * 100)
print("B) PÄRIS XAUUSD PORTFELLIJALG (Donchian-50, 0.01 fikseeritud lot, pip_value=100)")
print("   Sama signaal, mis live'is jookseb — mitte idealiseeritud riskiga, PÄRIS sunnitud lotiga.")
print("=" * 100)
cfg = dict(G); cfg.update({"lookback": 50, "risk_pct": 0.015, "max_positions": 1, "min_history": 210})

# Jooksuta koik 10 aastat, aga vaata tulemust ka LOIKUDES
res_full = S.simulate(df, S.sig_donchian, cfg, account_balance=214.0, pip_value=100.0)
trades = res_full["trades"]
print(f"  Kokku tehinguid 10 aastas: {len(trades)}\n")

# Segmenteeri tehingud perioodide kaupa (viimased N paeva) opening_at pohjal
now_ts = df.index[-1]
for lbl, days in [("Viimased 30 päeva", 30), ("Viimased 90 päeva", 90),
                  ("Viimased 180 päeva", 180), ("Viimane 1 aasta", 365)]:
    cutoff = now_ts - pd.Timedelta(days=days)
    seg = [t for t in trades if t.opened_at >= cutoff]
    if not seg:
        print(f"  {lbl:22s}  0 tehingut selles aknas")
        continue
    wins = [t for t in seg if t.pnl > 0]
    net = sum(t.pnl for t in seg)
    avg_days = np.mean([(t.closed_at - t.opened_at).days for t in seg])
    print(f"  {lbl:22s}  {len(seg):2d} tehingut  võit {100*len(wins)/len(seg):4.0f}%  "
          f"netokokku {net:+7.2f}$ (0.01 lot)  keskmine hoiuaeg {avg_days:4.1f}p")

print()
print("  ÜKSIKUD TEHINGUD viimase 180 päeva jooksul (see NÄITAB volatiilsuse mõju otse):")
cutoff = now_ts - pd.Timedelta(days=180)
for t in trades:
    if t.opened_at >= cutoff:
        days = (t.closed_at - t.opened_at).days
        print(f"    {t.opened_at.date()} {t.direction:4s} @ {t.entry:8.2f}  ->  "
              f"{t.closed_at.date()} @ {(t.tp if t.pnl>0 else t.sl):8.2f}  "
              f"{t.reason:12s}  {t.pnl:+7.2f}$  ({days}p)")
