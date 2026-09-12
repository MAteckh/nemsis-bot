"""
OTSUSTAV TEST: kas parem TP/SL suhe paastab gridi?

LEID: gridi TP/SL EI TULE configist. Nad on koodi sisse kirjutatud —
backtest.py real ~242-243 ja main_v4.py-s antakse send_grid_signals()'ile
literaalid 30.0 ja 45.0:

    tp = price + 30.0     # TP  $30
    sl = price - 45.0     # SL  $45

Seetottu ei muutnud tp_min / tp_max / sl_max seadmine MITTE MIDAGI —
need on surnud nupud (config'is olemas, grid ei loe neid).
Sama lugu risk_based_lot'iga: grid kasutab get_compound_lot()'i,
mitte get_risk_based_lot()'i.

TP $30 / SL $45 tahendab, et vajad 60% voiduprotsenti lihtsalt NULLI
jaamiseks. Ajaloos tuli 62.6% (72 TP vs 43 SL) — habemenoa peal.

MEETOD: originaalfaili EI PUUDUTATA. Loeme backtest.py teksti, teeme
mallutud koopia ajutisse kausta ja impordime selle eraldi moodulina.
Nii ei saa katkestus jatta backtest.py-d katkiseks.
"""
import warnings; warnings.filterwarnings("ignore")
import os, sys, copy, tempfile, importlib.util, shutil
import pandas as pd, numpy as np
import config

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "backtest.py")
OUT = "grid_tpsl_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

orig = open(SRC, encoding="utf-8").read()
assert "price + 30.0 if direction" in orig, "TP muster ei leidnud — kood on muutunud!"
assert "price - 45.0 if direction" in orig, "SL muster ei leidnud — kood on muutunud!"

h1 = pd.read_csv(os.path.join(HERE, "data", "XAUUSD_h1.csv"),
                 parse_dates=["Date"]).set_index("Date").sort_index()
h1 = h1[~h1.index.duplicated(keep="last")]
h1.columns = [c.strip().lower() for c in h1.columns]
for c in ("open", "high", "low", "close"):
    h1[c] = pd.to_numeric(h1[c], errors="coerce")
h1 = h1.dropna()[["open", "high", "low", "close"]]

TMP = tempfile.mkdtemp(prefix="gridtpsl_")
sys.path.insert(0, HERE)          # et patched moodul leiaks gold_logic, config

_n = 0
def load_patched(tp, sl):
    """Tee backtest.py-st TP/SL-mallitud koopia ja impordi eraldi moodulina."""
    global _n
    _n += 1
    mod_src = (orig
        .replace("price + 30.0 if direction", f"price + {float(tp)} if direction")
        .replace("price - 30.0 if direction", f"price - {float(tp)} if direction")
        .replace("price - 45.0 if direction", f"price - {float(sl)} if direction")
        .replace("price + 45.0 if direction", f"price + {float(sl)} if direction"))
    path = os.path.join(TMP, f"bt_{_n}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(mod_src)
    spec = importlib.util.spec_from_file_location(f"bt_{_n}", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def run_with(tp, sl, adx=False, maxfloat=None):
    m = load_patched(tp, sl)
    cfg = copy.deepcopy(config.GRID_CONFIG)
    if adx:
        cfg["adx_filter"] = True
    if maxfloat is not None:
        cfg["max_float"] = float(maxfloat)
    r = m.simulate_gold_grid(h1, grid_cfg=cfg, account_balance=200.0)
    eq = r["equity"]
    n = len([t for t in r["trades"] if t.closed_at])
    return float(eq.iloc[-1]), float(eq.min()), n

try:
    w(f"andmed {h1.index[0].date()}..{h1.index[-1].date()}  {len(h1)} H1 baari, 200 EUR konto")
    w("")
    w("Vajalik võiduprotsent nulli jäämiseks = SL / (TP + SL)")
    w("")
    w(f"{'TP':>5s} {'SL':>5s} {'suhe':>6s} {'vaja võite':>11s} {'lõpp':>9s} "
      f"{'madalaim':>9s} {'seis':>7s} {'teh':>5s}")
    w("-" * 72)
    for tp, sl in [(30, 45), (30, 30), (45, 45), (45, 30), (60, 30),
                   (60, 45), (60, 60), (90, 45), (90, 60), (120, 60)]:
        need = 100.0 * sl / (tp + sl)
        fin, low, n = run_with(tp, sl)
        seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
        mark = "  <<<" if low > 0 else ""
        w(f"{tp:5d} {sl:5d} {tp/sl:6.2f} {need:10.1f}% {fin:8.0f}€ {low:8.0f}€ "
          f"{seis:>7s} {n:5d}{mark}")

    w("")
    w("PARIMAD SUHTED + ADX trendifilter + lõdvem float_stop (200€):")
    w("-" * 72)
    for tp, sl in [(45, 30), (60, 30), (60, 45), (90, 45)]:
        fin, low, n = run_with(tp, sl, adx=True, maxfloat=200.0)
        seis = "SUREB" if low <= 0 else ("<100€" if low < 100 else "ELAB")
        mark = "  <<<" if low > 0 else ""
        w(f"{tp:5d} {sl:5d} {tp/sl:6.2f} {'ADX+200€':>11s} {fin:8.0f}€ {low:8.0f}€ "
          f"{seis:>7s} {n:5d}{mark}")
finally:
    shutil.rmtree(TMP, ignore_errors=True)
    # kinnitus, et originaali ei puutunud
    same = open(SRC, encoding="utf-8").read() == orig
    w("")
    w(f"backtest.py puutumata: {'JAH' if same else 'EI — KONTROLLI!'}")
    w("VALMIS")
