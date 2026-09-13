"""
SUVAKAEVAMINE: ainus kandidaat + kasutaja oma idee + uudiste-puhver.

SOELAST JAI JARELE:
  WTI "Aasia->London murre", 24h horisont: +24.17bp neto, ja mis
  tahtsam, +22.66bp ULE lihtsalt-ole-pikk tulu. 234 tehingut aastas.
  Koik teised tipud olid pikk-positsiooni varjus.

KASUTAJA IDEE, mida soel ei testinud tapselt:
  "puua hinnaga kaasa minna ja mitte paris algusest vaid siis kui on
   naha et liigub sinna poole"
  = KINNITUSEGA sisenemine. Mitte esimese murde peal, vaid siis kui
  murre on PUSINUD. Testime: N jarjestikust baari suunas, murre
  hoiab k baari, ATR-i ulatus kinnitab.

UUDISED ilma uudisvooguta:
  Meil ei ole uudistekalendrit. AGA uudise KAUBELDAV jalg on
  volatiilsuse hupe. Testime, kas kauplemine volatiilsuse hupete
  ajal / nende valtimine muudab midagi.
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import h1engine as E

rng = np.random.default_rng(1409)
OUT = "h1_syva_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

D = E.lae_koik()


def sess_murre(d, a_algus=0, a_lopp=7, k_algus=7, k_lopp=16, kinnitus=0):
    """Aasia vahemik murtakse kauplemisaknas. kinnitus = mitu baari peab hoidma."""
    c, h, l = d["close"], d["high"], d["low"]
    tund = d.index.hour
    grp = pd.Series(d.index.normalize(), index=d.index)
    vahe = (tund >= a_algus) & (tund < a_lopp)
    hi = h.where(vahe).groupby(grp).transform("max")
    lo = l.where(vahe).groupby(grp).transform("min")
    aken = (tund >= k_algus) & (tund < k_lopp)
    up = (c > hi) & aken
    dn = (c < lo) & aken
    if kinnitus > 0:
        up = up & (c > hi).rolling(kinnitus + 1).sum().eq(kinnitus + 1)
        dn = dn & (c < lo).rolling(kinnitus + 1).sum().eq(kinnitus + 1)
    sg = (up.astype(float) - dn.astype(float)).fillna(0.0)
    esim = sg.ne(0) & (~sg.ne(0).groupby(grp).cumsum().gt(1))
    return sg.where(esim, 0.0)


# ══ 1) WTI SESSIOONIMURRE — kas peab vett? ══════════════════════
w("=" * 100)
w("1) WTI SESSIOONIMURRE — ainus kandidaat, mis ületas 'ole-pikk' võrdlusaluse")
w("=" * 100)
d = D["WTI"]
kr, ke = E.KULU_RETAIL["WTI"], E.KULU_ECN["WTI"]
sg = sess_murre(d)
y = E.tulevik(d, 24)
r = E.hinda(sg, y, kr)
w(f"   tehinguid {r['n']}  ({r['teh_aastas']:.0f}/aastas)")
w(f"   keskmine {1e4*r['keskm']:+.2f}bp   t={r['tstat']:+.2f}   võit% {r['wr']:.1f}")
w(f"   1. pool {1e4*r['p1']:+.2f}bp   2. pool {1e4*r['p2']:+.2f}bp")

# libisev aken — kas STABIILNE?
w("")
w("   LIBISEV AKEN (6 kuud kaupa) — kas serv on püsiv või ühe perioodi nähtus?")
t_all = pd.Series(r["t"], index=sg[sg != 0].index[:len(r["t"])])
for per, g in t_all.groupby(pd.Grouper(freq="6MS")):
    if len(g) < 20:
        continue
    w(f"      {str(per.date()):>11s}: {len(g):4d} teh  {1e4*g.mean():+8.2f}bp  "
      f"{'PLUSS' if g.mean() > 0 else 'miinus'}")

# null-jaotus
nz = sg != 0
ok = 0
for _ in range(200):
    v = pd.Series(0.0, index=sg.index)
    v[nz] = rng.choice([-1.0, 1.0], size=int(nz.sum()))
    rr = E.hinda(v, y, kr)
    if rr and rr["keskm"] >= r["keskm"]:
        ok += 1
w("")
w(f"   NULL (200 katset, juhuslik suund): p = {ok/200:.3f}")

# kas teistel instrumentidel ka?
w("")
w("   SAMA REEGEL TEISTEL INSTRUMENTIDEL (kas üldistub või on WTI-eripära?):")
w(f"      {'instr':8s} {'teh/a':>7s} {'keskm bp':>10s} {'t':>7s} {'1.pool':>9s} {'2.pool':>9s}")
w("      " + "-" * 56)
uld = []
for s2, d2 in D.items():
    r2 = E.hinda(sess_murre(d2), E.tulevik(d2, 24), E.KULU_RETAIL.get(s2, 2.0))
    if r2 is None:
        continue
    uld.append(r2["keskm"])
    w(f"      {s2:8s} {r2['teh_aastas']:7.0f} {1e4*r2['keskm']:+10.2f} "
      f"{r2['tstat']:+7.2f} {1e4*r2['p1']:+9.2f} {1e4*r2['p2']:+9.2f}")
w(f"      => plussis {sum(1 for x in uld if x>0)}/{len(uld)}, "
  f"keskmine {1e4*np.mean(uld):+.2f}bp")

# ══ 2) KASUTAJA IDEE: KINNITUSEGA SISENEMINE ════════════════════
w("")
w("=" * 100)
w("2) KASUTAJA IDEE — 'mitte päris algusest, vaid kui on näha et liigub sinna poole'")
w("=" * 100)
w("   Test: nõua, et murre PÜSIKS k baari enne sisenemist.")
w(f"   {'instr':8s} {'kinnitus':>9s} {'teh/a':>7s} {'keskm bp':>10s} {'t':>7s}")
w("   " + "-" * 48)
kinn_kokku = {0: [], 1: [], 2: [], 3: []}
for s2, d2 in D.items():
    for k in (0, 1, 2, 3):
        r2 = E.hinda(sess_murre(d2, kinnitus=k), E.tulevik(d2, 24),
                     E.KULU_RETAIL.get(s2, 2.0))
        if r2 is None:
            continue
        kinn_kokku[k].append(r2["keskm"])
        if s2 in ("WTI", "XAUUSD", "EURUSD", "GBPUSD"):
            w(f"   {s2:8s} {k:9d} {r2['teh_aastas']:7.0f} "
              f"{1e4*r2['keskm']:+10.2f} {r2['tstat']:+7.2f}")
w("")
w("   KÕIGI instrumentide keskmine kinnituse taseme kaupa:")
for k, v in kinn_kokku.items():
    if v:
        w(f"      kinnitus {k} baari: keskm {1e4*np.mean(v):+7.2f}bp   "
          f"plussis {sum(1 for x in v if x>0)}/{len(v)}")

# jarjestikused baarid samas suunas
w("")
w("   Teine kinnituse vorm: N järjestikust baari samas suunas, siis kaasa.")
w(f"   {'N baari':>8s} {'instr-e plussis':>16s} {'keskm bp':>10s} {'teh/a keskm':>12s}")
w("   " + "-" * 50)
for n_b in (2, 3, 4, 5):
    vs, ta = [], []
    for s2, d2 in D.items():
        c = d2["close"]
        r1 = c / c.shift(1) - 1
        up = (r1 > 0).rolling(n_b).sum().eq(n_b)
        dn = (r1 < 0).rolling(n_b).sum().eq(n_b)
        sg2 = (up.astype(float) - dn.astype(float)).fillna(0.0)
        r2 = E.hinda(sg2, E.tulevik(d2, 4), E.KULU_RETAIL.get(s2, 2.0))
        if r2:
            vs.append(r2["keskm"]); ta.append(r2["teh_aastas"])
    if vs:
        w(f"   {n_b:8d} {sum(1 for x in vs if x>0):8d}/{len(vs):<7d} "
          f"{1e4*np.mean(vs):+10.2f} {np.mean(ta):12.0f}")

# ══ 3) VOLATIILSUS = UUDISTE JÄLG ═══════════════════════════════
w("")
w("=" * 100)
w("3) UUDISED ILMA UUDISVOOTA — volatiilsuse hüpe on uudise kaubeldav jälg")
w("=" * 100)
w("   Kas kauplemine volatiilsuse hüppe ajal on parem või halvem?")
w(f"   {'režiim':>22s} {'instr-e plussis':>16s} {'keskm bp':>10s} {'teh/a':>9s}")
w("   " + "-" * 60)
for nimi, f_ in (("KÕRGE vol (top 20%)", "korge"), ("MADAL vol (alum 20%)", "madal"),
                 ("kõik baarid", "koik")):
    vs, ta = [], []
    for s2, d2 in D.items():
        c, h, l = d2["close"], d2["high"], d2["low"]
        a = E.atr(d2, 14)
        rel = a / a.rolling(240).mean()
        up = c >= h.rolling(24).max().shift(1)
        dn = c <= l.rolling(24).min().shift(1)
        sg2 = (up.astype(float) - dn.astype(float)).fillna(0.0)
        if f_ == "korge":
            sg2 = sg2.where(rel > rel.rolling(480).quantile(0.80), 0.0)
        elif f_ == "madal":
            sg2 = sg2.where(rel < rel.rolling(480).quantile(0.20), 0.0)
        r2 = E.hinda(sg2, E.tulevik(d2, 8), E.KULU_RETAIL.get(s2, 2.0))
        if r2:
            vs.append(r2["keskm"]); ta.append(r2["teh_aastas"])
    if vs:
        w(f"   {nimi:>22s} {sum(1 for x in vs if x>0):8d}/{len(vs):<7d} "
          f"{1e4*np.mean(vs):+10.2f} {np.mean(ta):9.0f}")
w("VALMIS")
