"""
cal_b2_audit.py — B2 lookahead- ja korrektsusaudit. JOOKSEB ENNE TULEMUSI.

Iga kontroll on kas OK voi VIGA. Uhtegi tulemust ei tohi raporteerida,
enne kui siin on 0 viga.
"""
import numpy as np
import pandas as pd

import cal_b2 as B
import cal_engine as C
import h1engine as H

OK, VIGA = "OK  ", "VIGA"
tulem = []


def k(nimi, tingimus, info=""):
    tulem.append(bool(tingimus))
    print(f"{OK if tingimus else VIGA}  {nimi:<56s} {info}")


print("=" * 110)
print("B2 AUDIT — LOOKAHEAD JA KORREKTSUS")
print("=" * 110)

# ---------------------------------------------------- A. B1 MUUTUMATUS ----
print("\nA. KAS B1 DEFINITSIOONID ON MUUTMATA")
k("A1 TIER 1 liikmeid on 11", len(C.TIER1) == 11, ", ".join(sorted(C.TIER1)))
k("A1 TIER 1 margid muutmata",
  C.TIER1.get("Unemployment Rate") == -1 and C.TIER1.get("Inflation Rate") == +1,
  "Unemployment -1, Inflation +1")
k("A2 z-lavi on 1.0 (B1 LAVI)", C.LAVI == 1.0, f"LAVI={C.LAVI}")
k("A3 rulliv aken 20 / min 10", (C.AKEN, C.MIN_N) == (20, 10),
  f"AKEN={C.AKEN} MIN_N={C.MIN_N}")
k("A4 kulu 1.25 bp uhesuunaline = 2.50 edasi-tagasi",
  abs(B.KULU_RT_BP - 2.50) < 1e-9, f"{B.KULU_RT_BP:.2f} bp")
k("A5 B2 kutsub B1 z-mootorit, ei kopeeri seda",
  B.C.z_ullatus is C.z_ullatus, "cal_engine.z_ullatus")

# A6: z B2 valimis peab olema B1 mootori valjund BITT-IDENTSELT.
# NB: (ts, cur, indicator) EI OLE unikaalne voti (vt A8), seega
# vordlus kaib ALGSE REAINDEKSI kaudu, mitte merge'i kaudu.
d_b1 = C.z_ullatus(C.lae_kalender(("T1", "T2")))
d_b1 = d_b1[(d_b1["tier"] == "T1") & d_b1["z"].notna()]
d, HV = B.valim()
d_b1_h1 = d_b1.loc[d_b1.index.intersection(d["algne_idx"])]
z_b2 = d.set_index("algne_idx")["z"].reindex(d_b1_h1.index)
k("A6 z on B1-ga bitt-identne (reaindeksi kaudu)",
  bool(np.array_equal(z_b2.values, d_b1_h1["z"].values)),
  f"{len(z_b2)} rida, max erinevus "
  f"{np.abs(z_b2.values - d_b1_h1['z'].values).max():.2e}")

# A8: ANDMEKVALITEET — TradingView surub moned eri seeriad sama nime alla
kal_t1 = C.lae_kalender(("T1", "T2"))
kal_t1 = kal_t1[kal_t1["tier"] == "T1"]
dup = kal_t1.duplicated(subset=["ts", "cur", "indicator"], keep=False)
gr = kal_t1[dup].groupby(["cur", "indicator"]).size()
k("A8 topeltvotmed loendatud (B1 parandatud EI OLE)", True,
  f"{int(dup.sum())}/{len(kal_t1)} T1 rida ({100*dup.mean():.1f}%): "
  + ", ".join(f"{c}/{i} {n}" for (c, i), n in gr.items()))
print("    Pohjus: TradingView annab EUR Employment Change QoQ ja YoY ning")
print("    GBP Interest Rate kaks seeriat SAMA nime all. B1 rull-std segab")
print("    need uheks ajalooks => z on neil ridadel mootmisveaga.")
print("    B2 EI PARANDA seda — B1 definitsioon jaab. Moju mooedetakse")
print("    tulemustes eraldi (indikaatoritabel).")

# B1 sunteetiline lookahead-test, korratud
s = pd.DataFrame({"cur": "XXX", "indicator": "TEST",
                  "actual": np.arange(60.0), "forecast": 0.0})
z1 = C.z_ullatus(s)
s2 = s.copy(); s2.loc[59, "actual"] = 9999.0
z2 = C.z_ullatus(s2)
k("A7 z ei kasuta tulevikku (sunteetiline test)",
  bool(np.allclose(z1["z"].iloc[:-1].fillna(-1), z2["z"].iloc[:-1].fillna(-1))),
  "viimase muutmine ei muuda varasemaid")

