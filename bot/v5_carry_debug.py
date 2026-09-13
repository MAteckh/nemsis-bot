"""
CS-CARRY ANDIS SHARPE 4.4 — SEE EI SAA OLLA OIGE. KUS ON VIGA?

Paris FX carry Sharpe on kirjanduses 0.4-0.8. Sharpe 4.4 tahendab, et
midagi lekib. Kaks kahtlustatavat:

KAHTLUSTATAV 1 — POORDUMISE SAASTUMINE.
Carry-skoor C_t = ETF_tootlus_t MIINUS spot_tootlus_t. Selles on sees
MIINUS spot-tootlus. Kui seda 60 paeva keskmistada ja siis jarjestada,
on skooris komponent "-viimaste paevade tootlus" ehk POORDUMISSIGNAAL.
Ja H01 naitas, et 1-paevane poordumine on FX-is tugev (-5.19bp momentumi
kasuks tahendab +5.19bp poordumise kasuks).
=> carry ei pruugi olla carry, vaid poordumine.

KAHTLUSTATAV 2 — ETF-i ja spot-i erinev sulgemisaeg tekitab
sunteetilise korrelatsiooni.

OTSUSTAV TEST: paris intressivahe liigub AEGLASELT (keskpangad muudavad
maarasid kord kvartalis). Kui lukata skoori N paeva, ei tohi PARIS carry
peaaegu muutuda. Poordumise artefakt seevastu KAOB kohe.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import v5_engine as V
from v5_run import korv_tootlus, S, C

OUT = "v5_carry_debug.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

w("=" * 92)
w("OTSUSTAV TEST: LÜKKA CARRY-SKOORI AJAS TAGASI")
w("=" * 92)
w("  Päris intressivahe liigub aeglaselt => lükkamine ei tohi seda lõhkuda.")
w("  Pöördumise artefakt kaob kohe.")
w("")
w(f"  {'nihe':>10s} {'BRUTO bp':>10s} {'NETO bp':>10s} {'Sharpe':>8s} {'alles %':>9s}")
w("  " + "-" * 50)
baas = None
for nihe in (0, 1, 2, 5, 10, 20, 60, 120):
    sk = C.reindex(S.index).ffill().rolling(60).mean().shift(nihe)
    n_, br_ = korv_tootlus(sk)
    if n_ is None: continue
    neto = 1e4*float(n_.mean())
    if baas is None: baas = neto
    w(f"  {nihe:9d}p {1e4*float(br_.mean()):+10.2f} {neto:+10.2f} "
      f"{V.sharpe(n_):+8.2f} {100*neto/baas:8.0f}%")

w("")
w("=" * 92)
w("KONTROLL 2: ASENDA CARRY PUHTA PÖÖRDUMISSIGNAALIGA")
w("=" * 92)
w("  Kui carry on tegelikult pöördumine, peab -1 x hiljutine tootlus andma sama.")
w("")
w(f"  {'signaal':>26s} {'NETO bp':>10s} {'Sharpe':>8s}")
w("  " + "-" * 46)
for nimi, sk in (("carry (60p keskm)", C.reindex(S.index).ffill().rolling(60).mean()),
                 ("PÖÖRDUMINE -1 x 60p tootlus", -S.rolling(60).sum()),
                 ("PÖÖRDUMINE -1 x 20p tootlus", -S.rolling(20).sum()),
                 ("PÖÖRDUMINE -1 x 1p tootlus", -S.rolling(1).sum())):
    n_, br_ = korv_tootlus(sk)
    if n_ is None: continue
    w(f"  {nimi:>26s} {1e4*float(n_.mean()):+10.2f} {V.sharpe(n_):+8.2f}")

w("")
w("=" * 92)
w("KONTROLL 3: KORRELATSIOON CARRY-SKOORI JA PÖÖRDUMISSIGNAALI VAHEL")
w("=" * 92)
c60 = C.reindex(S.index).ffill().rolling(60).mean()
rev = -S.rolling(60).sum()
ix = c60.dropna(how="all").index.intersection(rev.dropna(how="all").index)
korr = []
for v in c60.columns:
    if v not in rev.columns: continue
    a, b = c60[v].reindex(ix), rev[v].reindex(ix)
    m = a.notna() & b.notna()
    if m.sum() > 200:
        korr.append((v, float(np.corrcoef(a[m], b[m])[0,1])))
for v, k in korr:
    w(f"  {v:>6s}: r = {k:+.3f}")
w(f"  KESKMINE: r = {np.mean([k for _, k in korr]):+.3f}")
w("")
if abs(np.mean([k for _, k in korr])) > 0.5:
    w("  => CARRY-SKOOR ON SUURES OSAS PÖÖRDUMISSIGNAAL. Leid ei ole carry.")
else:
    w("  => korrelatsioon madal, carry on eraldiseisev.")

w("")
w("=" * 92)
w("KONTROLL 4: PUHAS CARRY — kasuta AINULT AASTA VANUST intressivahet")
w("=" * 92)
w("  Aasta vanune intressivahe ei saa sisaldada hiljutist tootlust.")
w("  Kui carry on päris, peab ta osaliselt alles jääma (määrad on püsivad).")
w("")
sk = C.reindex(S.index).ffill().rolling(250).mean().shift(250)
n_, br_ = korv_tootlus(sk)
if n_ is not None:
    tr, va, fo = V.jaota(n_)
    w(f"  aasta vanune carry: NETO {1e4*float(n_.mean()):+.2f}bp, Sharpe {V.sharpe(n_):+.2f}")
    w(f"    TRAIN {1e4*float(tr.mean()):+.2f}  VALID {1e4*float(va.mean()):+.2f}  "
      f"FINAL OOS {1e4*float(fo.mean()):+.2f}")
w("VALMIS")
