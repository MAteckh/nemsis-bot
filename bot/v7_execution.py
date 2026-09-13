"""
v7 PARIS TAITMISE SIMULATSIOON (kasutaja punktid 4, 12, 13).

REEGEL: kui arvutatud lot < brokeri miinimum, siis TRADE = REJECTED.
MITTE umardada ules. MITTE suurendada riski.

Riskitasemed: 0.25% (target), 0.5% (hard max).
Kapital: 205, 250, 300, 500, 1000 EUR.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "v7_execution.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

FX22 = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
        "EURGBP","EURJPY","EURCHF","EURAUD","EURNZD","GBPJPY","GBPCHF",
        "GBPAUD","GBPCAD","AUDJPY","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"]
D = {s: E.lae(s) for s in FX22}
D = {k: v for k, v in D.items() if v is not None}
MIN_LOT, LOT_STEP = 0.01, 0.01
JPY = {"USDJPY","EURJPY","GBPJPY","AUDJPY","NZDJPY","CADJPY","CHFJPY"}

w("=" * 96)
w("1) SL-i VÄÄRTUS MIINIMUM-LOTIGA — mis see päriselt maksab?")
w("=" * 96)
w("  SL = 1.5 x ATR(14) H1. 0.01 lot = 1000 ühikut baasvaluutat.")
w("")
w(f"  {'paar':8s} {'ATR(14)':>10s} {'SL 0.01 lotiga':>15s} "
  f"{'% 205€-st':>10s} {'0.25% lubab lot':>16s} {'täidetav?':>10s}")
w("  " + "-" * 76)
read = []
for sym, d in D.items():
    a = float(E.atr(d, 14).dropna().median())
    hind = float(d["close"].median())
    sl_val = 1.5 * a * 1000.0                 # baasvaluutas
    if sym in JPY:
        sl_val /= hind                        # JPY -> USD
    elif sym.endswith("CHF"):
        sl_val /= hind if hind > 0 else 1     # XXXCHF -> CHF -> ~USD
    elif sym.endswith(("CAD","AUD","NZD")):
        pass                                  # ligikaudu, kvootvaluuta ~0.65-1.35 USD
    pct = 100 * sl_val / 205.0
    lubatud_lot = (205.0 * 0.0025) / (sl_val / MIN_LOT)
    read.append(dict(sym=sym, sl=sl_val, pct=pct, lot=lubatud_lot))
    w(f"  {sym:8s} {a:10.5f} {sl_val:14.2f}€ {pct:9.1f}% {lubatud_lot:15.4f} "
      f"{'JAH' if lubatud_lot >= MIN_LOT else 'EI':>10s}")
R = pd.DataFrame(read)
w("  " + "-" * 76)
w(f"  keskmine SL 0.01 lotiga: {R['sl'].mean():.2f}€ = {R['pct'].mean():.1f}% 205€-st")
w(f"  0.25% riskiga täidetavaid paare: {int((R['lot'] >= MIN_LOT).sum())}/{len(R)}")

w("")
w("=" * 96)
w("2) KAPITALI SKAALEERIMINE — millal miinimum-lot piirang kaob?")
w("=" * 96)
w("  Riskiprotsenti EI muudeta. Ainult kapital kasvab.")
w("")
w(f"  {'kapital':>9s} " + "".join(f"{f'{p}%':>14s}" for p in (0.25, 0.5, 0.75, 1.0)))
w("  " + "-" * 65)
for kap in (205, 250, 300, 500, 1000, 2000, 5000):
    rida = f"  {kap:8d}€ "
    for pct in (0.0025, 0.005, 0.0075, 0.01):
        lubatud = (R["sl"] / MIN_LOT)          # EUR ühe loti kohta
        lot = (kap * pct) / lubatud
        n_ok = int((lot >= MIN_LOT).sum())
        rida += f"{n_ok:>6d}/{len(R):<7d}"
    w(rida)
w("")
w("  Arvud = mitu paari 22-st on selle kapitali ja riskiga TÄIDETAV.")

w("")
w("=" * 96)
w("3) MITU POSITSIOONI KORRAGA MAHUB?")
w("=" * 96)
w(f"  {'kapital':>9s} {'0.25% risk':>12s} {'1 positsioon':>14s} "
  f"{'max positsioone':>16s} {'kogurisk':>10s}")
w("  " + "-" * 66)
kesk_sl = float(R["sl"].mean())
for kap in (205, 250, 300, 500, 1000, 2000, 5000):
    lubatud_eur = kap * 0.0025
    # miinimum-lotiga on risk fikseeritud kesk_sl juures
    n_max = int(np.floor(lubatud_eur / kesk_sl)) if kesk_sl > 0 else 0
    tegelik_1 = 100 * kesk_sl / kap
    w(f"  {kap:8d}€ {lubatud_eur:11.2f}€ {kesk_sl:13.2f}€ {n_max:16d} "
      f"{tegelik_1:9.1f}%")
w("")
w("  '1 positsioon' = mida miinimum-lot 0.01 tegelikult riskib.")
w("  'kogurisk' = see ÜHE positsiooni risk protsendina kontost.")
w("  Kui see ületab 0.25%, on juba esimene tehing üle lubatud piiri.")

w("")
w("=" * 96)
w("4) MIS JUHTUB, KUI JÄRGIDA REEGLIT 'REJECT KUI EI MAHU'?")
w("=" * 96)
S = pd.read_pickle("data/v7_signaalid.pkl")
sl_map = dict(zip(R["sl"].index.map(lambda i: R.loc[i, "sym"]), R["sl"]))
S["sl_eur"] = S["sym"].map(sl_map)
for kap, pct in ((205, 0.0025), (205, 0.005), (500, 0.0025), (1000, 0.0025),
                 (2000, 0.0025), (5000, 0.0025)):
    lubatud = kap * pct
    mahub = S["sl_eur"] <= lubatud
    w(f"  {kap:5d}€ @ {100*pct:.2f}% risk ({lubatud:5.2f}€): "
      f"täidetavaid signaale {int(mahub.sum()):6d}/{len(S)} "
      f"({100*mahub.mean():5.1f}%)")
w("")
w("  205€ @ 0.25%: lubatud risk on 0.51€. Keskmine SL miinimum-lotiga")
w(f"  on {kesk_sl:.2f}€ — {kesk_sl/0.5125:.0f} korda suurem.")
w("VALMIS")