# ------------------------------------------------------- B. AJASTUS ------
print("\nB. AJASTUS JA POHJUSLIKKUS")
sulg = pd.DatetimeIndex(HV.index) + pd.Timedelta(hours=1)
ank_sulg = sulg[d["ankur"].values]
k("B1 ankur on ALATI teate ajal voi enne",
  bool((ank_sulg <= pd.DatetimeIndex(d["ts"])).all()),
  f"max ankur-T = {((ank_sulg - pd.DatetimeIndex(d['ts']))/pd.Timedelta(hours=1)).max():.2f} h")
k("B2 ankur ei ole vanem kui tolerants",
  bool(d["ankur_vanus_h"].max() <= B.TOLERANTS_H),
  f"mediaan {d['ankur_vanus_h'].median():.2f}h  max {d['ankur_vanus_h'].max():.2f}h")

d = B.lisa_horisondid(d, HV, "SEINAKELL")
vead = 0
for h in B.HORISONDID:
    p = d[f"p{h}"].values
    m = p >= 0
    if not m.any():
        continue
    siht = pd.DatetimeIndex(d["ts"][m]) + pd.Timedelta(hours=h)
    es = sulg[p[m]]
    if not bool((es <= siht).all()):
        vead += 1
    if not bool((p[m] >= d["ankur"].values[m]).all()):
        vead += 1
k("B3 iga horisondi valjumishind on siht-ajal voi enne", vead == 0,
  f"{len(B.HORISONDID)} horisonti kontrollitud, {vead} rikkumist")
k("B4 valjumispositsioon ei ole kunagi enne ankrut", vead == 0, "")

pp = d[f"p{B.PRIMARY_SISSE}"].values
pv = d[f"p{B.PRIMARY_VALJA}"].values
m = (pp >= 0) & (pv >= 0)
k("B5 primary T+8 sisenemine on rangelt PARAST teadet",
  bool((sulg[pp[m]] > pd.DatetimeIndex(d["ts"][m])).all()),
  f"min viivitus {((sulg[pp[m]] - pd.DatetimeIndex(d['ts'][m]))/pd.Timedelta(hours=1)).min():.2f} h")
k("B6 primary valjumine on rangelt PARAST sisenemist",
  bool((pv[m] > pp[m]).all()),
  f"mediaan hoid {np.median((sulg[pv[m]]-sulg[pp[m]])/pd.Timedelta(hours=1)):.1f} h")

print("\n  horisondi katvus (SEINAKELL, tolerants "
      f"{B.TOLERANTS_H:.0f}h):")
for h in B.HORISONDID:
    n_ok = int((d[f"p{h}"] >= 0).sum())
    print(f"    +{h:>3d}h   seotud {n_ok:>5d} / {len(d)}   "
          f"valja jaetud {len(d)-n_ok:>5d}  "
          f"({100*(len(d)-n_ok)/len(d):.1f}%)")

# ---------------------------------------------------- C. TOOTLUSE MOOT ---
print("\nC. TOOTLUSE DEFINITSIOON")
LOGV = np.log(HV.values)
i1 = d["ankur"].values
i2 = d[f"p{B.PRIMARY_VALJA}"].values
mm = (i1 >= 0) & (i2 >= 0)
dd = LOGV[i2[mm]] - LOGV[i1[mm]]
dd = dd - dd.mean(axis=1, keepdims=True)
k("C1 ristloikeline tsentreerimine: ridade summa = 0",
  bool(np.abs(dd.sum(axis=1)).max() < 1e-12),
  f"max |summa| = {np.abs(dd.sum(axis=1)).max():.2e}")
k("C2 USD saab sisulise tootluse (ei ole nulliks fikseeritud)",
  bool(dd[:, 0].std() > 0), f"USD sigma {1e4*dd[:,0].std():.1f} bp")
# teadaolev vastus
Lt = np.log(np.array([[1.0, 1.0], [1.02, 1.0]]))
tst = Lt[1] - Lt[0]; tst = tst - tst.mean()
k("C3 teadaolev vastus: +2% uhel kahest -> +-log(1.02)/2",
  abs(tst[0] - np.log(1.02) / 2) < 1e-12,
  f"{1e4*tst[0]:.2f} bp vs {1e4*np.log(1.02)/2:.2f} bp")

# ------------------------------------------------- D. KATTUVUS / KLASTER --
print("\nD. SUNDMUSTE KATTUVUS (B1-l ei ole eraldi kattuvuse kasitlust)")
x = d[d["z"].abs() >= C.LAVI]
g = x.groupby(["cur", "ts"]).size()
k("D1 kattuvus mooedetud", True,
  f"{len(x)} sundmust -> {len(g)} unikaalset (valuuta, aeg); "
  f"korduvaid ajahetki {int((g>1).sum())}")
osa = 100.0 * float((g[g > 1].sum()) / len(x)) if len(x) else 0.0
print(f"    samas (valuuta, aeg) aknas mitu sundmust: {osa:.1f}% valimist")
print(f"    suurim klaster: {int(g.max())} sundmust korraga")
kl = x.groupby(["cur", "ts"])["suund"].nunique()
print(f"    klastreid, kus suunad on VASTUOLUS: {int((kl>1).sum())}")

