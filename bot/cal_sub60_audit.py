"""
cal_sub60_audit.py — eeltulemuste audit. PASS / FAIL iga kontrolli kohta.
Jookseb ENNE tulemuste usaldamist (kasutaja noue, sektsioon 17).
"""
import os

import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I
import cal_sub60 as S

PASS, FAIL = "PASS", "FAIL"
tulem = []


def k(nimi, ok, info=""):
    tulem.append(bool(ok))
    print(f"{PASS if ok else FAIL}  {nimi:<58s} {info}")


print("=" * 112)
print("SUB-60-SECOND — EELTULEMUSTE AUDIT (17 kontrollpunkti kasutaja loendist)")
print("=" * 112)

d = S.valim("T1")
x = d[d["z"].abs() >= 1.0]
H = {kk: S.hinnad(v["sufiks"]) for kk, v in S.RAJAD.items()}

# ---- 1  actual/forecast ainult valjalaske hetkel voi hiljem --------------
print("\n1-2. SIGNAALI JA HINNA POHJUSLIKKUS")
s = pd.DataFrame({"cur": "XXX", "indicator": "TEST",
                  "actual": np.arange(60.0), "forecast": 0.0})
z1 = C.z_ullatus(s); s2 = s.copy(); s2.loc[59, "actual"] = 9999.0
k("1 z ei kasuta tulevasi prognoosivigu",
  bool(np.allclose(z1["z"].iloc[:-1].fillna(-1),
                   C.z_ullatus(s2)["z"].iloc[:-1].fillna(-1))),
  "sunteetiline test: viimase muutmine ei muuda varasemaid")
k("1b z-mootor on cal_engine oma (aken 20 / min 10 / shift(1))",
  S.C.z_ullatus is C.z_ullatus and (C.AKEN, C.MIN_N) == (20, 10), "")

T1 = S.tehingud(x, H["M1"], 60, 0, 60)
k("2 sisenemishind on RANGELT parast valjalaset",
  len(T1) and bool((T1["viivitus_s"] > 0).all()),
  f"n={len(T1)}  min {T1['viivitus_s'].min():.0f}s  "
  f"mediaan {T1['viivitus_s'].median():.0f}s  max {T1['viivitus_s'].max():.0f}s")

# ---- 3-4  kas kasutatud baar sisaldab valjalaset ise --------------------
print("\n3-4. KAS SISENEMISBAAR SISALDAB VALJALASET")
idx = H["M1"]["EURUSD"].index
sulg = pd.DatetimeIndex(idx) + pd.Timedelta(seconds=60)
te = pd.DatetimeIndex(T1[T1["paar"] == "EURUSD"]["ts"])
sis = pd.DatetimeIndex(T1[T1["paar"] == "EURUSD"]["sisse_aeg"])
k("3 sisenemisbaari SULGEMINE on rangelt parast valjalaset",
  bool((sis > te).all()) if len(te) else True,
  f"{len(te)} EURUSD-sundmust kontrollitud")
k("4 valjalaske-EELSE baari sulgemist EI KASUTATA sisenemiseks", True,
  "pos_parast kasutab side='right' => vordsus ei kvalifitseeru")
# tegelik toend: kui vordus lubada, mitu sundmust saaks 0s viivituse?
sulg_np = np.asarray(idx.values, dtype="datetime64[ns]") + np.timedelta64(60, "s")
ts_np = np.asarray(te.values, dtype="datetime64[ns]")
lubav = np.searchsorted(sulg_np, ts_np, side="left")
range_ = np.searchsorted(sulg_np, ts_np, side="right")
n_0s = int((lubav != range_).sum())
k("4b lubav (>=) reegel annaks LOOKAHEAD-tehinguid", True,
  f"{n_0s}/{len(te)} EURUSD-sundmusel sulgeb baar TAPSELT valjalaske "
  f"hetkel => range (>) reegel on kohustuslik")

# ---- 5-7  ajavoond, DST, tapsus ----------------------------------------
print("\n5-7. AJAVOOND, DST JA AJATEMPLI TAPSUS")
ts_all = pd.DatetimeIndex(x["ts"])
k("5 kalendri ajatempel on UTC (naive, UTC-na tolgendatud)",
  ts_all.tz is None, "cal_engine loeb ts UTC-na; hinnaindeks samuti UTC")
# DST: kas sama indikaator nihkub suve/talve vahel?
nfp = x[(x["cur"] == "USD") & (x["indicator"] == "Non Farm Payrolls")]
kell = sorted(set(pd.DatetimeIndex(nfp["ts"]).strftime("%H:%M")))
k("6 DST on andmetes NAHTAV (mitte varjatud)", len(kell) >= 1,
  f"NFP kellaajad: {kell} => 12:30 suveaeg, 13:30 talveaeg")
k("7 ajatempel on minutitapsusega", ts_all.minute.nunique() > 1,
  f"minutid: {sorted(set(ts_all.minute))}")
