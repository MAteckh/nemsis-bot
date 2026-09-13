"""
T1 SUVAKONTROLL: kust tuleb 0.43bp süstemaatiline pessimism?

MIKS SEE LOEB: kogu mu senine jareldus tugineb vaitele "bruto-ootus on
-1.8bp ehk signaalid kaotavad ka ILMA kuludeta". Kui mootor ise tekitab
-0.4..-2bp pessimismi, on see jareldus VALE ja ma pean selle tagasi votma.

TEOORIA: triivita juhuslikul jalutuskaigul on P(TP enne SL) = SL/(TP+SL).
TP=2R, SL=1R => P=1/3, oodatav vaartus = (1/3)(2R) - (2/3)(1R) = 0 TAPSELT.

Kolm voimalikku pessimismi allikat:
  A) "molemad tabatud => SL" reegel
  B) ajapiirang (max_baare) — sulgeb positsiooni turuhinnaga
  C) minu SUNTEETILISE seeria high/low konstruktsioon (wick'id
     genereeritud soltumatult teekonnast => tasemeid puudutatakse
     sagedamini kui pariselt)

Eraldame nad.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import paar_engine as P

OUT = "audit_t1.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()


def gbm_ohlc(n, sigma, seed, sammud=20):
    """
    Juhuslik jalutuskaik, kus high/low tulevad PARIS teekonnast
    (baari sees sammud alamsammu). Nii ei ole wick'id valjamoeldud.
    """
    rg = np.random.default_rng(seed)
    s = sigma / np.sqrt(sammud)
    r = rg.normal(0, s, n * sammud)
    p = 1.10 * np.exp(np.cumsum(r)).reshape(n, sammud)
    alg = np.concatenate([[1.10], p[:-1, -1]])
    return pd.DataFrame(dict(
        open=alg, high=np.maximum(p.max(axis=1), alg),
        low=np.minimum(p.min(axis=1), alg), close=p[:, -1]),
        index=pd.date_range("2020-01-01", periods=n, freq="h"))


w("=" * 92)
w("T1 SÜVAKONTROLL — kas mootor tekitab süstemaatilist pessimismi?")
w("=" * 92)
w("  Teooria: triivita jalutuskäigul TP=2R/SL=1R => oodatav BRUTO = 0.0bp")
w("")
w(f"  {'seeria tüüp':>26s} {'max_baare':>10s} {'tehinguid':>10s} {'võit%':>7s} "
  f"{'BRUTO bp':>10s} {'SE':>7s} {'aeg-välj%':>10s}")
w("  " + "-" * 86)

for nimi, gen in (("VÄLJAMÕELDUD wick'id", None), ("PÄRIS teekond (20 alamsammu)", gbm_ohlc)):
    for mb in (24, 120, 2000):
        b, wr, n_, aeg = [], [], [], []
        for seed in range(8):
            if gen is None:
                rg = np.random.default_rng(seed)
                n = 20000; sig = 0.0008
                r = rg.normal(0, sig, n)
                c = 1.10 * np.exp(np.cumsum(r))
                o = np.concatenate([[1.10], c[:-1]])
                rr = np.random.default_rng(seed + 500)
                hi = np.maximum(o, c) * (1 + np.abs(rr.normal(0, sig*0.6, n)))
                lo = np.minimum(o, c) * (1 - np.abs(rr.normal(0, sig*0.6, n)))
                d = pd.DataFrame(dict(open=o, high=hi, low=lo, close=c),
                                 index=pd.date_range("2020-01-01", periods=n, freq="h"))
            else:
                d = gen(20000, 0.0008, seed)
            ind = P.valmista(d)
            rg2 = np.random.default_rng(1000 + seed)
            sg = pd.Series(0.0, index=d.index)
            ix = rg2.choice(np.arange(300, len(d)-1), size=1200, replace=False)
            sg.iloc[np.sort(ix)] = rg2.choice([-1.0, 1.0], size=1200)
            t = P.simuleeri(d, sg, 1.5, 3.0, 0.0, ind, (0, 24), max_baare=mb)
            if t is None or len(t) < 50: continue
            b.append(float(t["bruto"].mean()))
            wr.append(100*float((t["bruto"] > 0).mean()))
            n_.append(len(t))
            aeg.append(100*float((t["pohjus"] == "aeg").mean()))
        if not b: continue
        se = 1e4*np.std(b)/np.sqrt(len(b))
        w(f"  {nimi:>26s} {mb:10d} {int(np.mean(n_)):10d} {np.mean(wr):6.1f}% "
          f"{1e4*np.mean(b):+10.3f} {se:7.3f} {np.mean(aeg):9.1f}%")

w("")
w("  Teooria ütleb: TP=2R/SL=1R => võiduprotsent 33.3%, BRUTO 0.0bp")
w("")

# ── kas 'molemad tabatud' on suur? ──────────────────────────────
w("=" * 92)
w("KUI SUUR ON 'MÕLEMAD TABATUD => SL' REEGLI MAKSUMUS?")
w("=" * 92)
d = gbm_ohlc(20000, 0.0008, 42)
ind = P.valmista(d)
rg = np.random.default_rng(77)
sg = pd.Series(0.0, index=d.index)
ix = rg.choice(np.arange(300, len(d)-1), size=3000, replace=False)
sg.iloc[np.sort(ix)] = rg.choice([-1.0, 1.0], size=3000)

# loenda molemad-tabatud kaigud kasitsi
o,h,l,c = d["open"].values,d["high"].values,d["low"].values,d["close"].values
a = ind["atr"].values; s = sg.values
mol = kokku = 0
i = 250
while i < len(d)-1:
    if s[i]==0 or not (np.isfinite(a[i]) and a[i]>0): i+=1; continue
    su=int(np.sign(s[i])); e=o[i+1]; sld=1.5*a[i]; tpd=3.0*sld
    tp=e+su*tpd; slh=e-su*sld; j=i+1; done=False
    for j in range(i+1, min(i+1+120, len(d))):
        th=(h[j]>=tp) if su==1 else (l[j]<=tp)
        sh_=(l[j]<=slh) if su==1 else (h[j]>=slh)
        if th and sh_: mol+=1; done=True; break
        if th or sh_: done=True; break
    kokku+=1; i=j+1
w(f"  'mõlemad tabatud samas baaris': {mol} / {kokku} tehingut = "
  f"{100*mol/max(kokku,1):.2f}%")
w(f"  Iga selline juhtum kaotab 3R asemel -1R => mõju = "
  f"{100*mol/max(kokku,1):.2f}% x 4R")

w("")
w("=" * 92)
w("JÄRELDUS")
w("=" * 92)
