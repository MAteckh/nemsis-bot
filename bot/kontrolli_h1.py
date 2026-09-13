"""
H1-ANDMETE KVALITEEDIAUDIT enne mistahes strateegiatesti.

MIKS: Yahoo FX-sumbolid (EURUSD=X) on indikatiivsed noteeringud, mitte
paris kauplemisandmed. Tuntud probleemid:
  - Open == eelmine Close (sunteetiline Open) => breakout-testid valed
  - lamedad baarid (high == low) => "vaikne turg" mida ei olnud
  - puuduvad tunnid, nadalavahetuse read
  - hinnahupped, mis on tegelikult andmeviga
Kui Open on sunteetiline, EI TOHI testida sisenemist jargmise baari
avanemisel — see on tapselt eelmise baari sulgemishind ja tekitab
naiva serva.
"""
import warnings; warnings.filterwarnings("ignore")
import os, glob
import numpy as np, pandas as pd
import research as R

print(f"{'instrument':10s} {'baare':>7s} {'algus':>11s} {'lõpp':>11s} "
      f"{'O==prevC':>9s} {'H==L':>7s} {'dubl':>6s} {'tühik>3h':>9s} {'hüpe>5%':>8s}")
print("-" * 92)
halvad = []
for p in sorted(glob.glob(os.path.join(R.DATA, "*_h1.csv"))):
    sym = os.path.basename(p).replace("_h1.csv", "")
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d.columns = [c.strip().lower() for c in d.columns]
    n0 = len(d)
    dubl = int(d.index.duplicated().sum())
    d = d[~d.index.duplicated(keep="last")].dropna()
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    # 1) kas Open on lihtsalt eelmine Close?
    sunt = float((o - c.shift(1)).abs().le(1e-9).mean())
    # 2) lamedad baarid
    lame = float((h - l).le(1e-9).mean())
    # 3) ajatuhikud
    dt = d.index.to_series().diff().dt.total_seconds() / 3600
    tuhik = float((dt > 3).mean())
    # 4) ebarealistlikud hupped
    hupe = float((c / c.shift(1) - 1).abs().gt(0.05).mean())
    # 5) OHLC loogika katki?
    katki = int(((h < l) | (h < o) | (h < c) | (l > o) | (l > c)).sum())
    lipp = ""
    if sunt > 0.5:
        lipp += " SÜNTEETILINE-OPEN"; halvad.append(sym)
    if lame > 0.10:
        lipp += " LAMEDAD"
    if katki:
        lipp += f" OHLC-KATKI({katki})"
    print(f"{sym:10s} {n0:7d} {str(d.index[0].date()):>11s} {str(d.index[-1].date()):>11s} "
          f"{100*sunt:8.1f}% {100*lame:6.1f}% {dubl:6d} {100*tuhik:8.1f}% {100*hupe:7.2f}%{lipp}")

print()
print("KOKKUVÕTE:")
if halvad:
    print(f"  SÜNTEETILISE OPEN'iga (ei kolba baari-avanemisel sisenemise testiks):")
    print(f"    {', '.join(halvad)}")
else:
    print("  Ühelgi instrumendil ei ole sünteetilist Open'i.")
