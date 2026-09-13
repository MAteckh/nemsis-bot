"""
MONTE CARLO + RISK OF RUIN + POSITION SIZING 205 EUR KONTOLE.
(kasutaja punktid 7, 9, 10, 15)

MIKS SEE ON OTSUSTAV: strateegia annab +1983 EUR ja labib
robustsustestid (platoo 7/7 lookbacki, 6/7 aastat plussis, lyob
juhuslikku p=0.033). AGA halvim tehing on -49.74 EUR ja pikim
kaotusjada 5. 5 x 49.74 = 248.72 EUR, mis on ROHKEM kui konto.

Monte Carlo utleb, kui suur on toenaosus, et see jada tabab kontot
ENNE kui kasum joudis puhvri ehitada.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import gold_logic, kulumudel as K
from run_live_kuludega import simuleeri, DD, PV, MIN_LOT
import h1engine as E

OUT = "mc_ruin.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

rng = np.random.default_rng(2109)
teh = simuleeri(False, None)
hind_k = float(DD["close"].median())
neto = np.array([(t.pnl or 0) - K.tehingu_kulu(t, hind_k) for t in teh])
ALGUS = 205.0

w("=" * 96)
w("MONTE CARLO — 10 000 simulatsiooni, tehingute järjekord segatud")
w("=" * 96)
w(f"   sisend: {len(neto)} päris tehingut, keskmine {neto.mean():+.2f}€, "
  f"std {neto.std():.2f}€")
w("")

def mc(x, n_sim=10000, algus=ALGUS, libisemine=0.0, ruin_tase=50.0):
    lopud, ddd, ruinid = [], [], 0
    for _ in range(n_sim):
        y = rng.permutation(x) - libisemine
        eq = algus + np.cumsum(y)
        eq = np.concatenate([[algus], eq])
        # konto otsas => lopeta
        surnud = np.where(eq < ruin_tase)[0]
        if len(surnud):
            ruinid += 1
            eq = eq[:surnud[0] + 1]
        lopud.append(eq[-1])
        ddd.append(float((eq / np.maximum.accumulate(eq) - 1).min()))
    return np.array(lopud), np.array(ddd), ruinid / n_sim

for nimi, lib in (("baasjuhtum", 0.0), ("+0.20€ lisaslippage/teh", 0.20),
                  ("+0.50€ lisaslippage/teh", 0.50)):
    lop, dd, ruin = mc(neto, libisemine=lib)
    w(f"   --- {nimi} ---")
    w(f"     mediaan lõppkonto   {np.median(lop):9.2f}€")
    w(f"     halvim 5%           {np.percentile(lop,5):9.2f}€")
    w(f"     parim 5%            {np.percentile(lop,95):9.2f}€")
    w(f"     mediaan maxDD       {100*np.median(dd):8.1f}%")
    w(f"     halvima 5% maxDD    {100*np.percentile(dd,5):8.1f}%")
    w(f"     RISK OF RUIN (<50€) {100*ruin:8.1f}%")
    w("")

w("=" * 96)
w("RISK OF RUIN ERINEVA ALGKAPITALIGA (sama strateegia, 0.01 lot)")
w("=" * 96)
w(f"   {'algkapital':>11s} {'risk/teh':>9s} {'ruin%':>8s} {'mediaan lõpp':>14s} "
  f"{'halvim 5%':>11s}")
w("   " + "-" * 58)
for algus in (205, 500, 1000, 2000, 5000):
    lop, dd, ruin = mc(neto, n_sim=4000, algus=algus, ruin_tase=algus*0.25)
    w(f"   {algus:10d}€ {100*abs(neto.min())/algus:8.1f}% {100*ruin:7.1f}% "
      f"{np.median(lop):13.0f}€ {np.percentile(lop,5):10.0f}€")

w("")
w("=" * 96)
w("POSITION SIZING — kas 205€ kontol SAAB üldse 0.25-1% riski hoida?")
w("=" * 96)
w("   Nõue: risk tehingu kohta <= X% kontost, MIINIMUM-lotiga 0.01")
w("")
w(f"   {'instrument':11s} {'0.01 lot väärtus':>17s} {'ATR(14) H1':>12s} "
  f"{'SL=1.5ATR':>11s} {'% 205€-st':>11s} {'0.25-1% võimalik?':>19s}")
w("   " + "-" * 86)
# 0.01 loti vaartus punkti kohta
UHIK = {"XAUUSD": 1.0, "XAGUSD": 50.0, "EURUSD": 1000.0, "GBPUSD": 1000.0,
        "AUDUSD": 1000.0, "NZDUSD": 1000.0, "USDCHF": 1000.0, "USDCAD": 1000.0,
        "USDJPY": 1000.0, "EURJPY": 1000.0, "GBPJPY": 1000.0, "EURGBP": 1000.0,
        "WTI": 10.0}
JPY = {"USDJPY", "EURJPY", "GBPJPY", "AUDJPY"}
sobivad = []
for sym, uh in UHIK.items():
    d = E.lae(sym)
    if d is None: continue
    atr = float(E.atr(d, 14).dropna().median())
    hind = float(d["close"].median())
    sl_val = 1.5 * atr * uh
    if sym in JPY:
        sl_val /= hind                     # JPY => USD
    pct = 100 * sl_val / 205.0
    ok = "JAH" if pct <= 1.0 else ("1-2%" if pct <= 2 else "EI")
    if pct <= 1.0: sobivad.append(sym)
    w(f"   {sym:11s} {uh:16.1f}  {atr:12.5f} {sl_val:10.2f}€ {pct:10.1f}% {ok:>19s}")
w("")
w(f"   0.25-1% riskiga võimalikud: {', '.join(sobivad) if sobivad else 'MITTE ÜKSKI'}")
w("")
w("   NB: see on H1 ATR. Päevabaaril (mida live praegu kasutab) on ATR")
w("   ~4-5x suurem, seega risk vastavalt suurem.")

w("")
w("=" * 96)
w("PÄEVABAAR — mida live PRAEGU kasutab")
w("=" * 96)
w(f"   {'instrument':11s} {'ATR(14) päev':>14s} {'SL=1.5ATR':>11s} {'% 205€-st':>11s} "
  f"{'€45 lagiga':>12s}")
w("   " + "-" * 64)
for sym in ("XAUUSD",):
    dd_ = DD
    atr_d = float(gold_logic.calc_atr(dd_.iloc[-300:]))
    sl_val = 1.5 * atr_d * 1.0
    w(f"   {sym:11s} {atr_d:13.2f}$ {sl_val:10.2f}€ {100*sl_val/205:10.1f}% "
      f"{100*45/205:11.1f}%")
w("VALMIS")
