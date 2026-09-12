"""
TP/SL suhte test gridil — PARANDATUD VERSIOON.

=== MU VAREM VERSIOON OLI KATKI. Loe seda, enne kui vanu numbreid usud. ===

Vana versioon patchis backtest.py koopiat tekstiasendusega. Originaal on:

    tp = round(price + 30.0 if direction == "buy" else price - 30.0, 2)
    sl = round(price - 45.0 if direction == "buy" else price + 45.0, 2)

Asendusmustrid olid "price + 30.0 if direction", "price - 30.0 if direction",
"price - 45.0 if direction", "price + 45.0 if direction". Aga mustrid
"price - 30.0 if direction" ja "price + 45.0 if direction" EI ESINE
originaalis kunagi — muugipool on kujul "price - 30.0, 2)".

Tulemus: asendus muutis ainult OSTUPOOLE ja jattis muugipoole 30/45 peale.
Koik selle testi numbrid olid seega asummeetrilise TP/SL-iga ja MOTTETUD.
Tuvastasin selle ristkontrolliga: config-nupu tulemused ei klappinud
monkey-patch omadega.

NUUD: grid_tp_usd / grid_sl_usd on config'is ja koodis paris kulges
(main_v4.py grid_tp_sl_dist() + order placement, backtest.py simulaator).
Seega saab suhet testida ausalt, ilma tekstiasenduseta.
"""
import warnings; warnings.filterwarnings("ignore")
import copy, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = "grid_tpsl_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

HERE = os.path.dirname(os.path.abspath(__file__))
h1 = pd.read_csv(os.path.join(HERE, "data", "XAUUSD_h1.csv"),
                 parse_dates=["Date"]).set_index("Date").sort_index()
h1 = h1[~h1.index.duplicated(keep="last")]
h1.columns = [c.strip().lower() for c in h1.columns]
for c in ("open", "high", "low", "close"):
    h1[c] = pd.to_numeric(h1[c], errors="coerce")
h1 = h1.dropna()[["open", "high", "low", "close"]]
mid = len(h1) // 2


def run(tp, sl, df, adx=False, maxfloat=None):
    c = copy.deepcopy(config.GRID_CONFIG)
    c["grid_tp_usd"] = float(tp)
    c["grid_sl_usd"] = float(sl)
    if adx:
        c["adx_filter"] = True
    if maxfloat is not None:
        c["max_float"] = float(maxfloat)
    r = BT.simulate_gold_grid(df, grid_cfg=c, account_balance=200.0)
    eq = r["equity"]
    trades = [t for t in r["trades"] if t.closed_at]
    tp_n = sum(1 for t in trades if t.reason == "tp")
    sl_n = sum(1 for t in trades if t.reason == "sl")
    return (float(eq.iloc[-1]), float(eq.min()), len(trades), tp_n, sl_n)


w(f"andmed {h1.index[0].date()}..{h1.index[-1].date()}  {len(h1)} H1 baari, 200 EUR konto")
w("")
w("Vajalik võiduprotsent nulli jäämiseks = SL / (TP + SL)")
w("")
w(f"{'TP':>5s} {'SL':>5s} {'vaja':>6s} {'saadi':>7s} {'lõpp':>9s} {'madalaim':>9s} "
  f"{'seis':>7s} {'teh':>5s} {'1.pool':>9s} {'2.pool':>9s}")
w("-" * 86)

elus = []
for tp, sl in [(30, 45), (30, 30), (45, 45), (45, 30), (60, 30), (60, 45),
               (60, 60), (90, 45), (90, 60), (120, 60), (120, 45), (150, 60)]:
    need = 100.0 * sl / (tp + sl)
    fin, low, n, tpn, sln = run(tp, sl, h1)
    got = 100.0 * tpn / max(tpn + sln, 1)
    f1 = run(tp, sl, h1.iloc[:mid])[0]
    f2 = run(tp, sl, h1.iloc[mid:])[0]
    seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
    if low > 0:
        elus.append((tp, sl, fin, low, f1, f2))
    w(f"{tp:5d} {sl:5d} {need:5.1f}% {got:6.1f}% {fin:8.0f}€ {low:8.0f}€ "
      f"{seis:>7s} {n:5d} {f1:8.0f}€ {f2:8.0f}€")

w("")
if elus:
    w("ELLU JÄÄNUD variandid + ADX filter ja lõdvem float_stop:")
    w("-" * 86)
    for tp, sl, *_ in elus:
        fin, low, n, tpn, sln = run(tp, sl, h1, adx=True, maxfloat=200.0)
        seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
        w(f"{tp:5d} {sl:5d} {'ADX+200€':>13s} {fin:8.0f}€ {low:8.0f}€ {seis:>7s} {n:5d}")
else:
    w("MITTE ÜKSKI TP/SL suhe ei jäänud ellu.")
w("VALMIS")
