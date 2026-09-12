"""
SIHITUD PARANDUS — viimane 2 aastat, kaitsemehhanismide hailestamine.

DIAGNOOS (run_grid_windows.py) andis midagi vaga konkreetset:
viimase 2 aasta peal on TP/SL tuum VOIDUS —

    voiduprotsent 65.7%,  vajalik nulli jaamiseks 60.0%   (+5.7)

aga konto sureb ikka (-238 EUR), sest KAITSEMEHHANISMID votavad:

    float_stop    -409 EUR
    trend_reset   -210 EUR
    ------------------------
    kokku         -618 EUR

Ehk probleem EI OLE TP/SL suhtes. Probleem on selles, et kaitse tuleb
liiga tihti peale.

MIKS trend_reset nii tihti tuleb: backtest.py ~324 sulgeb KOIK lahtised
positsioonid turuhinnaga, kui "effective_trend != grid_trend". Trendi
arvutatakse aga ainult trend_period = 10 BAARI pealt — see poordub mura
peale. Pikem aken => vahem valesid poordeid.

MIKS float_stop nii tihti tuleb: max_float = 80 EUR, mis 200 EUR kontol
on 40% holjuvat kahjumit. Mehhanism sulgeb positsiooni keskmiselt
-1.92 EUR juures — ehk ta ei paasta suurest kahjumist, vaid katkestab
positsioone, mis oleksid voinud TP-ni jouda.

Molemad on paris config-nupud (trend_period, max_float), mitte surnud.
"""
import warnings; warnings.filterwarnings("ignore")
import copy, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = "grid_protect_tulemus.txt"

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
D2 = h1[h1.index >= LAST - pd.Timedelta(days=730)]     # viimased 2 aastat
D1 = h1[h1.index >= LAST - pd.Timedelta(days=365)]     # viimane aasta


def run(df, **muuda):
    c = copy.deepcopy(config.GRID_CONFIG)
    c.update(muuda)
    r = BT.simulate_gold_grid(df, grid_cfg=c, account_balance=200.0)
    eq = r["equity"]
    tr = [t for t in r["trades"] if t.closed_at]
    tpn = sum(1 for t in tr if t.reason == "tp")
    sln = sum(1 for t in tr if t.reason == "sl")
    fs = sum(t.pnl for t in tr if t.reason == "float_stop")
    fsn = sum(1 for t in tr if t.reason == "float_stop")
    trs = sum(t.pnl for t in tr if t.reason == "trend_reset")
    trn = sum(1 for t in tr if t.reason == "trend_reset")
    return dict(fin=float(eq.iloc[-1]), low=float(eq.min()), n=len(tr),
                wr=100.0 * tpn / max(tpn + sln, 1), fs=fs, fsn=fsn, trs=trs, trn=trn)


def rida(nimi, df, **muuda):
    r = run(df, **muuda)
    seis = "SUREB" if r["low"] <= 0 else ("<100€" if r["low"] < 100 else "ELAB")
    mark = "  <<< ELAB" if r["low"] >= 100 else ""
    w(f"{nimi:32s} {r['fin']:8.0f}€ {r['low']:8.0f}€ {seis:>7s} {r['n']:5d} "
      f"{r['wr']:6.1f}% {r['fs']:8.0f}€/{r['fsn']:<3d} {r['trs']:7.0f}€/{r['trn']:<3d}{mark}")


for nimi_aken, df in (("VIIMASED 2 AASTAT", D2), ("VIIMANE 1 AASTA", D1)):
    w("")
    w("=" * 104)
    w(f"{nimi_aken}  ({df.index[0].date()} .. {df.index[-1].date()})")
    w("=" * 104)
    w(f"{'variant':32s} {'lõpp':>8s} {'madalaim':>8s} {'seis':>7s} {'teh':>5s} "
      f"{'võit%':>7s} {'float_stop':>12s} {'trend_reset':>11s}")
    w("-" * 104)
    rida("PRAEGUNE (baas)", df)
    w("")
    w("  trend_period — pikem aken = vähem valesid pöördeid:")
    for tp_ in (20, 30, 50, 100):
        rida(f"  trend_period {tp_} (praegu 10)", df, trend_period=tp_)
    w("")
    w("  max_float — float_stop'i lävend:")
    for mf in (30, 150, 300, 100000):
        nimi = "  float_stop VÄLJAS" if mf == 100000 else f"  max_float {mf}€ (praegu 80)"
        rida(nimi, df, max_float=float(mf))
    w("")
    w("  KOMBINATSIOONID:")
    rida("  trend 30 + float VÄLJAS", df, trend_period=30, max_float=100000.0)
    rida("  trend 50 + float VÄLJAS", df, trend_period=50, max_float=100000.0)
    rida("  trend 30 + max_float 300", df, trend_period=30, max_float=300.0)
    rida("  trend 50 + max_float 300", df, trend_period=50, max_float=300.0)
    rida("  trend 100 + float VÄLJAS", df, trend_period=100, max_float=100000.0)
    rida("  trend 50 + float VÄLJAS + ADX", df, trend_period=50,
         max_float=100000.0, adx_filter=True)
w("VALMIS")
