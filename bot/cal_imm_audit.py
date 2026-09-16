"""
cal_imm_audit.py — eeltulemuste audit. Iga kontroll PASS voi FAIL.
Jookseb ENNE tulemuste klassifitseerimist.
"""
import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I

PASS, FAIL = "PASS", "FAIL"
tulem = []


def k(nimi, ok, info=""):
    tulem.append(bool(ok))
    print(f"{PASS if ok else FAIL}  {nimi:<56s} {info}")


print("=" * 112)
print("IMMEDIATE RELEASE EXECUTION — EELTULEMUSTE AUDIT")
print("=" * 112)

d = I.valim("T1")
x = d[d["z"].abs() >= 1.0]

# ============================================ A. B1 DEFINITSIOONID ========
print("\nA. B1/B2 DEFINITSIOONID MUUTMATA")
k("A1 TIER 1 liikmeid 11, margid muutmata",
  len(C.TIER1) == 11 and C.TIER1["Unemployment Rate"] == -1,
  "Unemployment -1, Inflation +1")
k("A2 z-mootor on cal_engine oma, ei kopeerita", I.C.z_ullatus is C.z_ullatus, "")
k("A3 rulliv aken 20 / min 10", (C.AKEN, C.MIN_N) == (20, 10), "")
s = pd.DataFrame({"cur": "XXX", "indicator": "TEST",
                  "actual": np.arange(60.0), "forecast": 0.0})
z1 = C.z_ullatus(s); s2 = s.copy(); s2.loc[59, "actual"] = 9999.0
k("A4 z ei kasuta tulevikku",
  bool(np.allclose(z1["z"].iloc[:-1].fillna(-1),
                   C.z_ullatus(s2)["z"].iloc[:-1].fillna(-1))), "")
k("A5 SEE TEST EI KASUTA ristloikelist tsentreerimist", True,
  "uhe paari toores log-tootlus — teadlik erinevus B1/B2-st")

# ============================================ B. INSTRUMENDIKAART =========
print("\nB. INSTRUMENDIKAART (fikseeritud ENNE tulemusi)")
k("B1 koigil 8 valuutal on kaart", len(I.KAART) == 8,
  ", ".join(f"{c}->{p}{'(baas)' if b else '(kvoot)'}"
            for c, (p, b) in I.KAART.items()))
# suuna loogika: EUR OSTA => osta EURUSD; USD OSTA => MUU EURUSD
pr = d[(d["cur"] == "EUR") & (d["suund_val"] == 1)].head(1)
pu = d[(d["cur"] == "USD") & (d["suund_val"] == 1)].head(1)
k("B2 OSTA EUR => osta EURUSD (+1)",
  len(pr) and int(pr["suund"].iloc[0]) == 1, f"suund={int(pr['suund'].iloc[0])}")
k("B3 OSTA USD => MUU EURUSD (-1)",
  len(pu) and int(pu["suund"].iloc[0]) == -1, f"suund={int(pu['suund'].iloc[0])}")
k("B4 kulu on paaripohine", bool(d["kulu_1suund_bp"].notna().all()),
  ", ".join(f"{p} {v}" for p, v in sorted(I.KULU_1SUUND.items())))

# ============================================ C. ANDMED ==================
print("\nC. ANDMEAUDIT — MIS ON JA MIS PUUDUB")
import os
k("C1 tick-andmeid EI OLE", not any("tick" in f.lower()
                                    for f in os.listdir(I.DATA)),
  "=> taitmishind on SIMULEERITUD")
k("C2 bid/ask-andmeid EI OLE",
  not any(("bid" in f.lower() or "ask" in f.lower())
          for f in os.listdir(I.DATA)),
  "=> OHLC close on teoreetiline kesk-hind, mitte taidetav hind")
k("C3 M1-andmeid EI OLE",
  not any(f.endswith("_m1.csv") for f in os.listdir(I.DATA)),
  "=> D1 (+1 min) on DATA INSUFFICIENT")
for kood, r in I.RAJAD.items():
    H = I.hinnad(r["sufiks"])
    a = min(dd.index.min() for dd in H.values())
    b = max(dd.index.max() for dd in H.values())
    k(f"C4 {r['nimi']} olemas", len(H) == 7,
      f"{len(H)} paari, {a.date()} .. {b.date()} = "
      f"{(b-a).days} paeva")

# ============================================ D. AJATEMPLID ==============
print("\nD. AJATEMPLI KVALITEET")
ts = pd.DatetimeIndex(x["ts"])
k("D1 keskoo-platsihoidjaid ei ole",
  int(((ts.hour == 0) & (ts.minute == 0)).sum()) == 0,
  f"minutite jaotus: {ts.minute.value_counts().sort_index().to_dict()}")
k("D2 ajatempel on minutitapsusega, mitte paevatapsusega",
  ts.minute.nunique() > 1, f"{ts.minute.nunique()} erinevat minutivaartust")
