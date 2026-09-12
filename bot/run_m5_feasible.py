"""
M5 KULLAANDMED — KAS SEAL SAAB ULDSE RAHA TEENIDA?

44 197 M5 baari (marts-august 2026) on ainus andmestik, mida ma pole
kordagi puudutanud. Enne kui viskan sinna 50 strateegiatesti, mootan
ara FUNDAMENTAALSE PIIRI: kas liikumine on suurem kui spread?

Kui keskmine M5 liikumine on vaiksem kui edasi-tagasi kulu, siis EI OLE
VOIMALIK uhtegi kasumlikku M5 strateegiat teha — see ei ole strateegia
kusimus, vaid aritmeetika. Parem teada seda 2 minutiga kui 2 tunniga.

BlackBulli PARIS kullaspread (check_jp225.py naitas JPN225 kohta 0.93bp;
XAUUSD on tavaliselt 1.5-3.0bp/pool). Kasutame 1.5bp ja 3.0bp.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, "data", "xauusd_m5_2026-03_2026-08.csv")
d = pd.read_csv(p)
d["t"] = pd.to_datetime(d["timestamp"], unit="ms", utc=True)
d = d.set_index("t").sort_index()
d = d[~d.index.duplicated(keep="last")]
for c in ("open", "high", "low", "close"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna()

print("=" * 88)
print("1) ANDMETE KVALITEET")
print("=" * 88)
print(f"  baare        : {len(d):,}")
print(f"  vahemik      : {d.index[0]} .. {d.index[-1]}")
print(f"  paevi        : {d.index.normalize().nunique()}")
print(f"  hind         : {d['close'].min():,.0f} .. {d['close'].max():,.0f}")
hl = (d["high"] == d["low"]).mean()
oc = (d["open"] == d["close"]).mean()
print(f"  H==L (liikumiseta baare)  : {100*hl:.1f}%")
print(f"  O==C                      : {100*oc:.1f}%")
samm = pd.Series(d.index).diff().dt.total_seconds().value_counts().head(3)
print(f"  ajasammud (sek, top 3)    : {dict(samm)}")

r = d["close"].pct_change().dropna()
rng = ((d["high"] - d["low"]) / d["open"]).dropna()

print()
print("=" * 88)
print("2) FUNDAMENTAALNE PIIR — liikumine vs kulu")
print("=" * 88)
print(f"  {'mõõdik':38s} {'bp':>10s}")
print("  " + "-" * 50)
print(f"  {'|5-min tootlus| mediaan':38s} {1e4*r.abs().median():10.2f}")
print(f"  {'|5-min tootlus| keskmine':38s} {1e4*r.abs().mean():10.2f}")
print(f"  {'5-min kõikumine (std)':38s} {1e4*r.std():10.2f}")
print(f"  {'baari vahemik (H-L) mediaan':38s} {1e4*rng.median():10.2f}")
print()
for sp in (1.5, 3.0):
    rt = 2 * sp
    print(f"  --- spread {sp}bp/pool => edasi-tagasi {rt}bp ---")
    print(f"      kulu / mediaan liikumine : {rt/(1e4*r.abs().median()):6.2f}x")
    print(f"      kulu / std               : {rt/(1e4*r.std()):6.2f}x")
    osa = float((r.abs() * 1e4 > rt).mean())
    print(f"      baare, kus liikumine > kulu: {100*osa:5.1f}%")

print()
print("=" * 88)
print("3) MITU BAARI PEAB HOIDMA, ET KULU ÄRA TEENIDA?")
print("=" * 88)
print("  (juhusliku kõnna korral kasvab oodatav liikumine ~sqrt(aeg)-ga)")
print(f"  {'hoidmisaeg':>14s} {'oodatav |liikumine|':>21s} {'vs 3bp kulu':>13s} {'vs 6bp':>9s}")
print("  " + "-" * 62)
for n in (1, 3, 6, 12, 24, 48, 96, 288):
    fwd = (d["close"].shift(-n) / d["close"] - 1).dropna()
    m = 1e4 * fwd.abs().median()
    mins = n * 5
    lbl = f"{n} baari ({mins}min)" if mins < 60 else f"{n} baari ({mins/60:.0f}h)"
    print(f"  {lbl:>14s} {m:20.1f}bp {m/3.0:12.1f}x {m/6.0:8.1f}x")

print()
print("=" * 88)
print("4) OTSUS")
print("=" * 88)
med = 1e4 * r.abs().median()
if med < 3.0:
    print(f"  Mediaan 5-min liikumine on {med:.2f}bp, edasi-tagasi kulu 3-6bp.")
    print("  => ÜKSIKUL M5 BAARIL KAUPLEMINE ON ARITMEETILISELT VÕIMATU.")
    print("     Kulu on liikumisest suurem. Ükski signaal ei aita.")
    print("     Ainus tee: hoia positsiooni kauem (vt tabel 3) — aga siis")
    print("     ei ole see enam M5 strateegia, vaid H1/päeva strateegia,")
    print("     mida me juba testisime.")
else:
    print(f"  Mediaan 5-min liikumine {med:.2f}bp > kulu => tasub testida.")