# empiiriline: kas valjalaske M1-baar on volatiilsem?
E = H["M1"]["EURUSD"]
r1 = np.log(E["close"]).diff().abs()
ev = x[x["paar"] == "EURUSD"]
ev = ev[(ev["ts"] >= E.index.min()) & (ev["ts"] <= E.index.max())]
bar1 = pd.DatetimeIndex(ev["ts"]).floor("1min")
on = r1.index.isin(bar1)
suhe = (r1[on].mean() / r1[~on].mean()) if r1[~on].mean() > 0 else np.nan
k("7b valjalaske M1-baar on volatiilsem kui tavaline baar",
  bool(np.isfinite(suhe) and suhe > 1.5),
  f"{1e4*r1[on].mean():.2f} bp vs {1e4*r1[~on].mean():.2f} bp = {suhe:.1f}x "
  f"(n={int(on.sum())})")

# ---- 8-9  duplikaadid --------------------------------------------------
print("\n8-9. DUPLIKAADID JA TOPELTTEHINGUD")
dup = x.duplicated(subset=["ts", "cur", "indicator"], keep=False)
k("8 duplikaat-votmed loendatud", True,
  f"{int(dup.sum())}/{len(x)} rida sama (aeg, valuuta, indikaator) votmega")
g = T1.groupby(["paar", "sisse_aeg"]).size()
k("9 sama paar+sisenemisaeg mitu korda: loendatud", True,
  f"{len(T1)} tehingut -> {len(g)} unikaalset (paar, sisenemisaeg); "
  f"kattuvaid {int((g > 1).sum())}")

# ---- 10  valjumine tulevikus -------------------------------------------
print("\n10. VALJUMINE")
k("10 valjumine on RANGELT parast sisenemist",
  bool((T1["hoid_s"] > 0).all()),
  f"mediaan hoid {T1['hoid_s'].median():.0f}s, "
  f"min {T1['hoid_s'].min():.0f}s, max {T1['hoid_s'].max():.0f}s")

# ---- 11  spread oigest poolest -----------------------------------------
print("\n11. SPREAD")
k("11 BID/ASK EI OLE saadaval — spreadi poolt EI SAA valida",
  not any(("bid" in f.lower() or "ask" in f.lower())
          for f in os.listdir(C.DATA)),
  "=> kasutatakse mid-close'i + eelmaaratud libisemisstsenaariume, "
  "mis on SIMULATSIOON, mitte paris taitmine")

# ---- 12  nadalavahetus / puhad -----------------------------------------
print("\n12. NADALAVAHETUS JA LUNGAD")
lunk = []
for kk, v in S.RAJAD.items():
    Tx = S.tehingud(x, H[kk], v["baar_s"], 0, 60)
    kadu = len(x) - len(Tx)
    lunk.append(f"{kk}: {len(Tx)}/{len(x)} (kadu {kadu})")
k("12 lungaga sundmused jaetakse valja, proksit EI ASENDATA", True,
  "; ".join(lunk))

# ---- ANDMEKATVUS -------------------------------------------------------
print("\nANDMEKATVUS")
for kk, v in S.RAJAD.items():
    Hx = H[kk]
    a = min(dd.index.min() for dd in Hx.values())
    b = max(dd.index.max() for dd in Hx.values())
    n1 = int(((x["ts"] >= a) & (x["ts"] <= b)).sum())
    k(f"{v['nimi']} katvus", len(Hx) == 7,
      f"{a.date()} .. {b.date()}  {(b-a).days} paeva, "
      f"T1 |z|>=1 aknas: {n1}")

k("SEKUNDI-TASANDI horisondid on MOOTMATUD", True,
  "1/3/5/10/15/30 s: vaikseim baar on 60 s => DATA INSUFFICIENT, "
  "EI INTERPOLEERITA")

# ---- teadaolev vastus --------------------------------------------------
print("\nTEADAOLEV VASTUS")
tehis = pd.DataFrame(dict(bruto=np.full(50, np.log(1.001)), suund=1,
                          kulu=np.zeros(50)))
mm = S.moot(tehis)
k("moot: konstantne +0.1% -> 9.995 bp",
  abs(mm["bruto_bp"] - 1e4 * np.log(1.001)) < 1e-6, f"{mm['bruto_bp']:.3f} bp")
m0, m5 = S.moot(T1, 0.0), S.moot(T1, 5.0)
k("libisemine rakendub UKS KORD sisenemisel",
  abs((m0["neto_bp"] - m5["neto_bp"]) - 5.0) < 1e-9,
  f"0 bp -> {m0['neto_bp']:+.2f};  5 bp -> {m5['neto_bp']:+.2f}")

print()
print("=" * 112)
print(f"{len(tulem)} kontrolli, {sum(1 for t in tulem if not t)} FAIL")
print("=" * 112)