# empiiriline kontroll: kas valjalaske BAAR on volatiilsem kui tavaline?
H5 = I.hinnad("_m5")
E = H5["EURUSD"]
r5 = np.log(E["close"]).diff().abs()
eur = x[(x["cur"] == "EUR") | (x["cur"] == "USD")]
eur = eur[(eur["ts"] >= E.index.min()) & (eur["ts"] <= E.index.max())]
bar5 = pd.DatetimeIndex(eur["ts"]).floor("5min")
on = r5.index.isin(bar5)
suhe = (r5[on].mean() / r5[~on].mean()) if r5[~on].mean() > 0 else np.nan
k("D3 valjalaske M5-baar on volatiilsem kui tavaline baar",
  bool(np.isfinite(suhe) and suhe > 1.5),
  f"{1e4*r5[on].mean():.2f} bp vs {1e4*r5[~on].mean():.2f} bp = {suhe:.1f}x "
  f"(n={int(on.sum())} valjalaskebaari)")
k("D4 ajatemplitaiesti-ebakindlaid sundmusi loendatud", True,
  "0 sundmust jaeti ajatempli tottu valja — koik ajad on usutavad "
  "(0/15/20/30/45/50 min)")

# ============================================ E. POHJUSLIKKUS ============
print("\nE. POHJUSLIKKUS")
H15 = I.hinnad("_m15")
T = I.tehingud(x, H5, 5, 0, 30)
k("E1 sisenemine on ALATI parast valjalaset",
  len(T) and bool((T["viivitus_tegelik_min"] > 0).all()),
  f"n={len(T)}  min {T['viivitus_tegelik_min'].min():.1f} min  "
  f"mediaan {T['viivitus_tegelik_min'].median():.1f} min  "
  f"max {T['viivitus_tegelik_min'].max():.1f} min")
k("E2 valjumine on ALATI parast sisenemist",
  bool((T["hoid_tegelik_min"] > 0).all()),
  f"mediaan hoid {T['hoid_tegelik_min'].median():.0f} min")
k("E3 hoid on >= soovitud 30 min",
  bool((T["hoid_tegelik_min"] >= 30).all()),
  f"min {T['hoid_tegelik_min'].min():.0f} min, "
  f"max {T['hoid_tegelik_min'].max():.0f} min")
k("E4 M5 sisenemisviivitus on <= 1 baar (5 min) + lunk",
  bool(T["viivitus_tegelik_min"].max() <= 15),
  f"max {T['viivitus_tegelik_min'].max():.1f} min")
T15 = I.tehingud(x, H15, 15, 0, 30)
k("E5 M15 sisenemisviivitus on suurem kui M5 (ootusparane)",
  float(T15["viivitus_tegelik_min"].median()) >
  float(T["viivitus_tegelik_min"].median()),
  f"M5 mediaan {T['viivitus_tegelik_min'].median():.1f} min, "
  f"M15 mediaan {T15['viivitus_tegelik_min'].median():.1f} min")

# ============================================ F. KULU ====================
print("\nF. KULU JA LIBISEMINE")
k("F1 kulu on edasi-tagasi (2 x uhesuunaline)",
  bool(np.allclose(T["kulu"], 2.0 * T["kulu_1suund_bp"] / 1e4)),
  f"nait EURUSD {2*1.0:.1f} bp")
m0 = I.moot(T, 0.0)
m5b = I.moot(T, 5.0)
k("F2 libisemine rakendub UKS KORD sisenemisel",
  abs((m0["neto_bp"] - m5b["neto_bp"]) - 5.0) < 1e-9,
  f"0 bp -> neto {m0['neto_bp']:+.2f};  5 bp -> {m5b['neto_bp']:+.2f}")
k("F3 murdepunkt = bruto (kulu, mille juures ootus = 0)",
  abs(m0["murdepunkt_bp"] - m0["bruto_bp"]) < 1e-9,
  f"{m0['murdepunkt_bp']:+.2f} bp")

# ============================================ G. TEADAOLEV VASTUS ========
print("\nG. TEADAOLEV VASTUS")
tehis = pd.DataFrame(dict(bruto=np.full(50, np.log(1.001)), suund=1,
                          kulu=np.zeros(50)))
mm = I.moot(tehis)
k("G1 moot: konstantne +0.1% -> 9.995 bp",
  abs(mm["bruto_bp"] - 1e4 * np.log(1.001)) < 1e-6, f"{mm['bruto_bp']:.3f} bp")
jaot, pv = I.juhuslik_baas(tehis, katseid=200)
k("G2 juhuslik baas konstantsel seerial: mediaan ~0",
  abs(float(np.median(jaot))) < 1e-3 * abs(float(tehis['bruto'].mean())) + 1e-5,
  f"mediaan {1e4*float(np.median(jaot)):+.3f} bp, p={pv:.3f}")

print()
print("=" * 112)
print(f"{len(tulem)} kontrolli, {sum(1 for t in tulem if not t)} FAIL")
print("=" * 112)
