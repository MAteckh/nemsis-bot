"""
KOIK 14 REGISTREERITUD HUPOTEESI, TAIS PROTOKOLL.

Iga huopotees saab: TRAIN / VALIDATION / FINAL OOS eraldi, kolm kulutaset.
FINAL OOS-i ei kasutata uhegi valiku tegemiseks.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import v5_engine as V
from v5_registry import REGISTER

OUT = "v5_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

P, IX = V.paarid_df()
S = V.valuuta_tootlused(P)          # paev x valuuta, tootlus vs korv
C = V.carry_diff()                  # intressivahe
VAL = list(S.columns)

# keskmine uhesuunaline kulu paari kohta, kulutaseme kaupa
KESK = {k: float(np.mean(list(v.values()))) for k, v in V.KULU.items()}


def korv_tootlus(skoor, k=2, kulu_tase="BASE", rebal=1):
    """
    LONG top-k valuutat, SHORT bottom-k. Kaalud summeeruvad nulli.
    Kulu: iga kaalumuutus noiab paari kauplemist. Uks paar puudutab
    KAHTE valuutat, seega kulu = (kaalude muutuse summa / 2) x 2 x kulu_bp.
    """
    sk = skoor.dropna(how="all")
    if len(sk) < 100:
        return None
    Wt = pd.DataFrame(0.0, index=sk.index, columns=sk.columns)
    for t, rida in sk.iterrows():
        r = rida.dropna()
        if len(r) < 2 * k:
            continue
        jarj = r.sort_values(ascending=False)
        Wt.loc[t, jarj.index[:k]] = 1.0 / k
        Wt.loc[t, jarj.index[-k:]] = -1.0 / k
    if rebal > 1:                                 # harvem rebalanss
        Wt = Wt.iloc[::rebal].reindex(Wt.index, method="ffill")
    # kaal teada paeva t lopus, teenib paeva t+1 tootluse
    Wp = Wt.shift(1).fillna(0.0)
    ix = Wp.index.intersection(S.index)
    bruto = (Wp.reindex(ix) * S.reindex(ix)).sum(axis=1)
    kaibe = Wp.reindex(ix).diff().abs().sum(axis=1).fillna(0.0)
    kulu = kaibe * KESK[kulu_tase] / 1e4
    return (bruto - kulu).rename("neto"), bruto.rename("bruto")


def rida(hid, nimi, seeria, w_fn=w):
    if seeria is None:
        w_fn(f"  {hid} {nimi:16s}  liiga vähe andmeid"); return None
    tr, va, fo = V.jaota(seeria)
    m = lambda x: V.moodikud(x)
    a, b, c = m(tr), m(va), m(fo)
    if a is None:
        w_fn(f"  {hid} {nimi:16s}  liiga vähe andmeid"); return None
    f = lambda d: (f"{1e4*d['keskm']:+7.2f} {d['sh']:+6.2f}" if d else "    -      - ")
    w_fn(f"  {hid} {nimi:16s} {f(a)} | {f(b)} | {f(c)}")
    return dict(id=hid, nimi=nimi, train=a, valid=b, oos=c, seeria=seeria)


w("=" * 104)
w("NEMSIS v5 — 14 EELREGISTREERITUD HÜPOTEESI")
w("=" * 104)
w(f"  andmed {IX[0].date()} .. {IX[-1].date()}, {len(IX)} päeva, 8 valuutat, 8 paari")
w(f"  TRAIN kuni {V.TRAIN_LOPP.date()} | VALID kuni {V.VALID_LOPP.date()} | FINAL OOS pärast")
w("  kulud: BASE tase (retail). Arvud: keskm bp/päev ja Sharpe.")
w("")
w(f"  {'ID':4s} {'hüpotees':16s} {'TRAIN':>15s} | {'VALIDATION':>14s} | {'FINAL OOS':>14s}")
w("  " + "-" * 72)

R = []
# ── H01-H04 ristloikeline momentum ──────────────────────────────
for hid, lb in (("H01", 1), ("H02", 5), ("H03", 20), ("H04", 60)):
    skoor = S.rolling(lb).sum()
    n, br = korv_tootlus(skoor)
    r = rida(hid, f"CS-MOM-{lb}D", n)
    if r: r["bruto"] = br; R.append(r)

# ── H05 carry ───────────────────────────────────────────────────
carry_sk = C.reindex(S.index).ffill().rolling(60).mean()   # silutud jarjestus
n, br = korv_tootlus(carry_sk)
r = rida("H05", "CS-CARRY", n)
if r: r["bruto"] = br; R.append(r)

# ── H06 carry + momentum ────────────────────────────────────────
z = lambda d: d.sub(d.mean(axis=1), axis=0).div(d.std(axis=1).replace(0, np.nan), axis=0)
liit = z(carry_sk).add(z(S.rolling(20).sum()), fill_value=0)
n, br = korv_tootlus(liit)
r = rida("H06", "CS-CARRY+MOM", n)
if r: r["bruto"] = br; R.append(r)

# ── H07 time-series momentum, mitu horisonti ────────────────────
haal = sum(np.sign(S.rolling(lb).sum()) for lb in (1, 5, 20, 60, 120))
Wt = (np.sign(haal) / 8.0).shift(1).fillna(0.0)
ix = Wt.index.intersection(S.index)
bruto = (Wt.reindex(ix) * S.reindex(ix)).sum(axis=1)
kulu = Wt.reindex(ix).diff().abs().sum(axis=1).fillna(0) * KESK["BASE"] / 1e4
r = rida("H07", "TS-MOM-MULTI", (bruto - kulu))
if r: r["bruto"] = bruto; R.append(r)

# ── H08 momentumi kiirendus ─────────────────────────────────────
mom20 = S.rolling(20).sum()
n, br = korv_tootlus(mom20 - mom20.shift(20))
r = rida("H08", "MOM-ACCEL", n)
if r: r["bruto"] = br; R.append(r)

# ── H09 momentumi pusivus ───────────────────────────────────────
n, br = korv_tootlus((S > 0).rolling(20).mean())
r = rida("H09", "MOM-PERSIST", n)
if r: r["bruto"] = br; R.append(r)

# ── H10 overnight vs paevasisene ────────────────────────────────
w("")
w("  H10 OVERNIGHT — mitte korv, vaid paaride kaupa (vt allpool eraldi tabel)")
on_read = []
for p, d in P.items():
    o2c = (d["close"] / d["open"] - 1)
    c2o = (d["open"] / d["close"].shift(1) - 1)
    on_read.append(dict(paar=p, c2o=float(c2o.mean()), o2c=float(o2c.mean()),
                        c2o_sh=V.sharpe(c2o.dropna()), o2c_sh=V.sharpe(o2c.dropna())))

# ── H11 nadalapaev ──────────────────────────────────────────────
wd_read = []
for wd, nm in enumerate(["E", "T", "K", "N", "R"]):
    x = S.mean(axis=1) * 0  # placeholder, arvutame paaride keskmisena
    v = []
    for p, d in P.items():
        r1 = d["close"].pct_change()
        v.append(float(r1[r1.index.dayofweek == wd].mean()))
    wd_read.append((nm, float(np.mean(v))))

# ── H12 kuu lopp ────────────────────────────────────────────────
kuu_read = []
for nm, fn in (("kuu viimased 3", lambda i: i.to_series().groupby([i.year, i.month]).transform(
                    lambda g: g.rank(ascending=False) <= 3).values),
               ("kuu esimesed 3", lambda i: i.to_series().groupby([i.year, i.month]).transform(
                    lambda g: g.rank() <= 3).values)):
    v = []
    for p, d in P.items():
        r1 = d["close"].pct_change()
        m = fn(d.index)
        v.append(float(r1[m].mean()))
    kuu_read.append((nm, float(np.mean(v))))

# ── H13 kolmnurk ────────────────────────────────────────────────
eg = V.lae("EURGBP")
tri = None
if eg is not None:
    ixt = P["EURUSD"].index.intersection(P["GBPUSD"].index).intersection(eg.index)
    jaak = (np.log(P["EURUSD"]["close"].reindex(ixt))
            - np.log(P["GBPUSD"]["close"].reindex(ixt))
            - np.log(eg["close"].reindex(ixt)))
    zz = (jaak - jaak.rolling(60).mean()) / jaak.rolling(60).std()
    sg = (-np.sign(zz) * (zz.abs() > 1.5)).shift(1).fillna(0.0)
    rr = jaak.diff().shift(-1)
    kulu = sg.diff().abs().fillna(0) * 3 * KESK["BASE"] / 1e4   # 3 paari!
    tri = (sg * rr - kulu).dropna()
r = rida("H13", "RELVAL-TRI", tri)
if r: r["bruto"] = tri; R.append(r)

# ── H14 AUD/NZD spread ──────────────────────────────────────────
ixa = P["AUDUSD"].index.intersection(P["NZDUSD"].index)
spr = np.log(P["AUDUSD"]["close"].reindex(ixa)) - np.log(P["NZDUSD"]["close"].reindex(ixa))
zz = (spr - spr.rolling(60).mean()) / spr.rolling(60).std()
sg = (-np.sign(zz) * (zz.abs() > 1.5)).shift(1).fillna(0.0)
rr = spr.diff().shift(-1)
kulu = sg.diff().abs().fillna(0) * 2 * KESK["BASE"] / 1e4
r = rida("H14", "RELVAL-AUDNZD", (sg * rr - kulu).dropna())
if r: r["bruto"] = (sg * rr); R.append(r)

# ══ H10-H12 TABELID ════════════════════════════════════════════
w("")
w("=" * 104)
w("H10 OVERNIGHT — close-to-open vs open-to-close, paaride kaupa (bp/päev, ILMA kuludeta)")
w("=" * 104)
w(f"  {'paar':8s} {'close→open':>12s} {'Sharpe':>8s} {'open→close':>12s} {'Sharpe':>8s} {'vahe':>9s}")
w("  " + "-" * 62)
for r_ in on_read:
    w(f"  {r_['paar']:8s} {1e4*r_['c2o']:+11.2f} {r_['c2o_sh']:+8.2f} "
      f"{1e4*r_['o2c']:+11.2f} {r_['o2c_sh']:+8.2f} {1e4*(r_['c2o']-r_['o2c']):+8.2f}")
w(f"  keskmine c→o {1e4*np.mean([x['c2o'] for x in on_read]):+.2f}bp, "
  f"o→c {1e4*np.mean([x['o2c'] for x in on_read]):+.2f}bp   "
  f"(edasi-tagasi kulu {2*KESK['BASE']:.1f}bp)")

w("")
w("=" * 104)
w("H11 NÄDALAPÄEV / H12 KUU VAHETUS — keskmine päevatootlus (bp, ILMA kuludeta)")
w("=" * 104)
w("  " + "  ".join(f"{nm}: {1e4*v:+.2f}bp" for nm, v in wd_read))
w("  " + "  ".join(f"{nm}: {1e4*v:+.2f}bp" for nm, v in kuu_read))
w(f"  Võrdluseks: edasi-tagasi kulu on {2*KESK['BASE']:.1f}bp. Ükski ülaltoodust ei kata seda.")

# ══ KULUTUNDLIKKUS ═════════════════════════════════════════════
w("")
w("=" * 104)
w("KULUTUNDLIKKUS (Phase 6) — korvistrateegiad kolmel kulutasemel, KOGU periood")
w("=" * 104)
w(f"  {'ID':4s} {'hüpotees':16s} {'BRUTO':>9s} {'LOW':>9s} {'BASE':>9s} {'HIGH':>9s} {'hinnang':>12s}")
w("  " + "-" * 68)
for hid, lb in (("H01",1),("H02",5),("H03",20),("H04",60)):
    sk = S.rolling(lb).sum()
    vals = {}
    for kt in ("LOW","BASE","HIGH"):
        n_, br_ = korv_tootlus(sk, kulu_tase=kt)
        vals[kt] = 1e4*float(n_.mean()); vals["BRUTO"] = 1e4*float(br_.mean())
    hinn = "robustne" if vals["HIGH"] > 0 else ("FRAGIILNE" if vals["LOW"] > 0 else "kaotaja")
    w(f"  {hid} {'CS-MOM-'+str(lb)+'D':16s} {vals['BRUTO']:+8.2f} {vals['LOW']:+8.2f} "
      f"{vals['BASE']:+8.2f} {vals['HIGH']:+8.2f} {hinn:>12s}")
for hid, sk, nm in (("H05", carry_sk, "CS-CARRY"), ("H06", liit, "CS-CARRY+MOM")):
    vals = {}
    for kt in ("LOW","BASE","HIGH"):
        n_, br_ = korv_tootlus(sk, kulu_tase=kt)
        vals[kt] = 1e4*float(n_.mean()); vals["BRUTO"] = 1e4*float(br_.mean())
    hinn = "robustne" if vals["HIGH"] > 0 else ("FRAGIILNE" if vals["LOW"] > 0 else "kaotaja")
    w(f"  {hid} {nm:16s} {vals['BRUTO']:+8.2f} {vals['LOW']:+8.2f} "
      f"{vals['BASE']:+8.2f} {vals['HIGH']:+8.2f} {hinn:>12s}")

import pickle
with open("data/v5_tulemused.pkl", "wb") as f:
    pickle.dump({r["id"]: {k: r[k] for k in ("id","nimi","seeria")} for r in R}, f)
w("")
w(f"tulemused salvestatud: data/v5_tulemused.pkl ({len(R)} hüpoteesi)")
w("VALMIS")
