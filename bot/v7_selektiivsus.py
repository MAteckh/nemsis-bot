"""
v7 OTSUSTAV TEST: KAS SELEKTIIVSUS TOSTAB SERVA?

KASUTAJA HUPOTEES: "paljude paaride skaneerimine + VAGA SELEKTIIVSED
entry'd + range risk annab parema riskiga korrigeeritud tulemuse."

MIKS SEE ON UUS KUSIMUS: v4-v6 testisid, mis juhtub, kui votta KOIK
signaalid. Selektiivsus tahendab votta ainult PARIMAD. Need on erinevad
asjad. Kui signaali kvaliteet on moodetav ja seotud realiseeruva
tulemusega, siis TOP-detsiil peab andma parema tulemuse kui keskmine.

SEE ON KOGU HUPOTEESI SUDA:
  kui TOP-detsiil >> keskmine  => selektiivsus tootab, ehita portfell
  kui TOP-detsiil ~ keskmine   => selektiivsus ei toota, portfell ei paasta

Miks portfell ei paasta, kui selektiivsus ei toota: hajutamine vahendab
HAJUVUST, mitte ei loo TOOTLUST. Kui iga komponendi oodatav vaartus on
negatiivne, on ka portfelli oma negatiivne — lihtsalt siledamalt.

KVALITEEDISKOOR — kasutaja punkt 7, iga komponent pohjendatud:
  ATR-i laienemine     — liikumine on "paris", mitte mura
  trendi joondus       — signaal on kordas suurema pildiga
  suhteline tugevus    — valuutapaar on ristloikes aarmuslik
  spread / ATR         — kulu on liikumise suhtes vaike
  murde selgus         — kui kaugele ule taseme mindi
KOIK arvutatud ENNE sisenemist, baari i sulgemise seisuga.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "v7_selektiivsus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

FX22 = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD",
        "EURGBP","EURJPY","EURCHF","EURAUD","EURNZD","GBPJPY","GBPCHF",
        "GBPAUD","GBPCAD","AUDJPY","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"]
KULU = {p: E.KULU_RETAIL.get(p, 1.8) for p in FX22}   # uhesuunaline bp
for p in ("EURNZD","GBPCHF","GBPCAD","AUDNZD","AUDCAD","NZDJPY","CADJPY","CHFJPY"):
    KULU[p] = 2.2                                      # ristpaarid kallimad

D = {s: E.lae(s) for s in FX22}
D = {k: v for k, v in D.items() if v is not None}
w(f"universum: {len(D)} FX-paari")
w(f"periood: {min(v.index[0] for v in D.values()).date()} .. "
  f"{max(v.index[-1] for v in D.values()).date()}")

# ── valuutatugevus ristloikeks ─────────────────────────────────
BAAS = {p: (p[:3], p[3:]) for p in D}
def valuuta_tugevus():
    r = {p: np.log(d["close"]).diff() for p, d in D.items()}
    R = pd.DataFrame(r).dropna()
    val = sorted({c for p in D for c in BAAS[p]})
    idx = {c: i for i, c in enumerate(val)}
    A = np.zeros((len(D)+1, len(val)))
    for j, p in enumerate(D):
        b, q = BAAS[p]; A[j, idx[b]] = 1.0; A[j, idx[q]] = -1.0
    A[-1, :] = 1.0
    pinv = np.linalg.pinv(A)
    Y = np.column_stack([R[p].values for p in D] + [np.zeros(len(R))])
    return pd.DataFrame(Y @ pinv.T, index=R.index, columns=val)

TUG = valuuta_tugevus()
w(f"valuutatugevus: {TUG.shape[1]} valuutat, kontroll summa={float(TUG.sum(axis=1).abs().max()):.1e}")

# ── kogu signaalide nimekiri koos kvaliteediskooriga ───────────
read = []
for sym, d in D.items():
    ind = P.valmista(d)
    c, h, l, o = d["close"], d["high"], d["low"], d["open"]
    a, adx = ind["atr"], ind["adx"]
    b, q = BAAS[sym]
    kulu_rt = 2 * KULU[sym] / 1e4

    # ── SIGNAAL: murre + volatiilsuse laienemine (kasutaja punkt 6A/6F)
    lb = 24
    hi = h.rolling(lb).max().shift(1)
    lo = l.rolling(lb).min().shift(1)
    up = c > hi
    dn = c < lo
    sg = up.astype(float) - dn.astype(float)

    # ── KVALITEEDIKOMPONENDID, koik baari i sulgemise seisuga ──
    # 1) ATR laienemine: jooksev ATR vs 10 paeva keskmine
    atr_exp = (a / a.rolling(240).mean()).fillna(1.0)
    # 2) trendi joondus: EMA50 vs EMA200 suund vs signaali suund
    ef, es = c.ewm(span=50).mean(), c.ewm(span=200).mean()
    tr_suund = np.sign(ef - es)
    joondus = (np.sign(sg) == tr_suund).astype(float)
    # 3) suhteline tugevus: baas miinus kvoot, 120h kumulatiiv
    ts = TUG.reindex(d.index).ffill()
    if b in ts.columns and q in ts.columns:
        rs = (ts[b].rolling(120).sum() - ts[q].rolling(120).sum())
        rs_z = (rs / rs.rolling(480).std()).fillna(0.0)
    else:
        rs_z = pd.Series(0.0, index=d.index)
    rs_kooskola = (np.sign(sg) * np.sign(rs_z)).clip(lower=0)
    # 4) kulu liikumise suhtes: ATR / spread (suurem = parem)
    kulu_suhe = (a / c) / (2*KULU[sym]/1e4)
    # 5) murde selgus: kui kaugele ule taseme (ATR-i uhikutes)
    selgus = pd.Series(0.0, index=d.index)
    selgus[up] = ((c - hi) / a)[up]
    selgus[dn] = ((lo - c) / a)[dn]
    selgus = selgus.fillna(0.0).clip(0, 3)
    # 6) ADX (trendi tugevus)
    adx_n = (adx / 50.0).clip(0, 2)

    # ── realiseeruv tootlus: sisene i+1 avanemisel, valju i+8 sulgemisel
    y = (c.shift(-8) / o.shift(-1) - 1)

    m = (sg != 0) & y.notna() & atr_exp.notna() & a.notna() & (a > 0)
    if int(m.sum()) < 200:
        continue
    for nimi, arr in (("atr_exp", atr_exp), ("joondus", joondus),
                      ("rs", rs_kooskola), ("kulu_suhe", kulu_suhe),
                      ("selgus", selgus), ("adx", adx_n)):
        pass
    df_ = pd.DataFrame(dict(
        sym=sym, aeg=d.index[m], suund=sg[m].values,
        y=(np.sign(sg[m]) * y[m]).values,
        neto=(np.sign(sg[m]) * y[m] - kulu_rt).values,
        atr_exp=atr_exp[m].values, joondus=joondus[m].values,
        rs=rs_kooskola[m].values, kulu_suhe=kulu_suhe[m].values,
        selgus=selgus[m].values, adx=adx_n[m].values))
    read.append(df_)

S = pd.concat(read, ignore_index=True).dropna()
S = S[np.isfinite(S["neto"])]
w(f"signaale kokku: {len(S)}  ({len(S)/len(D):.0f} paari kohta)")

# ── KVALITEEDISKOOR: z-standarditud komponentide summa ─────────
KOMP = ["atr_exp", "joondus", "rs", "kulu_suhe", "selgus", "adx"]
Z = S[KOMP].apply(lambda x: (x - x.mean()) / x.std())
S["kvaliteet"] = Z.sum(axis=1)

w("")
w("=" * 96)
w("1) KAS ÜKSIK KVALITEEDIKOMPONENT ENNUSTAB TULEMUST?")
w("=" * 96)
w("  Iga komponent eraldi: jaga signaalid 5 ossa, vaata NETO tulemust.")
w("")
w(f"  {'komponent':12s} {'1 (madal)':>11s} {'2':>9s} {'3':>9s} {'4':>9s} "
  f"{'5 (kõrge)':>11s} {'5 miinus 1':>12s}")
w("  " + "-" * 78)
for k in KOMP:
    try:
        b_ = pd.qcut(S[k], 5, labels=False, duplicates="drop")
    except Exception:
        continue
    g = S.groupby(b_)["neto"].mean() * 1e4
    if len(g) < 5: continue
    w(f"  {k:12s} {g.iloc[0]:+10.2f} {g.iloc[1]:+9.2f} {g.iloc[2]:+9.2f} "
      f"{g.iloc[3]:+9.2f} {g.iloc[4]:+10.2f} {g.iloc[4]-g.iloc[0]:+11.2f}")

w("")
w("=" * 96)
w("2) OTSUSTAV: KAS LIITKVALITEEDISKOOR ENNUSTAB? (detsiilid)")
w("=" * 96)
S["det"] = pd.qcut(S["kvaliteet"], 10, labels=False, duplicates="drop")
g = S.groupby("det").agg(n=("neto","size"), bruto=("y","mean"),
                         neto=("neto","mean"), wr=("neto", lambda x: 100*(x>0).mean()))
w(f"  {'detsiil':>8s} {'signaale':>10s} {'BRUTO bp':>10s} {'NETO bp':>10s} {'võit%':>8s}")
w("  " + "-" * 50)
for i, r in g.iterrows():
    mark = "  <-- TOP" if i == g.index.max() else ("  <-- põhi" if i == g.index.min() else "")
    w(f"  {int(i)+1:>8d} {int(r['n']):10d} {1e4*r['bruto']:+10.2f} "
      f"{1e4*r['neto']:+10.2f} {r['wr']:7.1f}%{mark}")
w("  " + "-" * 50)
w(f"  {'KÕIK':>8s} {len(S):10d} {1e4*S['y'].mean():+10.2f} "
  f"{1e4*S['neto'].mean():+10.2f} {100*(S['neto']>0).mean():7.1f}%")

top = g.loc[g.index.max()]; pohi = g.loc[g.index.min()]
vahe = 1e4 * (top["neto"] - pohi["neto"])
w("")
w(f"  TOP-detsiil miinus PÕHI-detsiil: {vahe:+.2f}bp")
w(f"  TOP-detsiil vs KÕIK:             {1e4*(top['neto']-S['neto'].mean()):+.2f}bp")

# monotoonsus
korr = float(np.corrcoef(g.index.values, g["neto"].values)[0,1])
w(f"  Detsiili ja NETO korrelatsioon:  {korr:+.3f}  "
  f"({'monotoonne' if abs(korr)>0.6 else 'EI OLE monotoonne'})")

w("")
w("=" * 96)
w("3) JÄRELDUS")
w("=" * 96)
if 1e4*top["neto"] > 0 and vahe > 2 and korr > 0.6:
    w("  SELEKTIIVSUS TÖÖTAB. TOP-detsiil on plussis, seos on monotoonne.")
    w("  => tasub ehitada portfellimootor ja testida edasi.")
else:
    w("  SELEKTIIVSUS EI TÖÖTA.")
    if 1e4*top["neto"] <= 0:
        w(f"    - TOP-detsiil on ise miinuses ({1e4*top['neto']:+.2f}bp)")
    if vahe <= 2:
        w(f"    - TOP ja PÕHI vahe on ainult {vahe:+.2f}bp")
    if korr <= 0.6:
        w(f"    - seos ei ole monotoonne (r={korr:+.3f})")
    w("")
    w("  MIKS SEE TÄHENDAB, ET PORTFELL EI PÄÄSTA:")
    w("  Hajutamine vähendab HAJUVUST, mitte ei loo TOOTLUST. Kui parimate")
    w("  signaalide oodatav väärtus on negatiivne, on ka nende portfelli oma")
    w("  negatiivne — lihtsalt siledama kõveraga.")
S.to_pickle("data/v7_signaalid.pkl")
w("")
w(f"  signaalid salvestatud: data/v7_signaalid.pkl")
w("VALMIS")
