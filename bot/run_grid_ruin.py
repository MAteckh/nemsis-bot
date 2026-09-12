"""
MILLAL IGA VARIANT PARISELT SUREB?

Probleem koigi senise grid-arvudega: backtest.simulate_gold_grid ei
peata simulatsiooni, kui konto tuhjaks saab. Ta kaupleb miinuses
kontoga edasi. Koik, mis juhtub parast surma, on VALJAMOELDIS —
paris broker oleks konto sulgenud.

Lisaks: kui balance <= 0, siis max_float = 0 ja float_stop sulgeb iga
kaotava positsiooni, olenemata seadest. Seetottu naitasid ka
"float_stop VALJAS" testid float_stop'i kaivitumas.

See skript ei muuda simulaatorit. Ta loeb equity-kurvi ja utleb, MILLAL
konto esimest korda:
  alla 100 EUR  — miinimum-lot 0.01 ei mahu enam plaanikohase riski sisse
  alla 0 EUR    — konto on fuusiliselt otsas

Ainus aus kusimus on: KAS KONTO JOUAB SURMANI, ja kui kiiresti.
"""
import warnings; warnings.filterwarnings("ignore")
import copy, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = "grid_ruin_tulemus.txt"

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

AKNAD = [("kogu 2.4a", h1),
         ("viim 2a", h1[h1.index >= LAST - pd.Timedelta(days=730)]),
         ("viim 1a", h1[h1.index >= LAST - pd.Timedelta(days=365)])]

VARIANDID = [
    ("PRAEGUNE (mõlemad sees)",   dict()),
    ("float_stop VÄLJAS",         dict(max_float=1e9)),
    ("trend_reset VÄLJAS",        dict(trend_reset_close=False)),
    ("MÕLEMAD VÄLJAS",            dict(max_float=1e9, trend_reset_close=False)),
    ("mõlemad väljas + ADX",      dict(max_float=1e9, trend_reset_close=False,
                                       adx_filter=True)),
    ("mõlemad väljas + trend 20", dict(max_float=1e9, trend_reset_close=False,
                                       trend_period=20)),
]


def analyse(df, **muuda):
    c = copy.deepcopy(config.GRID_CONFIG)
    c.update(muuda)
    r = BT.simulate_gold_grid(df, grid_cfg=c, account_balance=200.0)
    eq = r["equity"]
    algus = eq.index[0]
    a100 = eq[eq < 100]
    a0 = eq[eq <= 0]
    d100 = (a100.index[0] - algus).days if len(a100) else None
    d0 = (a0.index[0] - algus).days if len(a0) else None
    # tootlus kuni surmani (voi lopuni)
    lopp_idx = a0.index[0] if len(a0) else eq.index[-1]
    enne = eq[eq.index <= lopp_idx]
    return dict(d100=d100, d0=d0, tipp=float(eq.cummax().max()),
                enne_lopp=float(enne.iloc[-1]), paevi=(lopp_idx - algus).days,
                lopp=float(eq.iloc[-1]))


for nimi_aken, df in AKNAD:
    w("")
    w("=" * 98)
    w(f"{nimi_aken}   ({df.index[0].date()} .. {df.index[-1].date()},"
      f" {(df.index[-1]-df.index[0]).days} päeva)")
    w("=" * 98)
    w(f"{'variant':30s} {'alla 100€':>12s} {'alla 0€':>12s} {'tipp':>9s} "
      f"{'seis surma hetkel':>19s}")
    w("-" * 98)
    for nimi, muuda in VARIANDID:
        r = analyse(df, **muuda)
        s100 = f"{r['d100']} p pärast" if r["d100"] is not None else "ei langenud"
        s0 = f"{r['d0']} p pärast" if r["d0"] is not None else "EI SURNUD"
        w(f"{nimi:30s} {s100:>12s} {s0:>12s} {r['tipp']:8.0f}€ "
          f"{r['enne_lopp']:18.0f}€")
w("")
w("Loe nii: 'alla 0€ = 120 p pärast' tähendab, et konto oli 120 päevaga otsas")
w("ja kõik selle backtesti numbrid pärast seda päeva on väljamõeldis.")
w("VALMIS")
