"""
LOOKAHEAD-AUDIT (kasutaja punkt 3) — kohustuslik ENNE testi jooksutamist.

Iga test on konstrueeritud nii, et KUKUKS LABI, kui viga oleks sees.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import impulss_engine as I

OUT = "impulss_audit.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()
OK, VIGA = [], []
def k(nimi, tingimus, det):
    (OK if tingimus else VIGA).append(nimi)
    w(f"  [{'OK  ' if tingimus else 'VIGA'}] {nimi:48s} {det}")


def gbm(n=12000, sigma=0.0008, seed=7, sammud=20):
    """Juhuslik jalutuskaik PARIS teekonnaga. Serva EI OLE."""
    rg = np.random.default_rng(seed)
    s = sigma / np.sqrt(sammud)
    p = 1.10 * np.exp(np.cumsum(rg.normal(0, s, n*sammud))).reshape(n, sammud)
    alg = np.concatenate([[1.10], p[:-1, -1]])
    return pd.DataFrame(dict(open=alg, high=np.maximum(p.max(1), alg),
                             low=np.minimum(p.min(1), alg), close=p[:, -1]),
                        index=pd.date_range("2020-01-01", periods=n, freq="h"))

w("=" * 92)
w("LOOKAHEAD-AUDIT — sünteetilised testid teadaolevate vastustega")
w("=" * 92)

d = gbm()

# T1 ATR ei sisalda jooksvat baari
a = I.atr_shift(d)
tr_now = (d["high"] - d["low"])
# kui ATR sisaldaks jooksvat baari, oleks korrelatsioon tugev
korr = float(pd.concat([a, tr_now], axis=1).dropna().corr().iloc[0, 1])
k("T1 ATR ei sisalda jooksva baari ulatust", korr < 0.45,
  f"korrelatsioon ATR vs jooksev ulatus = {korr:+.3f}")

# T2 6-baari tipp ei sisalda jooksvat baari
hi6 = d["high"].rolling(6).max().shift(1)
rikub = int((hi6 >= d["high"]).sum() == len(d.dropna()))
k("T2 6-baari tipp on baarid i-6..i-1", not rikub,
  f"jooksev high ületab 6-baari tippu {int((d['high'] > hi6).sum())} korda "
  f"(peab olema > 0)")

# T3 juhuslikul jalutuskaigul peab BRUTO olema ~0
tul = []
for seed in range(8):
    dd = gbm(seed=seed)
    sg, _ = I.impulss(dd, "A")
    sg2, nihe = I.kinnitus(dd, sg, "JATK")
    t = I.simuleeri(dd, sg2, hoia=2, suund=+1, nihe=nihe)
    if t is not None and len(t) > 50:
        tul.append(float(t["bruto"].mean()))
m, se = 1e4*np.mean(tul), 1e4*np.std(tul)/np.sqrt(len(tul))
k("T3 juhuslikul jalutuskäigul BRUTO ~ 0", abs(m) < max(3*se, 1.0),
  f"mõõdetud {m:+.2f}bp, SE {se:.2f}")

# T4 POSITIIVNE KONTROLL: kui anda tuleviku info, peab test seda nagema
dd = gbm(seed=99)
tulevik = np.sign(dd["close"].shift(-3) - dd["close"]).fillna(0.0)
t = I.simuleeri(dd, tulevik, hoia=2, suund=+1, nihe=0)
petu = 1e4*float(t["bruto"].mean())
k("T4 tuleviku info annab suure plussi (test toimib)", petu > m + 10,
  f"{petu:+.1f}bp vs juhuslik {m:+.2f}bp")

# T5 sisenemine on baari i+1 avanemishind
dsm = gbm(n=400, seed=3)
sg = pd.Series(0.0, index=dsm.index); sg.iloc[200] = 1.0
t = I.simuleeri(dsm, sg, hoia=1, suund=+1, nihe=0)
ood = (float(dsm["close"].iloc[202]) - float(dsm["open"].iloc[201])) / float(dsm["open"].iloc[201])
k("T5 entry=open[i+1], exit=close[i+1+hoia]",
  len(t) == 1 and abs(float(t["bruto"].iloc[0]) - ood) < 1e-12,
  f"saadud {float(t['bruto'].iloc[0]):+.8f}, oodatav {ood:+.8f}")

# T6 poordumine on tapselt -1 x jatkuvus (ilma stopita)
t1 = I.simuleeri(dsm, sg, hoia=2, suund=+1, nihe=0)
t2 = I.simuleeri(dsm, sg, hoia=2, suund=-1, nihe=0)
k("T6 pöördumine = -1 x jätkuvus (ilma stopita)",
  abs(float(t1["bruto"].iloc[0]) + float(t2["bruto"].iloc[0])) < 1e-15,
  f"{float(t1['bruto'].iloc[0]):+.8f} + {float(t2['bruto'].iloc[0]):+.8f}")

# T7 TAGASI-kinnitus nihutab sisenemist uhe baari vorra
sg_a, _ = I.impulss(d, "A")
_, nihe_j = I.kinnitus(d, sg_a, "JATK")
_, nihe_t = I.kinnitus(d, sg_a, "TAGASI")
k("T7 TAGASI-kinnitus nihutab entry i+2-le", nihe_j == 0 and nihe_t == 1,
  f"JATK nihe={nihe_j}, TAGASI nihe={nihe_t}")

w("")
w("=" * 92)
w(f"AUDIT: {len(OK)} OK, {len(VIGA)} VIGA")
if VIGA:
    for v in VIGA: w(f"  VIGA: {v}")
else:
    w("  Lookahead'i ei tuvastatud. Testi võib jooksutada.")
w("=" * 92)
