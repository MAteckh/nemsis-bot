"""
KASUTAJA IDEE: kuunlamustrid + KOIK instrumendid + VAIKESED tehingud (1-2 EUR).

Idee ryndab oiget probleemi: praegune strateegia teeb 8.8 tehingut aastas,
mis on liiga vahe (ja rikub prop-firma tegevusetuse reeglit). Rohkem
instrumente + vaiksem eesmark = rohkem tehinguid.

SAMM 1 (see fail): KAS ARITMEETIKA TOIMIB?
Enne kui testida uhtegi mustrit, tuleb teada, kas 1-2 EUR eesmark
katab uldse kulud miinimum-lotiga. Kui kulu on eesmargist suurem, ei
aita ukski muster.

SAMM 2 (run_candles.py): kas mustrid uldse ennustavad midagi.

ANDMEHOIATUS, mis tuleb kohe valja oelda:
FX paevabaaride OPEN on katki (Open == Close). KUUNLAMUSTRID
NOUAVAD OPENI. Seega FX paevabaaridel ei saa kuunlamustreid testida
ULDSE. Kasutatavad on ainult need 11 instrumenti, millel on paris
Open: indeksid, metallid, energia, krupto.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

OUT = "small_tp_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

SYMS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
        "EURJPY", "XAUUSD", "XAGUSD", "SPX", "NAS100", "GER40", "JP225",
        "WTI", "COPPER", "BTCUSD", "ETHUSD"]

# Miinimum-lot ja uhiku vaartus 0.01 loti kohta (ligikaudne, BlackBull-tuupiline)
# pip_value = kui palju teenib 1.0 hinnauhiku liikumine 1.0 loti kohta
SPEC = {
    # sym:      (pip_value_1lot, tuupiline spread hinnauhikutes)
    "EURUSD":   (100000.0, 0.00010),
    "GBPUSD":   (100000.0, 0.00012),
    "USDJPY":   (1000.0,   0.010),
    "AUDUSD":   (100000.0, 0.00012),
    "NZDUSD":   (100000.0, 0.00018),
    "USDCAD":   (100000.0, 0.00013),
    "USDCHF":   (100000.0, 0.00013),
    "EURJPY":   (1000.0,   0.015),
    "XAUUSD":   (100.0,    0.30),
    "XAGUSD":   (5000.0,   0.020),
    "SPX":      (100.0,    0.60),
    "NAS100":   (100.0,    1.50),
    "GER40":    (100.0,    1.20),
    "JP225":    (100.0,    6.00),
    "WTI":      (1000.0,   0.030),
    "COPPER":   (10000.0,  0.0015),
    "BTCUSD":   (1.0,      25.0),
    "ETHUSD":   (10.0,     2.50),
}
MINLOT = 0.01


def load(s):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        if c not in d.columns:
            return None
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()


w("=" * 100)
w("1) KAS 1-2€ EESMÄRK KATAB KULUD? (miinimum-lot 0.01)")
w("=" * 100)
w(f"{'sümbol':9s} {'hind':>10s} {'1 punkti €':>11s} {'spread €':>10s} "
  f"{'2€ = punkti':>12s} {'kulu/2€':>9s} {'otsus':>10s}")
w("-" * 100)

kolblik = []
for s in SYMS:
    d = load(s)
    if d is None:
        continue
    pv, spread_units = SPEC[s]
    px = float(d["close"].iloc[-1])
    # 1 hinnauhiku vaartus 0.01 lotiga, eurodes (USD~EUR lihtsustus 1.16)
    unit_eur = pv * MINLOT / 1.1596
    kulu_eur = spread_units * 2 * unit_eur          # edasi-tagasi
    punkte_2e = 2.0 / unit_eur
    suhe = kulu_eur / 2.0
    ok = suhe < 0.30
    if ok:
        kolblik.append(s)
    w(f"{s:9s} {px:10.4f} {unit_eur:10.3f}€ {kulu_eur:9.3f}€ "
      f"{punkte_2e:12.5f} {100*suhe:8.0f}% {'OK' if ok else 'liiga kallis':>10s}")

w("")
w(f"  Kõlblikke (kulu alla 30% eesmärgist): {len(kolblik)}")
w(f"  {', '.join(kolblik) if kolblik else '(mitte ükski)'}")

w("")
w("=" * 100)
w("2) KAS 2€ LIIKUMINE ON ÜLDSE REALISTLIK? (kui tihti hind nii palju liigub)")
w("=" * 100)
w(f"{'sümbol':9s} {'2€ = % hinnast':>15s} {'päevane vahemik %':>19s} "
  f"{'kordi päevas':>13s} {'hinnang':>12s}")
w("-" * 100)
for s in kolblik:
    d = load(s)
    pv, _ = SPEC[s]
    unit_eur = pv * MINLOT / 1.1596
    px = float(d["close"].iloc[-1])
    punkte_2e = 2.0 / unit_eur
    pct_2e = 100.0 * punkte_2e / px
    rng_pct = 100.0 * float(((d["high"] - d["low"]) / d["close"]).median())
    kordi = rng_pct / pct_2e if pct_2e > 0 else 0
    hinnang = "liiga väike" if kordi > 50 else ("hea" if kordi > 3 else "liiga suur")
    w(f"{s:9s} {pct_2e:14.4f}% {rng_pct:18.2f}% {kordi:13.1f} {hinnang:>12s}")

w("")
w("=" * 100)
w("3) ANDMEPIIRANG — kas kuunlamustreid saab üldse testida?")
w("=" * 100)
w(f"{'sümbol':9s} {'|Open-Close| med':>18s} {'Open kasutatav?':>18s}")
w("-" * 50)
for s in SYMS:
    d = load(s)
    if d is None:
        continue
    oc = float(((d["close"] - d["open"]).abs() / d["close"]).median())
    ok = oc > 1e-5
    w(f"{s:9s} {1e4*oc:17.2f}bp {'JAH' if ok else 'EI — Open==Close':>18s}")
w("")
w("  Küünlamustrid nõuavad Open'i. FX päevabaaridel seda ei ole.")
w("VALMIS")
