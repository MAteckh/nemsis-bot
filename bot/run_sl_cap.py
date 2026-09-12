"""
KAS 45 EUR STOPP LOHUB XAUUSD STRATEEGIA ARA?

Kasutaja soov: kogu kahjum uhe tehingu kohta max 45 EUR, ja korraga
ainult 1 positsioon.

PROBLEEM, MIDA TESTIDA: praegune strateegia kasutab SL = 2 x ATR.
Praeguse ATR-iga (69.76) on see 139.53 ehk 68% 205 EUR kontost.
45 EUR piir tahendab SL-i $45 kaugusel — kolm korda tihedam.

Tihedam stopp EI OLE tasuta: teda tabatakse palju sagedamini. Kuld
liigub paevas keskmiselt ~70 dollarit (ATR), nii et $45 stopp on
ALLA UHE PAEVA normaalset liikumist. Positsioon voib sulguda mura
peale, enne kui trend uldse alustab.

See skript testib:
  A) praegune SL (2 x ATR)
  B) SL piiratud erinevate EUR-summadega
  C) mitu korda stoppi tabatakse
Ja poolte-test iga variandi kohta.
"""
import warnings; warnings.filterwarnings("ignore")
import os, copy
import pandas as pd, numpy as np
import strategies as S
import gold_logic
import research as R

OUT = "sl_cap_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, "data", "XAUUSD_d.csv"),
                parse_dates=["Date"]).set_index("Date").sort_index()
d = d[~d.index.duplicated(keep="last")]
d.columns = [c.strip().lower() for c in d.columns]
for c in ("open", "high", "low", "close"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna()[["open", "high", "low", "close"]]

PV = 100.0
LOT = 0.01
ACC = 205.01


def sig_capped(cap_eur):
    """Donchian 50, aga SL piiratud nii, et kahjum ei uletaks cap_eur."""
    max_dist = cap_eur / (LOT * PV) if cap_eur else None

    def fn(win, cfg):
        base = S.sig_donchian(win, cfg)
        if base is None:
            return None
        direction, sl_dist, tp_dist = base
        if max_dist is not None and sl_dist > max_dist:
            sl_dist = max_dist
        return direction, sl_dist, tp_dist
    return fn


def aja(df, cap):
    r = S.simulate(df, sig_capped(cap), cfg={"lookback": 50},
                   account_balance=200.0, pip_value=PV)
    tr = [t for t in r["trades"] if t.closed_at]
    if not tr:
        return None
    eq = r["equity"]
    sl_n = sum(1 for t in tr if "sl" in str(t.reason).lower())
    tp_n = sum(1 for t in tr if str(t.reason).lower() == "tp")
    return dict(n=len(tr), pnl=sum(t.pnl for t in tr),
                wr=100.0 * sum(1 for t in tr if t.pnl > 0) / len(tr),
                low=float(eq.min()), fin=float(eq.iloc[-1]),
                dd=100.0 * float((eq / eq.cummax() - 1).min()),
                sl_n=sl_n, tp_n=tp_n,
                halvim=min(t.pnl for t in tr))


atr_nyyd = gold_logic.calc_atr(d.tail(300))
w(f"XAUUSD donchian(50), {d.index[0].date()} .. {d.index[-1].date()}, 200€ konto, lot 0.01")
w(f"praegune ATR(14) = {atr_nyyd:.2f}  =>  praegune SL = 2xATR = {2*atr_nyyd:.2f} "
  f"= {2*atr_nyyd*LOT*PV:.2f}€ = {100*2*atr_nyyd*LOT*PV/ACC:.0f}% kontost")
w("")
w("=" * 104)
w("SL PIIRAMISE MÕJU")
w("=" * 104)
w(f"{'SL piir':>12s} {'$ kaugus':>9s} {'% kontost':>10s} {'teh':>5s} {'P&L':>10s} "
  f"{'võit%':>7s} {'SL/TP':>9s} {'madalaim':>9s} {'maxDD':>8s} {'halvim teh':>11s}")
w("-" * 104)
for cap in (None, 100, 80, 60, 45, 30, 20):
    r = aja(d, cap)
    if r is None:
        continue
    if cap is None:
        lbl, dist, pct = "2xATR (praegu)", 2 * atr_nyyd, 100 * 2 * atr_nyyd * LOT * PV / ACC
    else:
        lbl, dist, pct = f"{cap}€", cap / (LOT * PV), 100 * cap / ACC
    w(f"{lbl:>12s} {dist:8.1f}$ {pct:9.0f}% {r['n']:5d} {r['pnl']:+9.2f}€ "
      f"{r['wr']:6.1f}% {r['sl_n']:4d}/{r['tp_n']:<4d} {r['low']:8.2f}€ "
      f"{r['dd']:7.0f}% {r['halvim']:+10.2f}€")

w("")
w("=" * 104)
w("POOLTE-TEST")
w("=" * 104)
m = len(d) // 2
w(f"{'SL piir':>12s} {'1. pool P&L':>13s} {'2. pool P&L':>13s} {'mõlemad +?':>12s} "
  f"{'1.p madalaim':>14s} {'2.p madalaim':>14s}")
w("-" * 82)
for cap in (None, 100, 60, 45, 30):
    a, b = aja(d.iloc[:m], cap), aja(d.iloc[m:], cap)
    if a is None or b is None:
        continue
    lbl = "2xATR" if cap is None else f"{cap}€"
    ok = "JAH" if (a["pnl"] > 0 and b["pnl"] > 0) else "ei"
    w(f"{lbl:>12s} {a['pnl']:+12.2f}€ {b['pnl']:+12.2f}€ {ok:>12s} "
      f"{a['low']:13.2f}€ {b['low']:13.2f}€")
w("VALMIS")
