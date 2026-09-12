"""
TESTI TAPSELT NEID SEADEID, MIS ON CONFIGIS — enne esmaspaeva.

Kasutaja: "EUR ja USD olid kahjulikud ju selle strateegiaga."
Tal on oigus, et ma leidsin need norgaks. AGA ma testisin TEISI
parameetreid kui need, mis configis on:

  testisin varem       configis on
  ----------------------------------------------------------
  EURUSD ts_momentum_120   EURUSD ts_momentum mom_lookback=60
  USDJPY donchian_50       USDJPY donchian_trend lookback=20, ema_trend=200

Neid TAPSEID seadeid pole ma kunagi testinud. Teen seda nuud, sama
mootoriga (strategies.simulate), mida live-bot signaalide jaoks kasutab.

ANDMEKVALITEEDI MARKUS: FX paevabaaride Open on katki (Open == Close),
aga High/Low on korras (53-57bp mediaan vahemik). Signaalid kasutavad
Close'i ja ATR-i (High/Low pealt) — molemad toimivad. Mu varasem
jareldus "FX paevabaarid on katki" oli liiga lai.
"""
import warnings; warnings.filterwarnings("ignore")
import os, copy
import pandas as pd, numpy as np
import strategies as S
import config
import research as R

OUT = "legs_exact_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

G = config.GRID_CONFIG

FN = {
    "donchian":       S.sig_donchian,
    "donchian_trend": S.sig_donchian_trendfiltered,
    "bollinger_fade": S.sig_bollinger_reversion,
    "ts_momentum":    S.sig_ts_momentum,
    "ema_cross":      S.sig_ema_cross,
}


def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"),
                    parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()[["open", "high", "low", "close"]]


def aja(df, fn, cfg, pv):
    r = S.simulate(df, fn, cfg=cfg, account_balance=200.0, pip_value=pv)
    eq = r["equity"] if "equity" in r else r.get("equity_curve")
    tr = [t for t in r["trades"] if t.closed_at]
    if not tr:
        return None
    pnl = sum(t.pnl for t in tr)
    voit = sum(1 for t in tr if t.pnl > 0)
    low = float(eq.min()) if eq is not None else np.nan
    return dict(n=len(tr), pnl=pnl, wr=100.0 * voit / len(tr),
                fin=float(eq.iloc[-1]) if eq is not None else np.nan, low=low)


w("=" * 96)
w("PORTFELLI JALAD — TÄPSELT CONFIGI SEADETEGA, 200€ konto")
w("=" * 96)
w(f"{'jalg':8s} {'signaal':16s} {'params':28s} {'teh':>5s} {'P&L':>9s} "
  f"{'võit%':>7s} {'lõpp':>9s} {'madalaim':>9s}")
w("-" * 96)

kokku = []
for leg in G["portfolio_legs"]:
    nimi, sig = leg["name"], leg["signal"]
    pars = dict(leg.get("params", {}))
    pv = float(leg.get("pip_value", 100.0))
    fn = FN.get(sig)
    if fn is None:
        w(f"{nimi:8s} tundmatu signaal {sig}")
        continue
    df = load(nimi)
    r = aja(df, fn, copy.deepcopy(pars), pv)
    if r is None:
        w(f"{nimi:8s} {sig:16s} {str(pars):28s}  (ühtegi tehingut ei tekkinud)")
        continue
    kokku.append((nimi, r))
    w(f"{nimi:8s} {sig:16s} {str(pars):28s} {r['n']:5d} {r['pnl']:+8.2f}€ "
      f"{r['wr']:6.1f}% {r['fin']:8.2f}€ {r['low']:8.2f}€")

w("")
w("=" * 96)
w("POOLTE-TEST — kas tulemus püsib?")
w("=" * 96)
w(f"{'jalg':8s} {'1. pool P&L':>13s} {'2. pool P&L':>13s} {'mõlemad +?':>12s}")
w("-" * 50)
for leg in G["portfolio_legs"]:
    nimi, sig = leg["name"], leg["signal"]
    pars = dict(leg.get("params", {}))
    pv = float(leg.get("pip_value", 100.0))
    fn = FN.get(sig)
    if fn is None:
        continue
    df = load(nimi)
    m = len(df) // 2
    a = aja(df.iloc[:m], fn, copy.deepcopy(pars), pv)
    b = aja(df.iloc[m:], fn, copy.deepcopy(pars), pv)
    if a is None or b is None:
        w(f"{nimi:8s}  (liiga vähe tehinguid ühel poolel)")
        continue
    ok = "JAH" if (a["pnl"] > 0 and b["pnl"] > 0) else "ei"
    w(f"{nimi:8s} {a['pnl']:+12.2f}€ {b['pnl']:+12.2f}€ {ok:>12s}")

w("")
w("=" * 96)
w("VÕRDLUS: OSTA-JA-HOIA sama perioodil")
w("=" * 96)
w(f"{'jalg':8s} {'strateegia P&L':>16s} {'osta-ja-hoia':>14s} {'kas lööb?':>11s}")
w("-" * 54)
for nimi, r in kokku:
    df = load(nimi)
    leg = [l for l in G["portfolio_legs"] if l["name"] == nimi][0]
    pv = float(leg.get("pip_value", 100.0))
    bh = S.buy_and_hold(df, account_balance=200.0, pip_value=pv, lot=0.01)
    bhp = bh["pnl"] if isinstance(bh, dict) and "pnl" in bh else float("nan")
    ok = "JAH" if r["pnl"] > bhp else "ei"
    w(f"{nimi:8s} {r['pnl']:+15.2f}€ {bhp:+13.2f}€ {ok:>11s}")
w("VALMIS")
