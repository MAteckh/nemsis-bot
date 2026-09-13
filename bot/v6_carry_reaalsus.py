"""
OTSUSTAV TEST: KAS SEDA CARRY'T SAAB PARISELT KATTE?

Carry C1 annab +1.18 bp/paev, Sharpe +0.42. Lahutus:
  hinnamuutus +0.14 bp  (praktiliselt null, nagu carry puhul peabki)
  CARRY       +1.05 bp  (= 2.65% aastas) <- KOGU tulu tuleb siit
  kulu        -0.01 bp

AGA: ma arvutasin carry KESKPANGA POLIITIKAMAARADEST. Sina ei kauple
keskpangaga. Sa kauplad BlackBulli CFD-dega, kus swap on:
  swap = intressivahe MIINUS brokeri juurdehindlus
Retail CFD-brokerid votavad tuupiliselt 0.5-2.0% aastas KUMMALTKI
poolelt. Ja carry-positsioon on ALATI kahepoolne (long uks valuuta,
short teine) => maksad juurdehindlust KAKS korda.

KUI juurdehindlus on 1.3% poole kohta, kaob kogu 2.65% serv ara.

Testime tundlikkust. Lisaks:
  - kas tulu tuleb UHEST valuutast (JPY short)?
  - carry on tuntud oma CRASH-riski poolest: kontrolli asummeetriat
  - 205 EUR teostatavus
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import v5_engine as V
from v6_carry import CARRY_REL, S, korv, P, VAL, KESK

OUT = "v6_reaalsus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

c1 = korv(CARRY_REL, rebal=21)
neto = c1["neto"].dropna()

w("=" * 96)
w("1) BROKERI SWAP-JUURDEHINDLUS — kas serv jääb alles?")
w("=" * 96)
w("  Carry-positsioon on kahepoolne => juurdehindlust makstakse KAKS korda.")
w("  Positsioon on lahti kogu aeg (kuine rebalanss), seega juurdehindlus")
w("  rakendub IGA paev.")
w("")
w(f"  {'juurdehindlus/pool/aasta':>26s} {'aastane kulu':>13s} {'NETO bp/päev':>14s} "
  f"{'Sharpe':>8s} {'hinnang':>12s}")
w("  " + "-" * 78)
baas = float(neto.mean())
for mh in (0.0, 0.25, 0.50, 0.75, 1.00, 1.30, 1.50, 2.00):
    # 2 poolt x mh% aastas, paevas
    kulu_p = 2 * mh / 100.0 / 252.0
    n2 = neto - kulu_p
    sh = V.sharpe(n2)
    h = "TÖÖTAB" if float(n2.mean()) > 0 else "KAOTAJA"
    w(f"  {mh:>25.2f}% {2*mh:>12.2f}% {1e4*float(n2.mean()):+14.2f} {sh:+8.2f} {h:>12s}")
# murdepunkt
murd = 1e4 * baas / 2 * 252 / 100
w("")
w(f"  MURDEPUNKT: serv kaob, kui juurdehindlus ületab "
  f"{100*baas*252/2:.2f}% poole kohta aastas.")
w("  BlackBull standard-konto tüüpiline FX swap-juurdehindlus: 0.5-1.5%/pool.")

w("")
w("=" * 96)
w("2) KAS TULU TULEB ÜHEST VALUUTAST?")
w("=" * 96)
sk = CARRY_REL.dropna(how="all")
pv = sk.index[::21]
read = []
for t in pv:
    r = sk.loc[t].dropna()
    if len(r) < 4: continue
    j = r.sort_values(ascending=False)
    rida_ = pd.Series(0.0, index=sk.columns, name=t)
    rida_[j.index[:2]] = 0.5; rida_[j.index[-2:]] = -0.5
    read.append(rida_)
W = pd.DataFrame(read).reindex(sk.index, method="ffill").fillna(0.0)
Wp = W.shift(1).fillna(0.0)
ix = Wp.index.intersection(S.index).intersection(CARRY_REL.index)
w(f"  {'valuuta':>8s} {'LONG %ajast':>12s} {'SHORT %ajast':>13s} {'panus NETO-sse':>16s}")
w("  " + "-" * 54)
kokku = 0.0
panused = {}
for v in VAL:
    lng = float((Wp[v] > 0).mean()); srt = float((Wp[v] < 0).mean())
    p_ = float((Wp[v].reindex(ix) * (S[v].reindex(ix) + CARRY_REL[v].reindex(ix))).mean())
    panused[v] = p_; kokku += p_
    w(f"  {v:>8s} {100*lng:11.1f}% {100*srt:12.1f}% {1e4*p_:+15.2f}bp")
w("  " + "-" * 54)
w(f"  {'KOKKU':>8s} {'':>12s} {'':>13s} {1e4*kokku:+15.2f}bp")
suurim = max(panused, key=lambda k: abs(panused[k]))
w("")
w(f"  Suurim üksikpanus: {suurim} ({1e4*panused[suurim]:+.2f}bp = "
  f"{100*panused[suurim]/kokku:.0f}% kogutulust)")
if abs(panused[suurim]/kokku) > 0.5:
    w("  => TULU ON KONTSENTREERITUD ÜHTE VALUUTASSE. See on ühe makro-")
    w("     stsenaariumi panus, mitte hajutatud faktor.")

w("")
w("=" * 96)
w("3) CARRY CRASH-RISK — asümmeetria")
w("=" * 96)
x = neto.values
kuine = neto.resample("ME").sum()
w(f"  kalduvus (skew)      {float(pd.Series(x).skew()):+7.2f}   "
  f"(carry'l on ajalooliselt tugev NEGATIIVNE kalduvus)")
w(f"  kurtoos              {float(pd.Series(x).kurt()):+7.2f}")
w(f"  halvim päev          {1e4*float(x.min()):+7.0f}bp")
w(f"  halvim kuu           {100*float(kuine.min()):+7.2f}%")
w(f"  halvim 5% päevadest  {1e4*float(np.percentile(x,5)):+7.0f}bp")
w(f"  parim 5% päevadest   {1e4*float(np.percentile(x,95)):+7.0f}bp")
m = V.moodikud(neto)
w(f"  maxDD                {100*m['maxdd']:+7.1f}%")
w(f"  taastumistegur       {m['taastumis']:+7.2f}")

w("")
w("=" * 96)
w("4) 205 EUR TEOSTATAVUS")
w("=" * 96)
w("  C1 nõuab: LONG 2 valuutat + SHORT 2 valuutat = 4 valuutapositsiooni.")
w("  Need realiseeritakse 2-4 valuutapaarina, iga miinimum 0.01 lot.")
w("")
w(f"  {'näitaja':>34s} {'väärtus':>14s}")
w("  " + "-" * 50)
nom = 1000 * 1.10                     # 0.01 lot ~ 1100 USD nominaali
w(f"  {'0.01 lot nominaal':>34s} {nom:13.0f}$")
w(f"  {'4 positsiooni nominaal':>34s} {4*nom:13.0f}$")
w(f"  {'konto':>34s} {205:13.0f}€")
w(f"  {'vajalik võimendus':>34s} {4*nom/205:12.1f}x")
aastane = float(neto.mean()) * 252
w(f"  {'strateegia aastatootlus (1x)':>34s} {100*aastane:12.2f}%")
w(f"  {'sama 205€ pealt (1x nominaal)':>34s} {205*aastane:12.2f}€")
w(f"  {'4 x 0.01 lot => tegelik võimendus':>34s} {4*nom/205:12.1f}x")
w(f"  {'tootlus selle võimendusega':>34s} {205*aastane*(4*nom/205):12.2f}€/a")
w(f"  {'sama võimendusega maxDD':>34s} "
  f"{100*m['maxdd']*(4*nom/205):11.1f}%")
w("")
w("  Kui 21.5x võimendusega on maxDD -240%, on konto ammu otsas.")
w("  Miinimum-lot sunnib võimenduse peale, mida strateegia ei kannata.")
w("VALMIS")
