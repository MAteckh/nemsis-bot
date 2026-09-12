"""
KUIDAS VALTIDA GRIDI SUURT KAHJUMIT? — parandusevariantide test.

DIAGNOOS (run_grid_truth.py + tehingute lahtivotmine) naitas midagi
OOTAMATUT: hiiglaslikku uksikkahjumit EI OLNUDKI.

  halvim uksik tehing: -45.00 EUR (SL)
  halvim paev:        -135.00 EUR (3 tehingut)
  max positsioone korraga: 3  (kuigi config lubab levels=8)

Sulgemiste jaotus (289 tehingut, kokku -444.40 EUR):
  tp            72 tehingut  +2160.00 EUR   (keskm +30.00)
  sl            43 tehingut  -1935.00 EUR   (keskm -45.00)
  trend_reset   31 tehingut   -389.80 EUR   (keskm -12.57)
  float_stop   141 tehingut   -271.20 EUR   (keskm  -1.92)
  weekend        2 tehingut     -8.40 EUR

Ehk konto ei surnud UHE suure kahjumi katte, vaid:
  1. TP/SL suhe on vale: TP +30, SL -45. Vajad 60% voiduprotsenti
     lihtsalt nulli jaamiseks.
  2. Kaitsemehhanismid ise verevad: float_stop sulges 141 korda ja
     trend_reset 31 korda, kokku -661 EUR. Kaitse toimib (suurt
     kahjumit ei tule), aga ta tuleb nii tihti peale, et soob konto.

See skript testib parandusi uksikult ja kombinatsioonides.
"""
import warnings; warnings.filterwarnings("ignore")
import copy, time, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = os.environ.get("GRIDFIX_OUT", "grid_fixes_tulemus.txt")

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

h1 = pd.read_csv("data/XAUUSD_h1.csv", parse_dates=["Date"]).set_index("Date").sort_index()
h1 = h1[~h1.index.duplicated(keep="last")]
h1.columns = [c.strip().lower() for c in h1.columns]
for c in ("open", "high", "low", "close"):
    h1[c] = pd.to_numeric(h1[c], errors="coerce")
h1 = h1.dropna()[["open", "high", "low", "close"]]
BASE = copy.deepcopy(config.GRID_CONFIG)

w(f"andmed {h1.index[0].date()}..{h1.index[-1].date()}  {len(h1)} H1 baari, 200 EUR konto")
w("")
w(f"{'variant':34s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} {'teh':>5s} {'maxDD':>7s}")
w("-" * 78)


def show(nimi, cfg):
    t0 = time.time()
    r = BT.simulate_gold_grid(h1, grid_cfg=copy.deepcopy(cfg), account_balance=200.0)
    eq = r["equity"]
    n = len([t for t in r["trades"] if t.closed_at])
    fin, low = float(eq.iloc[-1]), float(eq.min())
    dd = float((eq / eq.cummax() - 1).min())
    seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
    w(f"{nimi:34s} {fin:8.0f}€ {low:8.0f}€ {seis:>7s} {n:5d} {100*dd:6.0f}%  ({time.time()-t0:.0f}s)")


show("PRAEGUNE (baas)", BASE)
for nimi, muuda in [
    ("+ ADX trendifilter sisse",   {"adx_filter": True}),
    ("+ risk_based_lot sisse",     {"risk_based_lot": True}),
    ("+ float_stop VÄLJAS",        {"max_float": 100000.0}),
    ("+ max_float 40€",            {"max_float": 40.0}),
    ("+ max_float 200€",           {"max_float": 200.0}),
    ("+ TP min 45$ (praegu 30)",   {"tp_min": 45.0, "tp_max": 120.0}),
    ("+ TP min 60$",               {"tp_min": 60.0, "tp_max": 150.0}),
    ("+ TP min 90$",               {"tp_min": 90.0, "tp_max": 200.0}),
    ("+ SL max 30$ (praegu 80)",   {"sl_max": 30.0}),
    ("+ SL max 50$",               {"sl_max": 50.0}),
    ("+ levels 1 (praegu 8)",      {"levels": 1}),
    ("+ levels 3",                 {"levels": 3}),
    ("ADX + TP60",                 {"adx_filter": True, "tp_min": 60.0, "tp_max": 150.0}),
    ("ADX + TP60 + float VÄLJAS",  {"adx_filter": True, "tp_min": 60.0, "tp_max": 150.0,
                                    "max_float": 100000.0}),
    ("TP60 + float VÄLJAS",        {"tp_min": 60.0, "tp_max": 150.0, "max_float": 100000.0}),
    ("ADX + TP60 + risk_lot",      {"adx_filter": True, "tp_min": 60.0, "tp_max": 150.0,
                                    "risk_based_lot": True}),
]:
    c = copy.deepcopy(BASE)
    c.update(muuda)
    show(nimi, c)
w("VALMIS")
