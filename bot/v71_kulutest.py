"""
v7.1 — LOW-COST EXECUTION STRESS TEST.

EI OLE uus strateegiaotsing. Uks kusimus:
  kas v7 selektiivne +1.83bp bruto serv on piisavalt tugev, et
  realistlike MADALATE kuludega muutuda pariselt positiivseks?

SIGNAAL ON TAPSELT SAMA MIS v7-s, MUUTMATA:
  murre : c > 24h max (shift 1)  voi  c < 24h min (shift 1)
  filter: trendi joondus (sign(sg) == sign(EMA50-EMA200))
          JA suhteline tugevus kooskolas (sign(sg)*sign(rs_z) > 0)
          JA ATR laienemine > 1.2  (atr / atr.rolling(240).mean())
  entry : baar i+1 avanemine
  exit  : baar i+8 sulgemine
Ainus muutus: UNIVERSUM = ainult 7 majorit, ristpaarid valjas.

AUS PIIRANG, mis tuleb valja oelda (kasutaja punkt 5):
Mul EI OLE tick- ega bid/ask-andmeid, seega ma EI SAA teha ajas muutuvat
spread-filtrit ("kauple ainult kui spread <= 0.75bp"). Minu kulumudel on
paari kohta FIKSEERITUD. Seetottu asendan spread-filtri sellega, mida
saab ausalt teha: PAARIPOHINE MURDEPUNKT — millise kulu juures iga paar
eraldi nulli laheb. See vastab samale kusimusele ilma andmeid leiutamata.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "v71_kulutest.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

MAJORID = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD"]
# valuutatugevus tuleb tuletada LAIEMAST korvist, muidu pole ristloiget
KOIK22 = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
          "EURGBP","EURJPY","EURCHF","EURAUD","EURNZD","GBPJPY","GBPCHF",
          "GBPAUD","GBPCAD","AUDJPY","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"]
DA = {s: E.lae(s) for s in KOIK22}
DA = {k: v for k, v in DA.items() if v is not None}
BAAS = {p: (p[:3], p[3:]) for p in DA}

def valuuta_tugevus():
    r = {p: np.log(d["close"]).diff() for p, d in DA.items()}
    R = pd.DataFrame(r).dropna()
    val = sorted({c for p in DA for c in BAAS[p]})
    idx = {c: i for i, c in enumerate(val)}
    A = np.zeros((len(DA)+1, len(val)))
    for j, p in enumerate(DA):
        b, q = BAAS[p]; A[j, idx[b]] = 1.0; A[j, idx[q]] = -1.0
    A[-1, :] = 1.0
    Y = np.column_stack([R[p].values for p in DA] + [np.zeros(len(R))])
    return pd.DataFrame(Y @ np.linalg.pinv(A).T, index=R.index, columns=val)

TUG = valuuta_tugevus()

# ── ehita v7 signaalid, AINULT majoritel ───────────────────────
read = []
for sym in MAJORID:
    d = DA.get(sym)
    if d is None: continue
    ind = P.valmista(d)
    c, h, l, o = d["close"], d["high"], d["low"], d["open"]
    a = ind["atr"]
    b, q = BAAS[sym]
    hi = h.rolling(24).max().shift(1); lo = l.rolling(24).min().shift(1)
    up, dn = c > hi, c < lo
    sg = up.astype(float) - dn.astype(float)
    atr_exp = (a / a.rolling(240).mean()).fillna(1.0)
    ef, es = c.ewm(span=50).mean(), c.ewm(span=200).mean()
    joondus = (np.sign(sg) == np.sign(ef - es)).astype(float)
    ts = TUG.reindex(d.index).ffill()
    rs = (ts[b].rolling(120).sum() - ts[q].rolling(120).sum())
    rs_z = (rs / rs.rolling(480).std()).fillna(0.0)
    rs_ok = (np.sign(sg) * np.sign(rs_z)).clip(lower=0)
    y = (c.shift(-8) / o.shift(-1) - 1)
    # v7 PARIM FILTER, muutmata
    m = ((sg != 0) & (joondus > 0.5) & (rs_ok > 0.5) & (atr_exp > 1.2)
         & y.notna() & a.notna() & (a > 0))
    if int(m.sum()) < 30: continue
    read.append(pd.DataFrame(dict(
        sym=sym, aeg=d.index[m], tund=d.index[m].hour,
        bruto=(np.sign(sg[m]) * y[m]).values)))
S = pd.concat(read, ignore_index=True)
S = S[np.isfinite(S["bruto"])].sort_values("aeg").reset_index(drop=True)

w("=" * 96)
w("v7.1 — KULUTUNDLIKKUSE STRESS-TEST (sama v7 signaal, ainult majorid)")
w("=" * 96)
w(f"  universum: {len(MAJORID)} majorit (ristpaarid VÄLJAS)")
w(f"  signaale: {len(S)}  (v7-s oli 3284 signaali 22 paari peale)")
w(f"  periood: {S['aeg'].min().date()} .. {S['aeg'].max().date()}")
aastaid = (S["aeg"].max() - S["aeg"].min()).days / 365.25
w(f"  ~{len(S)/aastaid:.0f} tehingut aastas kogu portfellis")
w("")
w(f"  BRUTO ootus: {1e4*float(S['bruto'].mean()):+.2f}bp   "
  f"(v7 22 paariga oli +1.83bp)")
w(f"  t-statistik: {float(S['bruto'].mean()/S['bruto'].std()*np.sqrt(len(S))):+.2f}")

# ══ 3) KULU-SWEEP ══════════════════════════════════════════════
w("")
w("=" * 96)
w("3) KULU-SWEEP — kogu kõver, mitte ainult parim punkt")
w("=" * 96)
w(f"  {'round-trip kulu':>17s} {'NETO bp':>10s} {'aastas %':>10s} {'hinnang':>12s}")
w("  " + "-" * 54)
br = float(S["bruto"].mean())
n_a = len(S) / aastaid
for kulu in np.arange(0.0, 3.51, 0.25):
    neto = br - kulu / 1e4
    w(f"  {kulu:>16.2f}bp {1e4*neto:+10.2f} {100*neto*n_a:+9.2f}% "
      f"{'PLUSS' if neto > 0 else 'miinus':>12s}")

# ══ 6) MURDEPUNKT ══════════════════════════════════════════════
be = 1e4 * br
w("")
w("=" * 96)
w("6) MURDEPUNKT")
w("=" * 96)
w(f"  BREAK-EVEN round-trip kulu = {be:.2f} bp")
w(f"  ehk {be/2:.2f} bp poole kohta.")
w("")
w("  VÕRDLUSEKS päris hinnakirjad (round-trip, EURUSD):")
w("    BlackBull ECN Prime (raw + $6/lot komisjon)   ~0.7-0.9 bp")
w("    BlackBull Standard (spread sees)              ~1.6-2.4 bp")
w("    minu BASE-mudel v4-v7-s                        2.0 bp")
w("    minu HIGH-mudel                                4.0 bp")

# ══ 4) SESSIOONIFILTER ═════════════════════════════════════════
w("")
w("=" * 96)
w("4) SESSIOONIFILTER (ainult 4 varianti, ei optimeeri kellaaegu)")
w("=" * 96)
SESS = {"kogu päev": (0, 24), "London": (7, 16), "New York": (13, 21),
        "LN/NY kattuvus": (13, 16)}
w(f"  {'sessioon':>16s} {'signaale':>10s} {'BRUTO bp':>10s} {'murdepunkt':>12s} "
  f"{'teh/aastas':>11s}")
w("  " + "-" * 64)
sess_tul = {}
for nimi, (h0, h1) in SESS.items():
    g = S[(S["tund"] >= h0) & (S["tund"] < h1)]
    if len(g) < 30:
        w(f"  {nimi:>16s} {len(g):10d}   liiga vähe"); continue
    b_ = float(g["bruto"].mean())
    sess_tul[nimi] = (len(g), b_)
    w(f"  {nimi:>16s} {len(g):10d} {1e4*b_:+10.2f} {1e4*b_:11.2f}bp "
      f"{len(g)/aastaid:10.0f}")

# ══ 5) PAARIPOHINE MURDEPUNKT (spread-filtri aus asendus) ══════
w("")
w("=" * 96)
w("5) PAARIPÕHINE MURDEPUNKT (spread-filtri aus asendus)")
w("=" * 96)
w("  Mul EI OLE tick/bid-ask andmeid => ajas muutuvat spread-filtrit ei saa")
w("  teha. Selle asemel: iga paari oma murdepunkt.")
w("")
w(f"  {'paar':>8s} {'signaale':>10s} {'BRUTO bp':>10s} {'murdepunkt':>12s} "
  f"{'t':>7s} {'teh/a':>8s}")
w("  " + "-" * 62)
for sym in MAJORID:
    g = S[S["sym"] == sym]
    if len(g) < 20:
        w(f"  {sym:>8s} {len(g):10d}   liiga vähe"); continue
    b_ = float(g["bruto"].mean())
    t_ = float(g["bruto"].mean()/g["bruto"].std()*np.sqrt(len(g))) if g["bruto"].std()>0 else 0
    w(f"  {sym:>8s} {len(g):10d} {1e4*b_:+10.2f} {1e4*b_:11.2f}bp {t_:+7.2f} "
      f"{len(g)/aastaid:7.0f}")

# ══ 7) WALK-FORWARD ════════════════════════════════════════════
w("")
w("=" * 96)
w("7) WALK-FORWARD — kas serv säilib OOS-is?")
w("=" * 96)
w("  H1-andmeid on 2023-11..2026-09 (~2.8 aastat), mitte 2016-2026.")
w("  Seega jaotan OLEMASOLEVA kolmeks võrdseks osaks, mitte ei teeskle")
w("  pikemat ajalugu.")
w("")
n3 = len(S) // 3
osad = [("TRAIN", S.iloc[:n3]), ("VALID", S.iloc[n3:2*n3]), ("FINAL OOS", S.iloc[2*n3:])]
w(f"  {'aken':>12s} {'periood':>26s} {'signaale':>10s} {'BRUTO bp':>10s} {'t':>7s}")
w("  " + "-" * 70)
for nimi, g in osad:
    b_ = float(g["bruto"].mean())
    t_ = float(g["bruto"].mean()/g["bruto"].std()*np.sqrt(len(g))) if g["bruto"].std()>0 else 0
    w(f"  {nimi:>12s} {str(g['aeg'].min().date())+'..'+str(g['aeg'].max().date()):>26s} "
      f"{len(g):10d} {1e4*b_:+10.2f} {t_:+7.2f}")
oos_b = float(osad[2][1]["bruto"].mean())
w("")
w(f"  FINAL OOS bruto: {1e4*oos_b:+.2f}bp  =>  murdepunkt OOS-is {1e4*oos_b:.2f}bp")

S.to_pickle("data/v71_signaalid.pkl")
w("")
w(f"  salvestatud: data/v71_signaalid.pkl")
w("VALMIS")
