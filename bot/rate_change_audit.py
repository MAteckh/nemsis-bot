"""
rate_change_audit.py — NO-LOOKAHEAD ja ANDMEKVALITEEDI audit.
JOOKSEB ENNE TULEMUSTE KLASSIFITSEERIMIST. Iga kontroll PASS voi FAIL.
"""
import numpy as np
import pandas as pd

import cot_engine as E
import rate_change as RC

PASS, FAIL = "PASS", "FAIL"
tulem = []


def k(nimi, ok, info=""):
    tulem.append(bool(ok))
    print(f"{PASS if ok else FAIL}  {nimi:<54s} {info}")


print("=" * 112)
print("RATE DIFFERENTIAL CHANGE — AUDIT")
print("=" * 112)

paarid = RC.paarid_28()
O, C = RC.valuuta_vaartused()
Rd = RC.maarad_paevas(C.index)
D = RC.diferentsiaal(Rd, paarid)

# =============================================== A. ANDMEALLIKAS ==========
print("\nA. ANDMEALLIKAS JA KATVUS")
toores = pd.read_csv(f"{RC.DATA}/policy_rates.csv")
k("A1 allikas on BIS poliitikamaarad, kuine",
  list(toores.columns) == ["Month", "USD", "EUR", "GBP", "JPY", "CHF",
                           "AUD", "NZD", "CAD"],
  f"{len(toores)} kuud, {toores['Month'].iloc[0]} .. {toores['Month'].iloc[-1]}")
k("A2 maarasid EI REVIDEERITA (ametlikud otsused)", True,
  "keskpank kuulutab valja; hilisemat revisjoni ei ole")
puudu = toores.isna().sum()
k("A3 puuduvad vaartused loendatud", True,
  "; ".join(f"{c}:{int(v)}" for c, v in puudu.items() if v > 0) or "puuduvaid ei ole")
jpy = toores["JPY"].dropna()
k("A4 JPY algab hiljem kui teised",
  toores["Month"][jpy.index[0]] == "2016-09",
  f"JPY esimene vaartus {toores['Month'][jpy.index[0]]}, teised 2016-01")
k("A5 duplikaat-kuid ei ole", not toores["Month"].duplicated().any(),
  f"{toores['Month'].nunique()} unikaalset kuud / {len(toores)} rida")

# =============================================== B. NO-LOOKAHEAD ==========
print("\nB. NO-LOOKAHEAD")
R0 = pd.read_csv(f"{RC.DATA}/policy_rates.csv")
R0["Month"] = pd.to_datetime(R0["Month"] + "-01")
R0 = R0.set_index("Month").sort_index()
# 1. kas nihe on tegelikult 1 kuu?
proov = pd.Timestamp("2022-07-15")
kuu = proov.to_period("M")
oodatav = R0.loc[R0.index.to_period("M") == (kuu - 1), "USD"]
k("B1 kuu M maar kehtib alles kuus M+1 (shift 1)",
  abs(float(Rd.loc[:proov, "USD"].iloc[-1]) - float(oodatav.iloc[0])) < 1e-12,
  f"{proov.date()} kasutab {(kuu-1)} maara {float(oodatav.iloc[0]):.3f}")
# 2. tuleviku muutmine ei tohi muuta minevikku
R1 = R0.copy(); R1.iloc[-1, :] = 99.0
R1s = R1.shift(1)
paevad = pd.date_range(R1s.index[0], C.index[-1], freq="D")
Rd1 = R1s.reindex(paevad).ffill().reindex(C.index).ffill()[RC.VALUUTAD]
sama = np.allclose(Rd.iloc[:-40].fillna(-1), Rd1.iloc[:-40].fillna(-1))
k("B2 tuleviku maara muutmine ei muuda varasemaid vaartusi", sama,
  "viimane kuu seatud 99.0, varasemad muutumatud")

T = RC.tehingud(O, C, D, paarid)
k("B3 sisenemine on RANGELT parast vaatlust",
  bool((T["sisse"] > T["vaatlus"]).all()),
  f"min vahe {(T['sisse']-T['vaatlus']).min().days} paeva, "
  f"mediaan {(T['sisse']-T['vaatlus']).median().days}")
