"""
OTSUSTAV TEST: kas kogu see otsing toodab midagi kaubeldavat?

PROBLEEM, mida see lahendab. Ma tegin 10 156 testi ja leidsin WTI
sessioonimurde: +24bp, koik 5 poolaastat plussis, null p=0.000.
Aga ma VALISIN selle 10 156 seast. Parim-10000-st NAEB alati selline
valja. Koik jargnevad kontrollid samade andmete peal on ringtoestus.

AINUS AUS TEST: teeskle, et on 2025. aasta keskpaik. Vali strateegia
AINULT selle hetkeni olemasolevate andmete pealt. Siis vaata, mida ta
teenis EDASPIDI. 2. poole andmeid ei kasutata valikul mitte kuidagi.

Teeme kolm varianti:
  A) pooleks: vali 1. poolelt, mõõda 2. poolel
  B) libisev: vali 12 kuu pealt, kauple 3 kuud, korda
  C) portfell: kas KOIGI instrumentide korv paastab uksiku nork serva?
     (kasutaja idee "kasuta koiki valuutasid")
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import h1engine as E

OUT = "h1_wf_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

D = E.lae_koik()

# ── ehita KOIK kandidaadid tootlusseeriatena (baari kaupa) ───────
def ehita(sym, d):
    """Tagastab {nimi: paevatootluste seeria}. Kaal on teada baaril i,
    teenib baari i+1 tootluse. Kulu lahutatakse kaalu MUUTUSE pealt."""
    c, h, l, o = d["close"], d["high"], d["low"], d["open"]
    tund = d.index.hour
    grp = pd.Series(d.index.normalize(), index=d.index)
    out = {}
    for lb in (6, 12, 24, 48, 96, 168):
        out[f"DON{lb}"] = ((c >= h.rolling(lb).max().shift(1)).astype(float)
                           - (c <= l.rolling(lb).min().shift(1)).astype(float))
    for lb in (4, 12, 24, 72, 168):
        out[f"MOM{lb}"] = pd.Series(np.sign((c / c.shift(lb) - 1).values),
                                    index=d.index).fillna(0.0)
    for lb in (12, 24, 72):
        m_, sd = c.rolling(lb).mean(), c.rolling(lb).std()
        z = (c - m_) / sd
        out[f"REV{lb}"] = (-np.sign(z) * (z.abs() > 1.0)).fillna(0.0)
    for a0, a1, k0, k1, nm in ((0, 7, 7, 16, "AS→LN"), (7, 13, 13, 21, "LN→NY")):
        vahe = (tund >= a0) & (tund < a1)
        hi = h.where(vahe).groupby(grp).transform("max")
        lo = l.where(vahe).groupby(grp).transform("min")
        aken = (tund >= k0) & (tund < k1)
        sg = (((c > hi) & aken).astype(float) - ((c < lo) & aken).astype(float))
        out[f"SESS {nm}"] = sg.fillna(0.0)
    for hh in (2, 6, 10, 14, 18, 22):
        out[f"TUND{hh}"] = pd.Series(np.where(tund == hh, 1.0, 0.0), index=d.index)
    return out


# hoidmisaeg: kaal kehtib H baari
H_HOID = 8

R = {}          # {(sym, nimi): tootlusseeria}
for sym, d in D.items():
    kulu = 2 * E.KULU_RETAIL.get(sym, 2.0) / 1e4
    r_next = (d["close"].shift(-1) / d["close"] - 1)
    for nimi, sg in ehita(sym, d).items():
        # hoia signaali H baari
        pos = sg.replace(0.0, np.nan).ffill(limit=H_HOID).fillna(0.0)
        vahetus = pos.diff().abs().fillna(pos.abs())
        x = (pos * r_next - vahetus * kulu / 2).fillna(0.0)
        if float((pos != 0).mean()) < 0.02:
            continue
        R[(sym, nimi)] = x

M = pd.DataFrame(R).fillna(0.0).sort_index()
w(f"kandidaate: {M.shape[1]}   baare: {M.shape[0]}   "
  f"periood {M.index[0].date()} .. {M.index[-1].date()}")


def sh(x):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 100 or x.std() == 0:
        return 0.0
    return float(x.mean() / x.std() * math.sqrt(6000))


# ══ A) POOLEKS ══════════════════════════════════════════════════
w("")
w("=" * 100)
w("A) VALI 1. POOLELT, MÕÕDA 2. POOLEL (2. poole andmeid valikul EI kasutata)")
w("=" * 100)
m = len(M) // 2
A, B = M.iloc[:m], M.iloc[m:]
w(f"   valikuaken  {A.index[0].date()} .. {A.index[-1].date()}")
w(f"   testiaken   {B.index[0].date()} .. {B.index[-1].date()}")
w("")
w(f"   {'valikureegel':34s} {'valitud':>8s} {'IS Sharpe':>10s} {'OOS Sharpe':>11s}")
w("   " + "-" * 68)

def korv(dfp, cols):
    if not cols:
        return pd.Series(0.0, index=dfp.index)
    Z = dfp[cols] / dfp[cols].std().replace(0, np.nan)
    return Z.mean(axis=1).fillna(0.0)

for lavi in (0.0, 0.5, 1.0, 1.5):
    val = [c for c in M.columns if sh(A[c]) > lavi]
    if not val:
        w(f"   {'Sharpe > ' + str(lavi):34s} {'0':>8s}  ükski ei kvalifitseeru")
        continue
    w(f"   {'kõik, kelle IS Sharpe > ' + str(lavi):34s} {len(val):8d} "
      f"{sh(korv(A, val)):+10.2f} {sh(korv(B, val)):+11.2f}")

# iga instrumendi PARIM 1. poolelt
parim_per_sym = {}
for sym in D:
    kand = [c for c in M.columns if c[0] == sym]
    if not kand:
        continue
    b = max(kand, key=lambda c: sh(A[c]))
    parim_per_sym[sym] = b
val = list(parim_per_sym.values())
w(f"   {'iga instrumendi parim (1.pool)':34s} {len(val):8d} "
  f"{sh(korv(A, val)):+10.2f} {sh(korv(B, val)):+11.2f}")

w("")
w("   INSTRUMENDIKAUPA — mida 1. pool soovitas ja mida see 2. poolel tootis:")
w(f"      {'instr':8s} {'valitud 1. poolelt':22s} {'IS Sharpe':>10s} {'OOS Sharpe':>11s}")
w("      " + "-" * 56)
oos_pos = 0
for sym, c in sorted(parim_per_sym.items()):
    s_is, s_oos = sh(A[c]), sh(B[c])
    oos_pos += (s_oos > 0)
    w(f"      {sym:8s} {c[1]:22s} {s_is:+10.2f} {s_oos:+11.2f}"
      f"{'  <<<' if s_oos > 0 else ''}")
w(f"      => OOS plussis {oos_pos}/{len(parim_per_sym)}  "
  f"(mündivisega oodatav {len(parim_per_sym)/2:.1f})")

# ══ B) LIBISEV AKEN ═════════════════════════════════════════════
w("")
w("=" * 100)
w("B) LIBISEV AKEN — vali 12 kuu pealt, kauple 3 kuud, korda")
w("=" * 100)
w(f"   {'kauplemisaken':>26s} {'valitud':>8s} {'OOS Sharpe':>11s}")
w("   " + "-" * 48)
VAL, TEST = 12 * 500, 3 * 500      # ~tunde
i = VAL
kogu = []
while i + TEST < len(M):
    tr, te = M.iloc[i - VAL:i], M.iloc[i:i + TEST]
    val = [c for c in M.columns if sh(tr[c]) > 1.0]
    if len(val) >= 3:
        k = korv(te, val)
        kogu.append(k)
        w(f"   {str(te.index[0].date()):>12s}..{str(te.index[-1].date()):>12s} "
          f"{len(val):8d} {sh(k):+11.2f}")
    i += TEST
if kogu:
    kk = pd.concat(kogu)
    w("")
    w(f"   KÕIK OOS-aknad kokku: Sharpe {sh(kk):+.2f}   "
      f"positiivseid aknaid {sum(1 for k in kogu if sh(k)>0)}/{len(kogu)}")

# ══ C) PORTFELL: kas KÕIK valuutad koos päästavad? ══════════════
w("")
w("=" * 100)
w("C) KASUTAJA IDEE — 'kasuta kõiki valuutasid'. Kas hajutamine päästab?")
w("=" * 100)
for per_nimi, filt in (("kõik kandidaadid", lambda c: True),
                       ("ainult DONCHIAN", lambda c: c[1].startswith("DON")),
                       ("ainult MOMENTUM", lambda c: c[1].startswith("MOM")),
                       ("ainult PÖÖRE", lambda c: c[1].startswith("REV")),
                       ("ainult SESSIOON", lambda c: c[1].startswith("SESS")),
                       ("ainult FX", lambda c: c[0] in E.FX)):
    cols = [c for c in M.columns if filt(c)]
    if not cols:
        continue
    k = korv(M, cols)
    eq = (1 + k * (0.10 / (k.std() * math.sqrt(6000)))).cumprod()
    dd = float((eq / eq.cummax() - 1).min())
    w(f"   {per_nimi:20s} {len(cols):4d} signaali   Sharpe {sh(k):+6.2f}   "
      f"10% vol sihiga: kokku {100*(eq.iloc[-1]-1):+7.1f}%  maxDD {100*dd:+6.1f}%")
w("VALMIS")