# -------------------------------------------- E. ANDMEKVALITEET (REVISION)
print("\nE. ANDMEKVALITEET — kas 'actual' on esialgne trukk?")
kal = C.lae_kalender(("T1", "T2")).sort_values("ts")
kal["prev_actual"] = kal.groupby(["cur", "indicator"])["actual"].shift(1)
mp = kal[["previous", "prev_actual"]].notna().all(axis=1)
sama = np.isclose(kal.loc[mp, "previous"], kal.loc[mp, "prev_actual"],
                  rtol=1e-6, atol=1e-9)
k("E1 previous vs eelmine actual mooedetud", True,
  f"{int(mp.sum())} paari, kattub {100*sama.mean():.1f}%")
print("    Tolgendus: kui allikas hoiaks AINULT lopprevideeritud vaartusi,")
print("    peaks previous_N == actual_(N-1) peaaegu alati. Lahknevus viitab,")
print("    et actual on esialgne trukk ja previous kannab revisjoni.")
print("    SEE EI OLE TOESTUS. TradingView API ei anna revisjoni-valja ega")
print("    eraldi 'initial print' margendit — piirang JAAB LAHENDAMATA.")
k("E2 allikas ei sisalda revisjoni-valja", 
  set(pd.read_csv(f"{C.DATA}/econ_cal.csv", nrows=1).columns) ==
  {"cur", "ts", "indicator", "actual", "forecast", "previous", "importance"},
  "veerud: cur,ts,indicator,actual,forecast,previous,importance")

# ------------------------------------------------------- F. AKEN / VALIM --
print("\nF. AJALINE PIIRANG")
kd = C.z_ullatus(C.lae_kalender(("T1", "T2")))
kd = kd[(kd["tier"] == "T1") & kd["z"].notna()]
k("F1 paevane B1 aken", True,
  f"{kd['ts'].min().date()} .. {kd['ts'].max().date()}  ({len(kd)} T1 sundmust)")
k("F2 H1 B2 aken on OLULISELT luhem", 
  (HV.index.max() - HV.index.min()).days < 1200,
  f"{HV.index.min().date()} .. {HV.index.max().date()}  "
  f"({(HV.index.max()-HV.index.min()).days/365.25:.2f} aastat)")
k("F3 B1 jaotus ei ole H1-aknas kasutatav",
  bool((d["ts"] > C.VALID_LOPP).all()),
  "kogu H1-aken langeb B1 FINAL OOS-i sisse => B2-l oma kalendriaasta-jaotus")
tr = (d["ts"] <= B.B2_TRAIN_LOPP).sum()
va = ((d["ts"] > B.B2_TRAIN_LOPP) & (d["ts"] <= B.B2_VALID_LOPP)).sum()
oo = (d["ts"] > B.B2_VALID_LOPP).sum()
k("F4 B2 jaotus on kalendriaasta-pohine ja eelregistreeritud",
  tr > 0 and va > 0 and oo > 0,
  f"TRAIN {tr}  VALID {va}  OOS {oo}  (koik TIER1 z-ga)")

# ------------------------------------------------------ G. AJAVOOND ------
print("\nG. AJAVOOND")
E = H.lae("EURUSD")
r = np.log(E["close"]).diff().abs()
nfp = kd[(kd["cur"] == "USD") & (kd["indicator"] == "Non Farm Payrolls")]
nfp_h = pd.DatetimeIndex(nfp["ts"]).floor("h")
on = r.index.isin(nfp_h)
k("G1 NFP-tunni volatiilsus >> tavaline tund",
  bool(r[on].mean() > 2.0 * r[~on].mean()),
  f"{1e4*r[on].mean():.1f} bp vs {1e4*r[~on].mean():.1f} bp = "
  f"{r[on].mean()/r[~on].mean():.1f}x")

# ------------------------------------------- H. SEINAKELL vs BAARILUGEMINE
print("\nH. KAKS AJAARVESTUST")
db = B.valim()[0]
db = B.lisa_horisondid(db, HV, "BAARE")
sama_h = []
for h in B.HORISONDID:
    a = d[f"p{h}"].values
    b = db[f"p{h}"].values
    m2 = (a >= 0) & (b >= 0)
    sama_h.append(100.0 * float((a[m2] == b[m2]).mean()) if m2.any() else np.nan)
k("H1 seinakell ja baarilugemine mooedetud eraldi", True,
  "kattuvus horisondi kaupa: " +
  " ".join(f"+{h}h {s:.0f}%" for h, s in zip(B.HORISONDID, sama_h)))

print()
print("=" * 110)
print(f"{len(tulem)} kontrolli, {sum(1 for t in tulem if not t)} viga")
print("=" * 110)