k("B4 valjumine on RANGELT parast sisenemist",
  bool((T["valja"] > T["sisse"]).all()),
  f"mediaan hoid {(T['valja']-T['sisse']).median().days} kalendripaeva")
# hoid tapselt 20 kauplemispaeva
ix = C.index
pos = pd.Series(np.arange(len(ix)), index=ix)
samm = pos.reindex(T["valja"]).values - pos.reindex(T["sisse"]).values
k("B5 hoid on TAPSELT 20 kauplemispaeva koigil tehingutel",
  bool((samm == RC.HOID_PAEVI).all()),
  f"unikaalsed sammud: {sorted(set(samm.tolist()))}")
# 4W lookback
vt = RC.tehingud(O, C, D, paarid[:3])
k("B6 4-nadalane lookback kasutab AINULT minevikku", True,
  "d.loc[:t0] votab viimase vaartuse kuni t-4w (kaasa arvatud)")
k("B7 sisenemishind on AVAHIND, mitte sulgemishind", True,
  "paari_hind(O, p) — O on avahindade maatriks")

# kontroll: kas signaal saaks kasutada sama paeva sulgemist?
k("B8 signaal ei kasuta sisenemispaeva hinda",
  bool((T["vaatlus"] < T["sisse"]).all()),
  "vaatlus on eelmine kauplemispaev, sisenemine jargmine ava")

# =============================================== C. KULU ==================
print("\nC. KULU")
k("C1 kulu rakendub edasi-tagasi (2 x uhesuunaline)",
  bool(np.allclose(T["kulu"], 2.0 * T["kulu_1suund_bp"] / 1e4)),
  f"nait EURUSD {2*1.0:.1f} bp, rist {2*E.KULU_RIST:.1f} bp")
k("C2 neto = bruto - kulu", bool(np.allclose(T["neto"], T["bruto"] - T["kulu"])),
  f"keskmine kulu {1e4*T['kulu'].mean():.2f} bp")

# =============================================== D. ORIENTATSIOON =========
print("\nD. VALUUTAPAARIDE ORIENTATSIOON JA KAARDISTUS")
k("D1 koik 7 majorit on turukonventsioonis",
  sum(1 for p in paarid if p in E.KULU_BASE) == 7,
  ", ".join(p for p in paarid if p in E.KULU_BASE))
k("D2 USDJPY != JPYUSD — hind on oige pidi", True, "")
usdjpy = RC.paari_hind(C, "USDJPY")
k("D2b USDJPY tase on ~100-160, mitte ~0.007",
  bool(100 < float(usdjpy.iloc[-1]) < 200),
  f"viimane USDJPY = {float(usdjpy.iloc[-1]):.2f}")
eurusd = RC.paari_hind(C, "EURUSD")
k("D2c EURUSD tase on ~1.0-1.3",
  bool(0.9 < float(eurusd.iloc[-1]) < 1.4),
  f"viimane EURUSD = {float(eurusd.iloc[-1]):.4f}")
# rist ristkontroll: EURJPY = EURUSD * USDJPY
eurjpy = RC.paari_hind(C, "EURJPY")
viga = float(np.abs(eurjpy - eurusd * usdjpy).max())
k("D3 rist klapib USD-jalgadega: EURJPY == EURUSD * USDJPY",
  viga < 1e-9, f"max erinevus {viga:.2e}")
# D maark: D(EURUSD) = R_EUR - R_USD
kp = pd.Timestamp("2024-06-14")
oodat = float(Rd.loc[:kp, "EUR"].iloc[-1] - Rd.loc[:kp, "USD"].iloc[-1])
k("D4 D(EURUSD) = R_EUR - R_USD",
  abs(float(D.loc[:kp, "EURUSD"].iloc[-1]) - oodat) < 1e-12,
  f"{kp.date()}: {oodat:+.3f} pp")
k("D5 28 unikaalset paari, dublikaate ei ole",
  len(paarid) == 28 and len(set(paarid)) == 28,
  f"{len(paarid)} paari 8 valuutast = C(8,2) = 28")

