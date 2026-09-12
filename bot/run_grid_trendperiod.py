"""
KAS trend_period = 20 ON PLATO VOI TERAV TIPP?

run_grid_protect.py leidis, et trend_period 20 (praegu 10) on ainus
variant, mis viimase 2 aasta peal kunagi miinusesse ei laind:
    trend_period 20  ->  +382 EUR, madalaim +39 EUR, float_stop 0 korda
Aga naabrid on palju halvemad:
    trend_period 30  ->  +153 EUR
    trend_period 50  ->   -21 EUR
See LOHNAB ulesobitamise jarele.

See skript teeb tapselt sama testi, millega ma olen terve sessiooni
kandidaate tapnud:
  1. PEEN SKAALA — kas kuju on plato voi uksik tipp?
  2. OUT-OF-SAMPLE — vaartus valiti viimase 2 aasta pealt; kas ta
     tootab ka VAREMAL perioodil, mida valikul ei kasutatud?
  3. POOLTE-TEST molemal aknal.

Kui 20 on uksik tipp ja varasemal perioodil ebaonnestub, on see
ulesobitamine ja seda EI TOHI live'i panna.
"""
import warnings; warnings.filterwarnings("ignore")
import copy, os
import pandas as pd, numpy as np
import backtest as BT
import config

OUT = "grid_trendperiod_tulemus.txt"

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

D2 = h1[h1.index >= LAST - pd.Timedelta(days=730)]          # valiku aken
VAREM = h1[h1.index < LAST - pd.Timedelta(days=730)]        # OOS: enne seda
KOGU = h1


def run(df, tp_):
    c = copy.deepcopy(config.GRID_CONFIG)
    c["trend_period"] = int(tp_)
    r = BT.simulate_gold_grid(df, grid_cfg=c, account_balance=200.0)
    eq = r["equity"]
    tr = [t for t in r["trades"] if t.closed_at]
    tpn = sum(1 for t in tr if t.reason == "tp")
    sln = sum(1 for t in tr if t.reason == "sl")
    return (float(eq.iloc[-1]), float(eq.min()), len(tr),
            100.0 * tpn / max(tpn + sln, 1))


w(f"andmed {h1.index[0].date()} .. {LAST.date()}   200 EUR konto")
w(f"valiku aken (2a): {D2.index[0].date()} .. {D2.index[-1].date()}  ({len(D2)} baari)")
w(f"OOS (varem):      {VAREM.index[0].date()} .. {VAREM.index[-1].date()}  ({len(VAREM)} baari)")
w("")
w("=" * 92)
w("1) PEEN SKAALA valiku aknal (viimased 2 aastat) — plato või tipp?")
w("=" * 92)
w(f"{'trend_period':>13s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} {'teh':>5s} {'võit%':>7s}")
w("-" * 58)
tulem = {}
for tp_ in (8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 30, 35, 40, 50):
    fin, low, n, wr = run(D2, tp_)
    tulem[tp_] = (fin, low)
    seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
    tahis = "  <<<" if low > 0 else ""
    w(f"{tp_:13d} {fin:8.0f}€ {low:8.0f}€ {seis:>7s} {n:5d} {wr:6.1f}%{tahis}")

pos = [k for k, (f, l) in tulem.items() if l > 0]
kõik = sorted(tulem)
w("")
w(f"   miinusesse EI läinud: {pos if pos else 'mitte ükski'}")
w(f"   suri:                {[k for k in kõik if k not in pos]}")

# PLATO tahendab KORVUTI vaartusi, mitte lihtsalt "mitut". Loeme pikima
# katkematu jada naabrite kaupa. (Esimene versioon luges ainult
# ellujaanute ARVU ja andis seetottu VALE hinnangu "voib olla plato",
# kuigi muster oli 8 ok / 10 surm / 12 surm / 14 ok / 16 surm / 18 ok —
# see on vahelduv, mitte plato.)
pikim = jooksev = 0
for k in kõik:
    jooksev = jooksev + 1 if k in pos else 0
    pikim = max(pikim, jooksev)
w(f"   pikim KÕRVUTI ellujäänute jada: {pikim}")
if pikim <= 2:
    w("   >>> VAHELDUV MUSTER, MITTE PLATO. Ellujäänud on hajutatud ja")
    w("       nende naabrid surevad — see on müra, mitte serv.")
else:
    w("   >>> tõeline plato (3+ kõrvuti) — võib olla päris.")

hullim = min(tulem.items(), key=lambda kv: kv[1][1])
w(f"   hullim väärtus: trend_period {hullim[0]} -> madalaim {hullim[1][1]:.0f}€")

w("")
w("=" * 92)
w("2) OUT-OF-SAMPLE — sama väärtus VAREMAL perioodil (valikul ei kasutatud)")
w("=" * 92)
w(f"{'trend_period':>13s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} {'teh':>5s} {'võit%':>7s}")
w("-" * 58)
for tp_ in (10, 16, 18, 20, 22, 24, 30):
    fin, low, n, wr = run(VAREM, tp_)
    seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
    tahis = "  <<<" if low > 0 else ""
    w(f"{tp_:13d} {fin:8.0f}€ {low:8.0f}€ {seis:>7s} {n:5d} {wr:6.1f}%{tahis}")

w("")
w("=" * 92)
w("3) KOGU AJALUGU (2.4a) — kas väärtus peab vastu tervel perioodil?")
w("=" * 92)
w(f"{'trend_period':>13s} {'lõpp':>9s} {'madalaim':>9s} {'seis':>7s} {'teh':>5s} {'võit%':>7s}")
w("-" * 58)
for tp_ in (10, 16, 18, 20, 22, 24, 30):
    fin, low, n, wr = run(KOGU, tp_)
    seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
    tahis = "  <<<" if low > 0 else ""
    w(f"{tp_:13d} {fin:8.0f}€ {low:8.0f}€ {seis:>7s} {n:5d} {wr:6.1f}%{tahis}")
w("VALMIS")
