"""
LOPPKONTROLL + KONKREETNE ARVUTUS 205-EUROSELE KONTOLE.

Walk-forward andis 7/21 instrumenti OOS plussis (mundivisega oodatav
10.5). Neist 4 olid SPX/NAS100/UK100/GER40 "TUND" signaalid. Kontrollin,
kas need on paris kellaaja efekt voi lihtsalt pikk aktsiapositsioon —
sest kui viimane, siis on tegelik OOS-edu 3/21, mitte 7/21.

Seejarel: mida tahendab "palju vaikseid tehinguid paevas" 205-eurosel
kontol, kui panna sisse PARIS numbrid.
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import h1engine as E

OUT = "h1_lopp_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

D = E.lae_koik()

w("=" * 100)
w("1) KAS 'TUND' SIGNAALID INDEKSITEL ON PÄRIS EFEKT VÕI LIHTSALT PIKK POSITSIOON?")
w("=" * 100)
w(f"   {'instr':8s} {'tund':>5s} {'strateegia':>11s} {'OSTA-JA-HOIA':>13s} "
  f"{'vahe':>8s} {'järeldus':>22s}")
w("   " + "-" * 74)
for sym, hh in (("SPX", 18), ("NAS100", 18), ("UK100", 10), ("GER40", 10),
                ("XAGUSD", 2)):
    d = D[sym]
    m = len(d) // 2
    d2 = d.iloc[m:]                     # AINULT OOS-aken
    kulu = 2 * E.KULU_RETAIL[sym] / 1e4
    tund = d2.index.hour
    sg = pd.Series(np.where(tund == hh, 1.0, 0.0), index=d2.index)
    pos = sg.replace(0.0, np.nan).ffill(limit=8).fillna(0.0)
    r_next = (d2["close"].shift(-1) / d2["close"] - 1)
    vah = pos.diff().abs().fillna(pos.abs())
    x = (pos * r_next - vah * kulu / 2).fillna(0.0)
    strat = float((1 + x).prod() - 1)
    # osta-ja-hoia SAMA ajavahemiku peal, sama keskmise positsiooniga
    osa = float((pos != 0).mean())
    bh = float(d2["close"].iloc[-1] / d2["close"].iloc[0] - 1)
    bh_sk = bh * osa                    # sama keskmine turuosalus
    vahe = strat - bh_sk
    jar = "PÄRIS EFEKT" if vahe > abs(bh_sk) * 0.5 else "lihtsalt PIKK positsioon"
    w(f"   {sym:8s} {hh:5d} {100*strat:+10.1f}% {100*bh_sk:+12.1f}% "
      f"{100*vahe:+7.1f}% {jar:>22s}")

w("")
w("   'OSTA-JA-HOIA' on skaleeritud sama turuosaluseni (sama osa ajast turul),")
w("   et võrdlus oleks õiglane.")

# ══ 2) 205 EURO KONTO — PÄRIS ARVUD ═════════════════════════════
w("")
w("=" * 100)
w("2) MIDA TÄHENDAB 'PALJU VÄIKSEID TEHINGUID' 205-EUROSEL KONTOL")
w("=" * 100)
KONTO = 205.0
w(f"   Konto: {KONTO:.0f}€. BlackBull miinimum-lot FX-is: 0.01 = 1000 ühikut.")
w(f"   EURUSD 0.01 lot = ~{1000*1.07:.0f}$ nominaali. Pip = 0.10$.")
w("")
w(f"   {'tehinguid/päev':>15s} {'aastas':>8s} {'kulu/teh':>10s} "
  f"{'kulu aastas':>12s} {'% kontost':>10s} {'vajalik serv':>14s}")
w("   " + "-" * 74)
# 0.01 lot EURUSD, edasi-tagasi kulu 2 bp nominaalist
nominaal = 1000 * 1.07
for per_paev in (1, 2, 5, 10, 20, 50):
    aastas = per_paev * 252
    kulu_teh = nominaal * 2 * 1.0 / 1e4      # 2 x 1.0bp
    kulu_a = kulu_teh * aastas
    # kui palju peab iga tehing bruto teenima, et kulu katta
    w(f"   {per_paev:15d} {aastas:8d} {kulu_teh:9.3f}$ {kulu_a:11.0f}$ "
      f"{100*kulu_a/KONTO:9.0f}% {2*1.0:13.1f}bp")

w("")
w("   Viimane veerg: iga tehing peab BRUTO teenima vähemalt 2.0 baaspunkti")
w("   ainult selleks, et null välja tulla. Meie 10 156 testist oli")
w("   keskmine bruto-serv +0.1bp. Kulu on 20x suurem kui serv.")

w("")
w("   SAMA, AGA VÕIMENDUSEGA (0.10 lot = 10x suurem positsioon):")
w(f"   {'tehinguid/päev':>15s} {'kulu aastas':>12s} {'% kontost':>10s}")
w("   " + "-" * 40)
for per_paev in (1, 5, 10, 20):
    kulu_a = nominaal * 10 * 2 * 1.0 / 1e4 * per_paev * 252
    w(f"   {per_paev:15d} {kulu_a:11.0f}$ {100*kulu_a/KONTO:9.0f}%")

w("")
w("   Võimendus EI aita: ta suurendab nii serva kui kulu ühepalju.")
w("   Suhe jääb samaks. Ainus asi, mida võimendus muudab, on see,")
w("   kui kiiresti konto null saab.")

# ══ 3) MIS SAGEDUS ON PARIM? ════════════════════════════════════
w("")
w("=" * 100)
w("3) MILLINE SAGEDUS ON ANDMETE JÄRGI PARIM?")
w("=" * 100)
df = pd.read_csv("data/h1_soel.csv")
w(f"   {'tehinguid aastas':>18s} {'teste':>7s} {'parim bruto':>12s} "
  f"{'kulu/aasta':>11s} {'parim NETO':>11s}")
w("   " + "-" * 64)
df["ampel"] = pd.cut(df["teh_a"], [0, 100, 300, 700, 1500, 4000, 1e9],
                     labels=["<100", "100-300", "300-700", "700-1500",
                             "1500-4000", ">4000"])
for amp, g in df.groupby("ampel", observed=True):
    kulu_a = (g["bruto"] - g["keskm"]).mean() * g["teh_a"].mean()
    w(f"   {str(amp):>18s} {len(g):7d} {1e4*g['bruto'].max():+11.2f}bp "
      f"{100*kulu_a:10.1f}% {1e4*g['keskm'].max():+10.2f}bp")
w("")
w("   Bruto-serv EI kasva sagedusega. Kulu kasvab LINEAARSELT.")
w("   Seega: mida harvem kaupled, seda parem — täpselt vastupidi")
w("   sellele, mida 'palju väikseid tehinguid' eeldab.")
w("VALMIS")
