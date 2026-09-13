"""
EELMISE TESTI KAHE VEA PARANDUS.

VIGA 1 — EBAAUS BASELINE. Ma vordlesin PARIMAT 252 variandi seast
uhe juhusliku sisenemisega. Parim-252-st on ulespuhutud valikunihke
tottu; uksik juhuslik ei ole. Oige vordlus: juhuslik peab labima
SAMA valikuprotsessi — genereeri sama palju juhuslikke variante ja
vota nende parim. Alles siis on "parem kui juhuslik" midagi vaart.

VIGA 2 — nan keskmises. Mitmel paaril oli FINAL OOS aknas 0 tehingut,
mis andis nan ja rikkus kokkuvotte. Pohjus: H1-baaridel tulistavad
tagasitomme/retest tingimused harva (1.3-3.8 tehingut kuus). PDF
naeb ette 15m sisenemist, mida mul ei ole.

LISAKS: kui signaalis ON informatsiooni (ka siis, kui kulud selle ara
soovad), siis see peab paistma BRUTO numbrites. Vaatame mollemaid.
"""
import warnings; warnings.filterwarnings("ignore")
import itertools
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P, paar_config as C
from run_paarid import variandid, signaal

rng = np.random.default_rng(2609)
OUT = "paarid_aus_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

df = pd.read_csv("data/paarid.csv")

w("=" * 100)
w("1) AUS BASELINE — juhuslik läbib SAMA valikuprotsessi (parim N seast)")
w("=" * 100)
w(f"   {'paar':8s} {'var':>4s} {'strat BRUTO':>12s} {'juhu BRUTO':>11s} {'vahe':>8s} "
  f"{'strat NETO':>11s} {'juhu NETO':>10s} {'vahe':>8s}")
w("   " + "-" * 78)
tul = []
for sym, cfg in C.PAARID.items():
    g = df[df["sym"] == sym]
    if not len(g):
        continue
    d = E.lae(sym)
    ind = P.valmista(d)
    kulu = E.KULU_RETAIL.get(sym, 1.5)
    sess = C.SESS[cfg["sess"]]
    nvar = len(g)
    # PARIS: parim NETO ja selle bruto
    r = g.loc[g["ootus"].idxmax()]
    # brutо parimast netost
    sg = signaal(d, cfg, dict(tuup=r["tuup"], adx=r["adx"],
                              retest=bool(r["retest"]) if pd.notna(r["retest"]) else True),
                 ind)
    t = P.simuleeri(d, sg, r["sl"], r["tp"], kulu, ind, sess)
    s_bruto = float(t["bruto"].mean()) if len(t) else np.nan
    # JUHUSLIK: sama arv variante, vota PARIM
    n = len(d)
    j_neto, j_bruto = [], []
    for _ in range(nvar):
        m = max(int(r["n"]), 30)
        idx = rng.choice(np.arange(250, n - 1), size=m, replace=False)
        s2 = pd.Series(0.0, index=d.index)
        s2.iloc[np.sort(idx)] = rng.choice([-1.0, 1.0], size=m)
        t2 = P.simuleeri(d, s2, r["sl"], r["tp"], kulu, ind, sess)
        if t2 is None or len(t2) < 20:
            continue
        j_neto.append(float(t2["tulem"].mean()))
        j_bruto.append(float(t2["bruto"].mean()))
    if not j_neto:
        continue
    jb, jn = max(j_bruto), max(j_neto)      # PARIM juhuslikest, nagu strateegiagi
    tul.append((sym, s_bruto - jb, r["ootus"] - jn))
    w(f"   {sym:8s} {nvar:4d} {1e4*s_bruto:+11.1f} {1e4*jb:+10.1f} "
      f"{1e4*(s_bruto-jb):+7.1f} {1e4*r['ootus']:+10.1f} {1e4*jn:+9.1f} "
      f"{1e4*(r['ootus']-jn):+7.1f}")

w("")
bp = sum(1 for _, b, _ in tul if b > 0)
np_ = sum(1 for _, _, n_ in tul if n_ > 0)
w(f"   AUSAS võrdluses juhuslikust parem:  BRUTO {bp}/{len(tul)}   NETO {np_}/{len(tul)}")
w(f"   keskmine vahe: BRUTO {1e4*np.mean([b for _,b,_ in tul]):+.1f}bp   "
  f"NETO {1e4*np.mean([n_ for _,_,n_ in tul]):+.1f}bp")
w("")
w("   Eelmine test ütles '11/15 parem'. See võrdles parimat 252-st ÜHE")
w("   juhuslikuga. Kui juhuslik läbib sama valiku, on pilt ülal.")

