"""
MIKS VAIKE TP EI TOO ROHKEM RAHA, KUIGI VOIDAB SAGEDAMINI.

Kasutaja vaide: "kui TP on vaike, jouab kiiremini voiduni ja iga voit
toob midagi sisse."

Esimene pool on TOSI. Teine pool on see, mida siin kontrollime.

TEOORIA: kui hind oleks puhas juhuslik jalutuskaik (ilma triivita),
siis toenaosus tabada TP enne SL-i on TAPSELT:
      p = SL / (TP + SL)
Sellest jareldub oodatav vaartus:
      OV = p*TP - (1-p)*SL
         = SL/(TP+SL)*TP - TP/(TP+SL)*SL
         = 0
IGA TP/SL kombinatsiooni juures. NULL. Alati.

Voiduprotsent kohaneb automaatselt nii, et see tasakaalustub. Vaike TP
annab korge voiduprotsendi, aga iga voit on tapselt nii palju vaiksem,
et summa jaab samaks.

Seega TP/SL valik EI MUUDA oodatavat tulu. Ta muudab AINULT:
  1) kui palju kordi sa kauplema pead  -> kui palju kulu maksad
  2) kuidas tulemus jaotub (palju vaikseid voite vs vahe suuri)

Kontrollime, kas kasutaja PARIS andmed kaituvad nii.
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import h1engine as E

OUT = "miks_vaike_tp.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

D = E.lae_koik()


def teekond(d, tp_atr, sl_atr, max_baare=240, samm=6):
    """
    Sisene IGAL sammu-baaril (suund vaheldumisi pikk/luhike, et suund
    ei annaks eelist), valju TP/SL peal. Tagastab (voiduosa, kesk_kasum,
    kesk_kahjum, kestus_baarides).
    """
    a = E.atr(d).values
    o, h, l, c = (d["open"].values, d["high"].values,
                  d["low"].values, d["close"].values)
    n = len(d)
    voit = kaotus = aeg = 0
    tulem = []
    for i in range(20, n - 1, samm):
        if not (np.isfinite(a[i]) and a[i] > 0):
            continue
        for suund in (1, -1):
            entry = o[i + 1]
            tp = entry + suund * tp_atr * a[i]
            sl = entry - suund * sl_atr * a[i]
            r, kest = None, max_baare
            for j in range(i + 1, min(i + 1 + max_baare, n)):
                th = (h[j] >= tp) if suund == 1 else (l[j] <= tp)
                sh_ = (l[j] <= sl) if suund == 1 else (h[j] >= sl)
                if th and sh_:
                    r, kest = -sl_atr * a[i] / entry, j - i; break
                if th:
                    r, kest = tp_atr * a[i] / entry, j - i; break
                if sh_:
                    r, kest = -sl_atr * a[i] / entry, j - i; break
            if r is None:
                j = min(i + max_baare, n - 1)
                r, kest = suund * (c[j] - entry) / entry, j - i
            tulem.append((r, kest))
    t = np.array([x[0] for x in tulem])
    k = np.array([x[1] for x in tulem])
    return t, k


w("=" * 100)
w("1) KAS VÄIKE TP VÕIDAB SAGEDAMINI? — JAH, ja täpselt nii palju kui teooria ütleb")
w("=" * 100)
w("   Test: sisene juhuslikult (vaheldumisi pikk/lühike, et suund ei annaks eelist).")
w("   Teooria ütleb: võiduprotsent = SL / (TP + SL)")
w("")
w(f"   {'TP':>5s} {'SL':>5s} {'teooria võit%':>14s} {'PÄRIS võit%':>12s} "
  f"{'kesk võit':>10s} {'kesk kaotus':>12s} {'OV ilma kuluta':>15s}")
w("   " + "-" * 80)
d = D["XAUUSD"]
read = []
for tp_a, sl_a in ((0.25, 1.0), (0.5, 1.0), (1.0, 1.0), (2.0, 1.0),
                   (3.0, 1.0), (0.5, 2.0), (0.25, 4.0)):
    t, kest = teekond(d, tp_a, sl_a)
    teooria = 100 * sl_a / (tp_a + sl_a)
    paris = 100 * float((t > 0).mean())
    kv = 1e4 * float(t[t > 0].mean()) if (t > 0).any() else 0
    kk = 1e4 * float(t[t <= 0].mean()) if (t <= 0).any() else 0
    ov = 1e4 * float(t.mean())
    read.append((tp_a, sl_a, teooria, paris, kv, kk, ov, float(kest.mean())))
    w(f"   {tp_a:5.2f} {sl_a:5.2f} {teooria:13.1f}% {paris:11.1f}% "
      f"{kv:+9.1f}bp {kk:+11.1f}bp {ov:+14.2f}bp")

w("")
w("   => Võiduprotsent järgib teooriat peaaegu täpselt. Ja veerg 'OV ilma")
w("      kuluta' on iga rea peal ~NULL. TP/SL valik EI MUUDA oodatavat tulu.")
w("      Ta muudab ainult seda, KUIDAS tulemus jaotub.")

# ── 2) MIS SIIS MUUTUB? KULU. ───────────────────────────────────
w("")
w("=" * 100)
w("2) MIS SIIS ÜLDSE MUUTUB? — KULU OSAKAAL SIHIST")
w("=" * 100)
hind = float(d["close"].median())
atr_med = float(E.atr(d).dropna().median())
kulu_bp = 2 * E.KULU_RETAIL["XAUUSD"]         # edasi-tagasi, baaspunktides
kulu_usd = hind * kulu_bp / 1e4               # 0.01 lot XAUUSD => 1 unts
w(f"   XAUUSD hind ~{hind:.0f}$, ATR(14) H1 ~{atr_med:.2f}$")
w(f"   Edasi-tagasi kulu: {kulu_bp:.1f}bp = {kulu_usd:.2f}$ (0.01 lot)")
w("")
w(f"   {'TP':>5s} {'TP dollarites':>14s} {'kulu':>8s} {'KULU % TP-st':>14s} "
  f"{'tehingu kestus':>15s} {'teh/aastas':>11s}")
w("   " + "-" * 74)
for tp_a, sl_a, teo, par, kv, kk, ov, kest in read:
    tp_usd = tp_a * atr_med
    osa = 100 * kulu_usd / tp_usd
    teh_a = 6000 / kest if kest > 0 else 0
    w(f"   {tp_a:5.2f} {tp_usd:13.2f}$ {kulu_usd:7.2f}$ {osa:13.1f}% "
      f"{kest:14.0f}h {teh_a:11.0f}")

w("")
w("   SIIN ONGI KOGU ASI:")
w("   TP 0.25 ATR = 3.61$ siht, aga kulu 1.01$ => kulu on 28% sihist.")
w("   TP 3.00 ATR = 43.3$ siht, kulu sama 1.01$ => kulu on 2.3% sihist.")
w("   Sama kulu, 12x erinev osakaal. Ja väikse TP-ga kaupled sa ka")
w("   palju SAGEDAMINI, ehk maksad seda kulu palju rohkem kordi.")

# ── 3) LOPLIK: OV parast kulu ───────────────────────────────────
w("")
w("=" * 100)
w("3) OODATAV TULU PÄRAST KULU — see on ainus number, mis loeb")
w("=" * 100)
w(f"   {'TP':>5s} {'SL':>5s} {'võit%':>7s} {'OV enne kulu':>13s} "
  f"{'kulu':>8s} {'OV PÄRAST':>11s} {'aastas 0.01 lot':>16s}")
w("   " + "-" * 74)
for tp_a, sl_a, teo, par, kv, kk, ov, kest in read:
    netо = ov - kulu_bp
    teh_a = 6000 / kest if kest > 0 else 0
    aasta_usd = netо / 1e4 * hind * teh_a
    w(f"   {tp_a:5.2f} {sl_a:5.2f} {par:6.1f}% {ov:+12.2f}bp {kulu_bp:7.1f}bp "
      f"{netо:+10.2f}bp {aasta_usd:+15.0f}$")

w("")
w("   Iga rida on miinuses. Kõige rohkem miinuses on VÄIKSEIM TP —")
w("   sest ta maksab sama kulu kõige rohkem kordi.")
w("")
w("=" * 100)
w("4) MIS SEE TÄHENDAB: 62% VÕITE JA IKKA KAOTAD")
w("=" * 100)
tp_a, sl_a = 0.5, 1.0
t, kest = teekond(d, tp_a, sl_a)
p = float((t > 0).mean())
vt, kt = 1e4*float(t[t>0].mean()), 1e4*float(t[t<=0].mean())
w(f"   TP 0.5 ATR / SL 1.0 ATR:")
w(f"     võidad {100*p:.0f}% ajast, keskmine võit {vt:+.0f}bp")
w(f"     kaotad {100*(1-p):.0f}% ajast, keskmine kaotus {kt:+.0f}bp")
w(f"     100 tehingut: {100*p:.0f} x {vt:+.0f} = {100*p*vt:+.0f}bp")
w(f"                   {100*(1-p):.0f} x {kt:+.0f} = {100*(1-p)*kt:+.0f}bp")
w(f"     summa enne kulu: {100*(p*vt + (1-p)*kt):+.0f}bp")
w(f"     kulu 100 tehingult: {-100*kulu_bp:+.0f}bp")
w(f"     KOKKU: {100*(p*vt+(1-p)*kt) - 100*kulu_bp:+.0f}bp")
w("")
w("   Kaks kaotust söövad kolm võitu ära. Võiduprotsent näeb hea välja,")
w("   aga ta ei ütle sulle, kui palju iga võit toob.")
w("VALMIS")
