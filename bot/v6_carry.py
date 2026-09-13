"""
NEMSIS v6 — KATEGOORIA 1: PARIS FX CARRY.

ANDMED: BIS WS_CBPOL, keskpankade ametlikud poliitikamaarad, kuu lopu
seisuga, 2016-01 .. 2026-08, koik 8 valuutat.
Allikas: https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/M.XX
Neid maarasid EI REVIDEERITA — nad kuulutatakse valja ja kehtivad
kindlast kuupaevast. Seega ei ole "hiljem avaldatud revised data" riski.

LOOKAHEAD-KAITSE: BIS annab KUU LOPU maara. Kuu M maar on teada kuu M
LOPUS. Seega kauplemisel kuus M+1 kasutame kuu M maara => nihe 1 kuu.
See on konservatiivne: pais bot teaks maara muutust kohe, kui keskpank
selle valja kuulutab.

EELREGISTREERITUD SPETSIFIKATSIOONID (Phase 4, uks primary kumbki):
  V6-C1  staatiline carry, KUINE rebalanss, LONG top-2 / SHORT bottom-2
  V6-C2  sama, NADALANE rebalanss
  V6-C3  volatiilsusega skaleeritud carry
  V6-C4  carry + trendifilter (kauple ainult trendi suunas)
  V6-C5  carry ilma USD-ta (dollar-neutraalne)

VORDLUSED (kohustuslikud):
  - juhuslikud valuutapaarid (sama arv positsioone)
  - osta-ja-hoia (EURUSD long)
  - olemasolevad NEMSIS FX-strateegiad (v5 parim)

NET RETURN = hinnamuutus + carry - spread - komisjon - slippage.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import v5_engine as V

OUT = "v6_carry.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

rng = np.random.default_rng(6006)
P, IX = V.paarid_df()
S = V.valuuta_tootlused(P)                 # paev x valuuta, hinnatootlus vs korv
VAL = list(S.columns)

# ── intressimaarad, NIHUTATUD 1 kuu (lookahead-kaitse) ─────────
R = pd.read_csv("data/policy_rates.csv")
R["Month"] = pd.to_datetime(R["Month"] + "-01")
R = R.set_index("Month").shift(1)          # kuu M maar kehtib kuus M+1
Rd = R.reindex(pd.date_range(R.index[0], IX[-1], freq="D")).ffill().reindex(IX).ffill()
Rd = Rd[VAL].dropna(how="all")

# carry PAEVAS: (maar% / 100) / 252
CARRY = Rd / 100.0 / 252.0
# suhteline carry vs korvi keskmine (nagu S on suhteline hinnatootlus)
CARRY_REL = CARRY.sub(CARRY.mean(axis=1), axis=0)

w("=" * 100)
w("NEMSIS v6 — PÄRIS FX CARRY (BIS keskpankade poliitikamäärad)")
w("=" * 100)
w(f"  andmed {Rd.index[0].date()} .. {Rd.index[-1].date()}, {len(Rd)} päeva")
w(f"  intressimäärad nihutatud 1 kuu (kuu M määr kehtib kuus M+1)")
w("")
w("  Intressivahe seis mõnel kuupäeval (% aastas, vs korvi keskmine):")
for d_ in ("2017-06-30", "2021-06-30", "2023-07-31", "2026-08-31"):
    try:
        rida = CARRY_REL.loc[:d_].iloc[-1] * 252 * 100
        w(f"    {d_}: " + "  ".join(f"{c}={rida[c]:+.2f}" for c in VAL))
    except Exception:
        pass

KESK = {k: float(np.mean(list(v.values()))) for k, v in V.KULU.items()}


def korv(skoor, k=2, rebal=21, kulu_tase="BASE", vol_skaala=False,
         trend_filter=False, valja=()):
    """LONG top-k / SHORT bottom-k. Tootlus = hinnamuutus + carry - kulu."""
    sk = skoor.copy()
    for v in valja:
        if v in sk.columns: sk = sk.drop(columns=v)
    sk = sk.dropna(how="all")
    if len(sk) < 200: return None
    # rebalanss ainult iga 'rebal' paeva tagant
    pv = sk.index[::rebal]
    read = []
    for t in pv:
        r = sk.loc[t].dropna()
        if len(r) < 2*k:
            continue
        j = r.sort_values(ascending=False)
        rida_ = pd.Series(0.0, index=sk.columns, name=t)
        rida_[j.index[:k]] = 1.0/k
        rida_[j.index[-k:]] = -1.0/k
        read.append(rida_)
    if len(read) < 10:
        return None
    W = pd.DataFrame(read).reindex(sk.index, method="ffill").fillna(0.0)
    if trend_filter:
        tr = np.sign(S.rolling(60).sum()).reindex(W.index)[W.columns].fillna(0.0)
        W = W.where(np.sign(W) == tr, 0.0)
    if vol_skaala:
        vol = S.rolling(60).std().reindex(W.index)[W.columns]
        W = (W / vol.replace(0, np.nan)).div(
            (W / vol.replace(0, np.nan)).abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    Wp = W.shift(1).fillna(0.0)
    ix = Wp.index.intersection(S.index).intersection(CARRY_REL.index)
    hind = (Wp.reindex(ix) * S.reindex(ix)[Wp.columns]).sum(axis=1)
    crr = (Wp.reindex(ix) * CARRY_REL.reindex(ix)[Wp.columns]).sum(axis=1)
    kaive = Wp.reindex(ix).diff().abs().sum(axis=1).fillna(0.0)
    kulu = kaive * KESK[kulu_tase] / 1e4
    return dict(bruto=(hind + crr), neto=(hind + crr - kulu),
                hind=hind, carry=crr, kulu=kulu)


def rida(nimi, r):
    if r is None:
        w(f"  {nimi:26s}  liiga vähe andmeid"); return None
    n = r["neto"].dropna()
    tr, va, fo = V.jaota(n)
    m = V.moodikud(n)
    if m is None:
        w(f"  {nimi:26s}  liiga vähe andmeid"); return None
    w(f"  {nimi:26s} {1e4*float(r['hind'].mean()):+8.2f} {1e4*float(r['carry'].mean()):+8.2f} "
      f"{1e4*float(r['kulu'].mean()):8.2f} {1e4*m['keskm']:+9.2f} {m['sh']:+7.2f} "
      f"{1e4*float(tr.mean()):+8.2f} {1e4*float(va.mean()):+8.2f} {1e4*float(fo.mean()):+10.2f}")
    return m


w("")
w("=" * 100)
w("EELREGISTREERITUD SPETSIFIKATSIOONID (bp/päev)")
w("=" * 100)
w(f"  {'spetsifikatsioon':26s} {'hind':>8s} {'carry':>8s} {'kulu':>8s} {'NETO':>9s} "
  f"{'Sharpe':>7s} {'TRAIN':>8s} {'VALID':>8s} {'FIN.OOS':>10s}")
w("  " + "-" * 96)
tul = {}
tul["V6-C1"] = rida("C1 kuine rebalanss", korv(CARRY_REL, rebal=21))
tul["V6-C2"] = rida("C2 nädalane rebalanss", korv(CARRY_REL, rebal=5))
tul["V6-C3"] = rida("C3 vol-skaleeritud", korv(CARRY_REL, rebal=21, vol_skaala=True))
tul["V6-C4"] = rida("C4 carry + trendifilter", korv(CARRY_REL, rebal=21, trend_filter=True))
tul["V6-C5"] = rida("C5 ilma USD-ta", korv(CARRY_REL, rebal=21, valja=("USD",)))

# ── KULUTUNDLIKKUS ─────────────────────────────────────────────
w("")
w("=" * 100)
w("KULUTUNDLIKKUS")
w("=" * 100)
w(f"  {'spetsifikatsioon':26s} {'BRUTO':>9s} {'LOW':>9s} {'BASE':>9s} {'HIGH':>9s} {'hinnang':>12s}")
w("  " + "-" * 78)
for nimi, kw in (("C1 kuine", dict(rebal=21)), ("C2 nädalane", dict(rebal=5)),
                 ("C3 vol-skaleeritud", dict(rebal=21, vol_skaala=True)),
                 ("C4 + trendifilter", dict(rebal=21, trend_filter=True)),
                 ("C5 ilma USD-ta", dict(rebal=21, valja=("USD",)))):
    v_ = {}
    for kt in ("LOW", "BASE", "HIGH"):
        r = korv(CARRY_REL, kulu_tase=kt, **kw)
        if r is None: continue
        v_[kt] = 1e4*float(r["neto"].mean()); v_["BRUTO"] = 1e4*float(r["bruto"].mean())
    if not v_: continue
    h = "robustne" if v_.get("HIGH",-9) > 0 else ("FRAGIILNE" if v_.get("LOW",-9) > 0 else "kaotaja")
    w(f"  {nimi:26s} {v_['BRUTO']:+9.2f} {v_['LOW']:+9.2f} {v_['BASE']:+9.2f} "
      f"{v_['HIGH']:+9.2f} {h:>12s}")

# ── VORDLUSED ──────────────────────────────────────────────────
w("")
w("=" * 100)
w("KOHUSTUSLIKUD VÕRDLUSED")
w("=" * 100)
c1 = korv(CARRY_REL, rebal=21)
w(f"  {'võrdlusalus':30s} {'NETO bp':>10s} {'Sharpe':>8s} {'maxDD':>9s}")
w("  " + "-" * 60)
m = V.moodikud(c1["neto"].dropna())
w(f"  {'CARRY C1 (kuine)':30s} {1e4*m['keskm']:+10.2f} {m['sh']:+8.2f} {100*m['maxdd']:+8.1f}%")
# juhuslikud valuutapaarid
juh = []
for _ in range(30):
    sk = pd.DataFrame(rng.standard_normal(CARRY_REL.shape),
                      index=CARRY_REL.index, columns=CARRY_REL.columns)
    r = korv(sk.rolling(21).mean(), rebal=21)
    if r is not None: juh.append(float(r["neto"].mean()))
w(f"  {'juhuslik valuutavalik (30x)':30s} {1e4*np.mean(juh):+10.2f} "
  f"{'':>8s} {'':>9s}   parim {1e4*max(juh):+.2f}")
# osta-ja-hoia EURUSD
bh = P["EURUSD"]["close"].pct_change().dropna()
mb = V.moodikud(bh)
w(f"  {'osta-ja-hoia EURUSD':30s} {1e4*mb['keskm']:+10.2f} {mb['sh']:+8.2f} {100*mb['maxdd']:+8.1f}%")
# v5 parim FX
haal = sum(np.sign(S.rolling(lb).sum()) for lb in (1,5,20,60,120))
Wt = (np.sign(haal)/8.0).shift(1).fillna(0.0)
ixv = Wt.index.intersection(S.index)
v5 = ((Wt.reindex(ixv)*S.reindex(ixv)).sum(axis=1)
      - Wt.reindex(ixv).diff().abs().sum(axis=1).fillna(0)*KESK["BASE"]/1e4)
m5 = V.moodikud(v5.dropna())
w(f"  {'v5 parim FX (TS-MOM-MULTI)':30s} {1e4*m5['keskm']:+10.2f} {m5['sh']:+8.2f} "
  f"{100*m5['maxdd']:+8.1f}%")
w("")
w(f"  p(juhuslik >= carry) = {float(np.mean([x >= float(c1['neto'].mean()) for x in juh])):.3f}")
w("VALMIS")