# ══ 2) 60/20/20 ILMA nan-ita ════════════════════════════════════
w("")
w("=" * 100)
w("2) 60/20/20 PROTOKOLL — ainult paarid, kus FINAL OOS aknas on tehinguid")
w("=" * 100)
w(f"   {'paar':8s} {'A (valik)':>11s} {'B (valid.)':>11s} {'C (FINAL OOS)':>14s} {'C teh':>7s}")
w("   " + "-" * 56)
cc, npos = [], 0
for sym in C.PAARID:
    g = df[(df["sym"] == sym) & (df["nA"] >= 15)]
    if not len(g):
        continue
    r = g.loc[g["A"].idxmax()]
    if not (r["nC"] >= 15 and np.isfinite(r["Cc"])):
        continue
    cc.append(r["Cc"]); npos += (r["Cc"] > 0)
    w(f"   {sym:8s} {1e4*r['A']:+10.1f} {1e4*r['B']:+10.1f} "
      f"{1e4*r['Cc']:+13.1f} {int(r['nC']):7d}{'  <<<' if r['Cc']>0 else ''}")
w("")
w(f"   FINAL OOS plussis {npos}/{len(cc)}, keskmine {1e4*np.mean(cc):+.1f}bp")

# ══ 3) KAS SIGNAALIS ON ÜLDSE INFOT? (bruto, ilma valikuta) ════
w("")
w("=" * 100)
w("3) KAS SIGNAALIS ON INFOT? — KÕIK 252 varianti, bruto (ilma kuludeta)")
w("=" * 100)
w("   Kui signaalil on väärtus, peab bruto-ootus olema süstemaatiliselt > 0,")
w("   ka siis kui kulud selle ära söövad. Ilma valikuta, kõik variandid.")
w("")
# arvuta bruto koigile
bruto_koik = []
for sym, cfg in C.PAARID.items():
    d = E.lae(sym)
    if d is None: continue
    ind = P.valmista(d)
    kulu = E.KULU_RETAIL.get(sym, 1.5)
    sess = C.SESS[cfg["sess"]]
    for v in variandid(sym, cfg):
        sg = signaal(d, cfg, v, ind)
        if int((sg != 0).sum()) < 40: continue
        t = P.simuleeri(d, sg, v["sl"], v["tp"], kulu, ind, sess)
        if t is None or len(t) < 30: continue
        bruto_koik.append(dict(sym=sym, rezim=cfg["rezim"],
                               bruto=float(t["bruto"].mean()),
                               neto=float(t["tulem"].mean()), n=len(t)))
bk = pd.DataFrame(bruto_koik)
w(f"   {'režiim':18s} {'variante':>9s} {'BRUTO>0':>9s} {'keskm BRUTO':>12s} "
  f"{'NETO>0':>8s} {'keskm NETO':>11s} {'kulu':>7s}")
w("   " + "-" * 78)
for rz, g in bk.groupby("rezim"):
    w(f"   {rz:18s} {len(g):9d} {100*(g['bruto']>0).mean():8.1f}% "
      f"{1e4*g['bruto'].mean():+12.1f} {100*(g['neto']>0).mean():7.1f}% "
      f"{1e4*g['neto'].mean():+11.1f} {1e4*(g['bruto']-g['neto']).mean():6.1f}")
w("   " + "-" * 78)
w(f"   {'KOKKU':18s} {len(bk):9d} {100*(bk['bruto']>0).mean():8.1f}% "
  f"{1e4*bk['bruto'].mean():+12.1f} {100*(bk['neto']>0).mean():7.1f}% "
  f"{1e4*bk['neto'].mean():+11.1f} {1e4*(bk['bruto']-bk['neto']).mean():6.1f}")

w("")
w("=" * 100)
w("4) TEHINGUTE SAGEDUS — kas PDF-i setupid üldse tulistavad piisavalt?")
w("=" * 100)
w(f"   {'paar':8s} {'tehinguid':>10s} {'kuus':>7s} {'PDF ootus':>25s}")
w("   " + "-" * 54)
for sym in C.PAARID:
    g = df[df["sym"] == sym]
    if not len(g): continue
    w(f"   {sym:8s} {int(g['n'].median()):10d} {g['teh_kuus'].median():7.1f} "
      f"{'(PDF: 15m entry, mul 1H)':>25s}")
w("")
w("   PDF näeb ette 1H trendi + 15m sisenemist. Mul on ainult 1H, seega")
w("   setup tulistab harvem. See vähendab statistilist võimekust, aga EI")
w("   muuda suunda: bruto-ootus on ülal ja see ei sõltu sagedusest.")
w("VALMIS")
