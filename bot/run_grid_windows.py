"""
GRID ERINEVATEL AJAAKNADEL — kasutaja soov: "testi viimase 2 aasta peale".

H1-andmeid on kokku 2024-04-19 .. 2026-09-11 (2.4 aastat), seega
"viimased 2 aastat" = 2024-09-11 edasi. Jooksutame mitut akent, et
naha, KUS serv kadus.

TP/SL tuleb nuud config'ist (grid_tp_usd / grid_sl_usd), seega saab
korraga vorrelda praegust 30/45 ja parima servaga 60/45.
"""
import warnings; warnings.filterwarnings("ignore")
import copy, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = "grid_windows_tulemus.txt"

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
LAST = h1.index[-1]


def run(tp, sl, df):
    c = copy.deepcopy(config.GRID_CONFIG)
    c["grid_tp_usd"] = float(tp)
    c["grid_sl_usd"] = float(sl)
    r = BT.simulate_gold_grid(df, grid_cfg=c, account_balance=200.0)
    eq = r["equity"]
    tr = [t for t in r["trades"] if t.closed_at]
    tpn = sum(1 for t in tr if t.reason == "tp")
    sln = sum(1 for t in tr if t.reason == "sl")
    fs = sum(t.pnl for t in tr if t.reason == "float_stop")
    trs = sum(t.pnl for t in tr if t.reason == "trend_reset")
    return dict(fin=float(eq.iloc[-1]), low=float(eq.min()), n=len(tr),
                tpn=tpn, sln=sln, fs=fs, trs=trs)


AKNAD = [("kogu ajalugu (2.4a)", None), ("viimased 2 aastat", 730),
         ("viimased 18 kuud", 548), ("viimane 1 aasta", 365),
         ("viimased 6 kuud", 183), ("viimased 3 kuud", 91)]

w(f"andmed {h1.index[0].date()} .. {LAST.date()}   200 EUR konto")
for tp, sl in ((30, 45), (60, 45)):
    w("")
    w("=" * 88)
    w(f"TP {tp}$ / SL {sl}$" + ("   (PRAEGUNE seade)" if (tp, sl) == (30, 45)
                                else "   (parima servaga seade)"))
    w("=" * 88)
    w(f"{'aken':22s} {'algus':>11s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} "
      f"{'teh':>5s} {'TP/SL':>9s} {'võit%':>7s}")
    w("-" * 88)
    for nimi, paevi in AKNAD:
        df = h1 if paevi is None else h1[h1.index >= LAST - pd.Timedelta(days=paevi)]
        if len(df) < 200:
            continue
        r = run(tp, sl, df)
        seis = "SUREB" if r["low"] <= 0 else ("<100€" if r["low"] < 100 else "ELAB")
        wr = 100.0 * r["tpn"] / max(r["tpn"] + r["sln"], 1)
        w(f"{nimi:22s} {str(df.index[0].date()):>11s} {r['fin']:8.0f}€ "
          f"{r['low']:8.0f}€ {seis:>7s} {r['n']:5d} {r['tpn']:4d}/{r['sln']:<4d} {wr:6.1f}%")

w("")
w("=" * 88)
w("KUS KAITSEMEHHANISMID RAHA VÕTSID (TP 30 / SL 45)")
w("=" * 88)
w(f"{'aken':22s} {'float_stop':>12s} {'trend_reset':>13s} {'kokku':>10s}")
w("-" * 60)
for nimi, paevi in AKNAD:
    df = h1 if paevi is None else h1[h1.index >= LAST - pd.Timedelta(days=paevi)]
    if len(df) < 200:
        continue
    r = run(30, 45, df)
    w(f"{nimi:22s} {r['fs']:11.0f}€ {r['trs']:12.0f}€ {r['fs']+r['trs']:9.0f}€")

w("")
w("=" * 88)
w("AASTATE KAUPA (TP 30 / SL 45) — iga aasta eraldi, 200€ algkontoga")
w("=" * 88)
w(f"{'periood':22s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} {'teh':>5s} {'võit%':>7s}")
w("-" * 66)
for algus, lopp, nimi in [("2024-04-19", "2025-04-19", "aasta 1"),
                          ("2025-04-19", "2026-04-19", "aasta 2"),
                          ("2026-04-19", "2026-09-11", "2026 apr-sept")]:
    df = h1[(h1.index >= algus) & (h1.index < lopp)]
    if len(df) < 200:
        continue
    r = run(30, 45, df)
    seis = "SUREB" if r["low"] <= 0 else ("<100€" if r["low"] < 100 else "ELAB")
    wr = 100.0 * r["tpn"] / max(r["tpn"] + r["sln"], 1)
    w(f"{nimi+' ('+algus[:7]+')':22s} {r['fin']:8.0f}€ {r['low']:8.0f}€ "
      f"{seis:>7s} {r['n']:5d} {wr:6.1f}%")
w("VALMIS")
