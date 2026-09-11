"""
VIITAJAGA SEOSED (lead-lag) — kas ühe instrumendi liikumine ennustab
teise järgmise päeva liikumist?

21 instrumenti = 420 suunatud paari. Mitmese testimise probleem on
massiivne: 420 testi juures leiame ~21 "olulist" seost (p<0.05)
PUHTALT JUHUSLIKULT. Seepärast:
  1. Bonferroni korrektsioon (p < 0.05/420)
  2. Out-of-sample kontroll: leia seosed 1. poolel, testi 2. poolel
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd

# scipy pole saadaval - arvuta Pearsoni korrelatsioon ja p-vaartus ise
# (t-jaotuse lahend suurte n juures = normaaljaotus, mis n>200 juures
# on praktiliselt tapne)
import math
class _Stats:
    @staticmethod
    def pearsonr(x, y):
        x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
        n = len(x)
        if n < 3: return 0.0, 1.0
        xm, ym = x - x.mean(), y - y.mean()
        denom = math.sqrt((xm**2).sum() * (ym**2).sum())
        if denom == 0: return 0.0, 1.0
        r = float((xm*ym).sum() / denom)
        r = max(-0.999999, min(0.999999, r))
        t = r * math.sqrt((n-2) / (1 - r*r))
        # kahepoolne p normaaljaotuse lahendina
        z = abs(t)
        p = math.erfc(z / math.sqrt(2))
        return r, p
stats = _Stats()
import research as R

px = R.load_panel()
rets = R.returns(px)
syms = list(rets.columns)
n_pairs = len(syms) * (len(syms) - 1)
mid = len(rets) // 2

print(f"Instrumente: {len(syms)}   suunatud paare: {n_pairs}   "
      f"Bonferroni lävend: p < {0.05/n_pairs:.6f}\n")

print("=" * 108)
print("A) KOGU PERIOOD — leia kõik seosed, kus eilne A ennustab tänast B")
print("=" * 108)
found = []
for a in syms:
    for b in syms:
        if a == b: continue
        x = rets[a].shift(1).iloc[1:]
        y = rets[b].iloc[1:]
        m = x.notna() & y.notna()
        if m.sum() < 200: continue
        r, p = stats.pearsonr(x[m], y[m])
        if p < 0.05:
            found.append((a, b, r, p))

found.sort(key=lambda t: t[3])
sig_naive = len(found)
sig_bonf = sum(1 for f in found if f[3] < 0.05/n_pairs)
print(f"  p < 0.05 (naiivne):      {sig_naive:4d} seost")
print(f"  juhuslikult oodatav:     {int(0.05*n_pairs):4d} seost")
print(f"  p < Bonferroni lävend:   {sig_bonf:4d} seost")
print()
print("  10 tugevaimat (kogu periood):")
for a, b, r, p in found[:10]:
    flag = " *BONFERRONI*" if p < 0.05/n_pairs else ""
    print(f"    {a:8s} -> {b:8s}  korr {r:+.3f}  p={p:.2e}{flag}")

print()
print("=" * 108)
print("B) OUT-OF-SAMPLE: leia 1. poolel, kontrolli 2. poolel")
print("=" * 108)
in_sample = []
for a in syms:
    for b in syms:
        if a == b: continue
        x = rets[a].shift(1).iloc[1:mid]
        y = rets[b].iloc[1:mid]
        m = x.notna() & y.notna()
        if m.sum() < 150: continue
        r, p = stats.pearsonr(x[m], y[m])
        if p < 0.05/n_pairs:   # ainult Bonferroni-tugevad
            in_sample.append((a, b, r, p))

print(f"  1. poolel Bonferroni-tugevaid seoseid: {len(in_sample)}")
if in_sample:
    print(f"\n  {'paar':22s} {'1.pool korr':>12s} {'2.pool korr':>12s} {'2.pool p':>10s}  püsib?")
    survived = 0
    for a, b, r1, p1 in in_sample:
        x = rets[a].shift(1).iloc[mid:]
        y = rets[b].iloc[mid:]
        m = x.notna() & y.notna()
        r2, p2 = stats.pearsonr(x[m], y[m])
        ok = (p2 < 0.05) and (np.sign(r2) == np.sign(r1))
        survived += ok
        print(f"  {a+' -> '+b:22s} {r1:+12.3f} {r2:+12.3f} {p2:10.3f}  "
              f"{'JAH' if ok else 'ei'}")
    print(f"\n  Out-of-sample püsis: {survived}/{len(in_sample)}")
else:
    print("  Ühtegi Bonferroni-tugevat seost 1. poolel ei leitud.")