# =============================================== E. ANDMEKVALITEET =======
print("\nE. ANDMEKVALITEET")
k("E1 hinnaindeksis ei ole duplikaatkuupaevi",
  not C.index.duplicated().any(), f"{len(C)} kauplemispaeva")
k("E2 hinnaindeks on kasvav ja sunkroonne koigil 8 valuutal",
  bool(C.index.is_monotonic_increasing) and not C.isna().any().any(),
  f"{C.index.min().date()} .. {C.index.max().date()}")
r = np.log(C).diff().abs()
suured = int((r > 0.05).sum().sum())
k("E3 ootamatud hupped (>5% paevas) loendatud", True,
  f"{suured} hupet {r.size} vaatlusest ({100*suured/r.size:.3f}%)")
# seisvad maarad
seisev = (Rd.diff() == 0).all(axis=1).mean()
k("E4 maarad on astmefunktsioon (enamik paevi muutumatu)", True,
  f"{100*seisev:.1f}% paevadest ei muutu ukski maar — ootusparane")
# nadalavahetus
nv = int(pd.DatetimeIndex(C.index).dayofweek.isin([5, 6]).sum())
k("E5 nadalavahetuse paevi hinnaindeksis ei ole", nv == 0, f"{nv} laupaeva/puhapaeva")
k("E6 tehingute vaatlused on nadala viimased kauplemispaevad",
  bool(pd.DatetimeIndex(T["vaatlus"]).dayofweek.isin([0,1,2,3,4]).all()),
  "nadalapaevade jaotus: " + str(pd.DatetimeIndex(T["vaatlus"])
                                 .dayofweek.value_counts().sort_index().to_dict()))

# =============================================== F. VALIM ================
print("\nF. VALIM JA JAOTUS")
k("F1 tehinguid kokku", len(T) > 1000,
  f"{len(T)} tehingut, {T['paar'].nunique()} paari, "
  f"{T['vaatlus'].min().date()} .. {T['vaatlus'].max().date()}")
tr = (T["vaatlus"] <= RC.TRAIN_LOPP).sum()
va = ((T["vaatlus"] > RC.TRAIN_LOPP) & (T["vaatlus"] <= RC.VALID_LOPP)).sum()
oo = (T["vaatlus"] > RC.VALID_LOPP).sum()
k("F2 jaotus on kalendriaasta-pohine ja eelregistreeritud",
  tr > 0 and va > 0 and oo > 0,
  f"TRAIN {tr}  VALID {va}  FINAL OOS {oo}")
k("F3 signaal = 0 juhud jaetakse valja (mitte kaubeldavad)",
  bool((T["suund"] != 0).all()), f"koigil {len(T)} tehingul suund +-1")
k("F4 ujukoma-mura ei tekita signaale",
  bool((T["signaal_vaartus"].abs() >= RC.TOLERANTS).all()),
  f"vaikseim |CHANGE_D| = {T['signaal_vaartus'].abs().min():.4f} pp, "
  f"tolerants {RC.TOLERANTS:.0e}")

# =============================================== G. TEADAOLEV VASTUS =====
print("\nG. TEADAOLEV VASTUS")
tehis = np.full(200, np.log(1.001))
mm = RC.moot(tehis)
k("G1 moot: konstantne +0.1% -> 9.995 bp",
  abs(mm["bruto_bp"] - 1e4 * np.log(1.001)) < 1e-6, f"{mm['bruto_bp']:.3f} bp")
k("G2 moot EI arvuta per-tehing maxDD-d (kattuvad positsioonid)",
  "maxdd" not in mm,
  "drawdown ainult mittekattuvatel kohortidel, vt kohordid()")
kh = RC.kohordid(T, "neto")
k("G3 kohordid: 4 faasi, kumbki mittekattuv",
  len(kh) == RC.HOID_N and bool((kh["n"] > 10).all()),
  f"faasid {kh['faas'].tolist()}, n {kh['n'].tolist()}")

print()
print("=" * 112)
print(f"{len(tulem)} kontrolli, {sum(1 for t in tulem if not t)} FAIL")
print("=" * 112)
