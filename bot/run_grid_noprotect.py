"""
MIS JUHTUB, KUI float_stop JA trend_reset VALJA LULITADA?

Kasutaja kusimus. Diagnoos naitas, et need kaks votsid viimasel
2 aastal kokku -618 EUR, samal ajal kui TP/SL tuum oli VOIDUS
(voiduprotsent 65.7%, vajalik 60.0%).

MATEMAATIKA, mida kaaluda:
  trend_reset keskmine on -12.57 EUR, SL on -45 EUR.
  Lahti jattes kaotavad kaotajad 3.5x rohkem, AGA osa neist muutub
  +30 EUR voitjaks.
  Tasuvuspiir: 30x - 45(1-x) = -12.57  =>  x = 43%
  Ehk kui ule 43% trend_reset'i positsioonidest oleks TP-ni joudnud,
  on valjalulitamine parem. See on empiiriline kusimus.

  float_stop keskmine on -1.92 EUR — ta ei paasta suurest kahjumist,
  vaid katkestab positsioone, mis oleksid voinud TP-ni jouda.
  Tasuvuspiir on seal veel madalam.

Lulitid on nuud paris config-nupud MOLEMAS failis (main_v4.py ja
backtest.py), vaikimisi senine kaitumine:
  max_float          — float_stop'i lavend (suur arv = valjas)
  trend_reset_close  — True = sulge trendipoordel, False = jata lahti
"""
import warnings; warnings.filterwarnings("ignore")
import copy, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = "grid_noprotect_tulemus.txt"

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

AKNAD = [("kogu ajalugu (2.4a)", h1),
         ("viimased 2 aastat", h1[h1.index >= LAST - pd.Timedelta(days=730)]),
         ("viimane 1 aasta", h1[h1.index >= LAST - pd.Timedelta(days=365)])]

VARIANDID = [
    ("PRAEGUNE (mõlemad sees)",      dict()),
    ("float_stop VÄLJAS",            dict(max_float=1e9)),
    ("trend_reset VÄLJAS",           dict(trend_reset_close=False)),
    ("MÕLEMAD VÄLJAS",               dict(max_float=1e9, trend_reset_close=False)),
    ("mõlemad väljas + ADX",         dict(max_float=1e9, trend_reset_close=False,
                                          adx_filter=True)),
    ("mõlemad väljas + trend 20",    dict(max_float=1e9, trend_reset_close=False,
                                          trend_period=20)),
]


def run(df, **muuda):
    c = copy.deepcopy(config.GRID_CONFIG)
    c.update(muuda)
    r = BT.simulate_gold_grid(df, grid_cfg=c, account_balance=200.0)
    eq = r["equity"]
    tr = [t for t in r["trades"] if t.closed_at]
    cnt = {}
    for t in tr:
        cnt[t.reason] = cnt.get(t.reason, 0) + 1
    tpn, sln = cnt.get("tp", 0), cnt.get("sl", 0)
    return dict(fin=float(eq.iloc[-1]), low=float(eq.min()), n=len(tr),
                wr=100.0 * tpn / max(tpn + sln, 1), tpn=tpn, sln=sln,
                fsn=cnt.get("float_stop", 0), trn=cnt.get("trend_reset", 0))


for nimi_aken, df in AKNAD:
    w("")
    w("=" * 96)
    w(f"{nimi_aken}  ({df.index[0].date()} .. {df.index[-1].date()})")
    w("=" * 96)
    w(f"{'variant':30s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} {'teh':>5s} "
      f"{'TP/SL':>9s} {'võit%':>7s} {'fs':>4s} {'tr':>4s}")
    w("-" * 96)
    for nimi, muuda in VARIANDID:
        r = run(df, **muuda)
        seis = "SUREB" if r["low"] <= 0 else ("<100€" if r["low"] < 100 else "ELAB")
        mark = "  <<<" if r["low"] >= 100 else ""
        w(f"{nimi:30s} {r['fin']:8.0f}€ {r['low']:8.0f}€ {seis:>7s} {r['n']:5d} "
          f"{r['tpn']:4d}/{r['sln']:<4d} {r['wr']:6.1f}% {r['fsn']:4d} {r['trn']:4d}{mark}")
w("VALMIS")
