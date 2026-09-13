"""
KAS KUUNLAMUSTRID ENNUSTAVAD MIDAGI? — puhas test, ilma TP/SL-ita.

Kasutaja idee: tuvasta liikumine kuunlamustri jargi, kauple KOIKI
valuutasid, vaikeste eesmarkidega (1-2 EUR).

METOODIKA: enne kui valida TP/SL, tuleb teada, kas mustril on
ULDSE serv. Kui muster ei ennusta jargmise paeva suunda, ei paasta
teda ukski TP/SL kombinatsioon.

Test: tuvasta muster paeval t, mõõda paeva t+1 tootlus (Open->Close,
mida saab kaubelda). Vordle mustri-paevade keskmist KOIGI paevade
keskmisega. Kui vahet ei ole, serva ei ole.

Kontrollid:
  - t-statistik ja Bonferroni (mustreid x instrumente = palju teste)
  - poolte-test
  - kulupiir: kas serv uletab spread'i

KOLBLIKUD INSTRUMENDID: koik peale EURUSD (seal Open == Close, mustreid
ei saa arvutada). run_small_tp.py kinnitas, et ulejaanud 17-l on Open
kasutatav.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

OUT = "candles_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

SYMS = ["GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURJPY",
        "XAUUSD", "XAGUSD", "SPX", "NAS100", "GER40", "JP225", "WTI",
        "COPPER", "BTCUSD", "ETHUSD"]

# uhesuunaline kulu bp-des (run_small_tp.py SPEC-ist tuletatud, konservatiivne)
COST_BP = {"GBPUSD": 0.6, "USDJPY": 0.6, "AUDUSD": 0.9, "NZDUSD": 1.3,
           "USDCAD": 0.9, "USDCHF": 0.9, "EURJPY": 0.8, "XAUUSD": 0.4,
           "XAGUSD": 1.6, "SPX": 0.4, "NAS100": 0.3, "GER40": 0.3,
           "JP225": 0.5, "WTI": 1.5, "COPPER": 1.2, "BTCUSD": 1.6,
           "ETHUSD": 0.9}


def load(s):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        if c not in d.columns:
            return None
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna()
    return d if len(d) > 500 else None


def mustrid(d):
    """Tagastab dict: mustri nimi -> bool-seeria (+1 tõusu-, -1 languseootus)."""
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    keha = (c - o)
    keha_abs = keha.abs()
    vahemik = (h - l).replace(0, np.nan)
    ulem = h - np.maximum(o, c)
    alum = np.minimum(o, c) - l
    po, pc = o.shift(1), c.shift(1)
    pkeha = (pc - po)

    m = {}
    # Neelav muster (engulfing)
    m["tõusev neelav"] = ((pkeha < 0) & (keha > 0) & (c > po) & (o < pc)).astype(int)
    m["langev neelav"] = -((pkeha > 0) & (keha < 0) & (c < po) & (o > pc)).astype(int)
    # Vasar / langev täht
    m["vasar"] = ((alum > 2 * keha_abs) & (ulem < keha_abs) & (keha_abs / vahemik < 0.35)).astype(int)
    m["langev täht"] = -((ulem > 2 * keha_abs) & (alum < keha_abs) & (keha_abs / vahemik < 0.35)).astype(int)
    # Doji
    m["doji"] = ((keha_abs / vahemik) < 0.1).astype(int)
    # Sisemine / välimine baar
    m["sisemine baar"] = ((h < h.shift(1)) & (l > l.shift(1))).astype(int)
    m["välimine baar"] = ((h > h.shift(1)) & (l < l.shift(1))).astype(int)
    # Kolm valget sõdurit / musta varest
    # shift() tekitab esimestesse ridadesse NaN'i => dtype muutub ja `~`
    # viskab "bad operand type for unary ~: 'float'". fillna+astype(bool)
    # enne loogikat.
    up = (c > o)
    up1 = up.shift(1).fillna(False).astype(bool)
    up2 = up.shift(2).fillna(False).astype(bool)
    m["3 valget sõdurit"] = (up & up1 & up2).astype(int)
    m["3 musta varest"] = -((~up) & (~up1) & (~up2)).astype(int)
    # Marubozu (pikk keha, lühikesed vurrud)
    m["marubozu üles"] = ((keha > 0) & (keha_abs / vahemik > 0.9)).astype(int)
    m["marubozu alla"] = -((keha < 0) & (keha_abs / vahemik > 0.9)).astype(int)
    return m


def tstat(x):
    x = x[np.isfinite(x)]
    if len(x) < 30 or x.std() == 0:
        return 0.0, 1.0, len(x)
    t = x.mean() / x.std() * math.sqrt(len(x))
    return t, math.erfc(abs(t) / math.sqrt(2)), len(x)


read = []
for s in SYMS:
    d = load(s)
    if d is None:
        continue
    # jargmise paeva OPEN -> CLOSE (kaubeldav osa)
    fwd = (d["close"] / d["open"] - 1).shift(-1)
    for nimi, sig in mustrid(d).items():
        sel = sig != 0
        if sel.sum() < 30:
            continue
        x = (np.sign(sig) * fwd)[sel].dropna().values
        t, p, n = tstat(x)
        kulu = 2 * COST_BP[s] / 1e4
        read.append(dict(sym=s, muster=nimi, n=n, keskm=x.mean(),
                         t=t, p=p, kulu=kulu, neto=x.mean() - kulu))

df = pd.DataFrame(read)
N_TESTE = len(df)
BONF = 0.05 / max(N_TESTE, 1)

w("=" * 100)
w("KÜÜNLAMUSTRID — kas neil on serv? (järgmise päeva Open->Close)")
w("=" * 100)
w(f"  instrumente {df['sym'].nunique()}, mustreid {df['muster'].nunique()}, "
  f"teste kokku {N_TESTE}")
w(f"  Bonferroni lävend: p < {BONF:.6f}")
w("")
w("  1) MUSTRITE KAUPA (kõik instrumendid koos)")
w(f"  {'muster':20s} {'teste':>6s} {'keskm bp':>10s} {'NETO bp':>9s} "
  f"{'+ neto':>8s} {'parim t':>9s}")
w("  " + "-" * 68)
for nimi, g in df.groupby("muster"):
    pos = (g["neto"] > 0).sum()
    w(f"  {nimi:20s} {len(g):6d} {1e4*g['keskm'].mean():+9.2f} "
      f"{1e4*g['neto'].mean():+8.2f} {pos:4d}/{len(g):<3d} {g['t'].abs().max():+9.2f}")

w("")
w("  2) KAS MÕNI ÜKSIK KOMBINATSIOON LÄBIB BONFERRONI?")
labib = df[df["p"] < BONF]
if len(labib) == 0:
    w(f"     MITTE ÜKSKI {N_TESTE}-st. (ootuspärane juhuslikult: "
      f"{0.05*N_TESTE:.1f} p<0.05 juures, 0 Bonferroni juures)")
else:
    for _, r in labib.sort_values("p").iterrows():
        w(f"     {r['sym']:8s} {r['muster']:20s} n={r['n']:5d} "
          f"t={r['t']:+.2f} p={r['p']:.2e} NETO={1e4*r['neto']:+.2f}bp")

w("")
w("  3) ILMA BONFERRONITA — mitu on p<0.05? (võrdle juhusega)")
p05 = (df["p"] < 0.05).sum()
w(f"     p<0.05: {p05} / {N_TESTE}  ({100*p05/N_TESTE:.1f}%)")
w(f"     juhuslikult oodatav: {0.05*N_TESTE:.1f} ({5.0:.1f}%)")

w("")
w("  4) KULUPIIR — mitu on peale kulusid plussis?")
pos = (df["neto"] > 0).sum()
w(f"     bruto plussis: {(df['keskm'] > 0).sum()} / {N_TESTE}")
w(f"     NETO plussis:  {pos} / {N_TESTE}  ({100*pos/N_TESTE:.1f}%)")
w(f"     keskmine NETO: {1e4*df['neto'].mean():+.2f}bp")

w("")
w("  5) PARIMAD 10 (neto järgi) — ja kas need on usaldusväärsed?")
w(f"  {'sümbol':8s} {'muster':20s} {'n':>6s} {'NETO bp':>9s} {'t':>7s} {'p':>10s}")
w("  " + "-" * 64)
for _, r in df.nlargest(10, "neto").iterrows():
    w(f"  {r['sym']:8s} {r['muster']:20s} {r['n']:6d} {1e4*r['neto']:+8.2f} "
      f"{r['t']:+7.2f} {r['p']:10.4f}")
w("VALMIS")
