"""
cal_imm_run.py — IMMEDIATE RELEASE EXECUTION, tulemused.
Jookseb PARAST cal_imm_audit.py-d (29 kontrolli, 0 FAIL).
"""
import math
import os

import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I

JUUR = I.JUUR
VALJUND = {}


def salvesta(nimi, read):
    df = pd.DataFrame(read)
    df.to_csv(os.path.join(JUUR, nimi), index=False)
    VALJUND[nimi] = len(df)
    return df


def rm(m, extra=None):
    if m is None:
        return dict(extra or {})
    d = {kk: m[kk] for kk in ("n", "bruto_bp", "med_bp", "wr", "v_bp", "k_bp",
                              "pf", "sd_bp", "t", "p", "kulu_bp", "lib_bp",
                              "neto_bp")}
    d.update(extra or {})
    return d


d_all = I.valim("T1")
d_t2 = I.valim("T2")
H = {kood: I.hinnad(r["sufiks"]) for kood, r in I.RAJAD.items()}
BAAR = {kood: r["baar_min"] for kood, r in I.RAJAD.items()}

print("=" * 112)
print("IMM.0  ANDMED, VALIM, EELREGISTREERITUD SPETSIFIKATSIOON")
print("=" * 112)
print("  UUS KUSIMUS (mitte B1 ega B2): kas makroteate hupe on TAIDETAV?")
print("  B1 = paevane efekt. B2 = viivitatud efekt (T+8h->T+32h). Neid EI SEGATA.")
print()
print("  ANDMEAUDIT:")
print("    tick / bid-ask / M1   EI OLE  => taitmishind on SIMULEERITUD,")
print("                                     D1 (+1 min) = DATA INSUFFICIENT")
for kood, r in I.RAJAD.items():
    Hx = H[kood]
    a = min(x.index.min() for x in Hx.values())
    b = max(x.index.max() for x in Hx.values())
    n1 = int(((d_all["z"].abs() >= 1) & (d_all["ts"] >= a)
              & (d_all["ts"] <= b)).sum())
    print(f"    {r['nimi']:<12s} {a.date()} .. {b.date()}  "
          f"{(b-a).days:>4d} paeva   T1 |z|>=1: {n1}")
print()
print(f"  PRIMARY: |z| >= 1, TIER 1, sisenemine D0 = esimene baar, mille")
print(f"           SULGEMINE on RANGELT parast valjalaset; hoid 30 min")
print(f"  instrumendikaart (fikseeritud enne tulemusi):")
print(f"    " + ", ".join(f"{c}->{p}" for c, (p, _) in I.KAART.items()))

# ================================================ 1. EVENT-TIME PROFIIL ===
print()
print("=" * 112)
print("IMM.1  KUS LIIKUMINE TOIMUB — |tootlus| valjalaskest, MARGITA (kirjeldav)")
print("=" * 112)
print("  Ankur = viimane sulgemine ENNE valjalaset (teate-eelne hind).")
print("  See EI OLE kaubeldav tulemus; see naitab, KUS liikumine asub.")
print()
MIN_A = [5, 15, 30, 60]
x5 = d_all[d_all["z"].abs() >= 1]
L = I.liikumine(x5, H["A_M5"], 5, MIN_A)
print(f"  RADA A (M5), n = {len(L)} sundmust")
print(f"{'aken':<14s}{'mediaan':>10s}{'keskm':>9s}{'p75':>8s}{'p90':>8s}"
      f"{'p95':>8s}{'osa 60min-st':>15s}")
read = []
a60 = L[60].abs()
for m in MIN_A:
    v = L[m].abs().dropna()
    osa = float((L[m].abs() / a60.replace(0, np.nan)).median())
    print(f"  0 -> +{m:<7d}{1e4*v.median():>10.1f}{1e4*v.mean():>9.1f}"
          f"{1e4*v.quantile(.75):>8.1f}{1e4*v.quantile(.90):>8.1f}"
          f"{1e4*v.quantile(.95):>8.1f}{100*osa:>14.0f}%")
    read.append(dict(rada="A_M5", aken_min=m, n=len(v),
                     mediaan_bp=1e4*float(v.median()),
                     keskm_bp=1e4*float(v.mean()),
                     p75_bp=1e4*float(v.quantile(.75)),
                     p90_bp=1e4*float(v.quantile(.90)),
                     p95_bp=1e4*float(v.quantile(.95)),
                     osa_60min=osa))
print("  +1 min        DATA INSUFFICIENT (M1-andmeid ei ole)")
L15 = I.liikumine(x5, H["B_M15"], 15, [15, 30, 60])
a60b = L15[60].abs()
print(f"\n  RADA B (M15), n = {len(L15)} sundmust")
for m in (15, 30, 60):
    v = L15[m].abs().dropna()
    osa = float((L15[m].abs() / a60b.replace(0, np.nan)).median())
    print(f"  0 -> +{m:<7d}{1e4*v.median():>10.1f}{1e4*v.mean():>9.1f}"
          f"{1e4*v.quantile(.75):>8.1f}{1e4*v.quantile(.90):>8.1f}"
          f"{1e4*v.quantile(.95):>8.1f}{100*osa:>14.0f}%")
    read.append(dict(rada="B_M15", aken_min=m, n=len(v),
                     mediaan_bp=1e4*float(v.median()),
                     keskm_bp=1e4*float(v.mean()),
                     p75_bp=1e4*float(v.quantile(.75)),
                     p90_bp=1e4*float(v.quantile(.90)),
                     p95_bp=1e4*float(v.quantile(.95)),
                     osa_60min=osa))
salvesta("IMM_EVENT_TIME.csv", read)

# ============================= 2. MARGIGA TOOTLUS JA INKREMENDID ==========
print()
print("=" * 112)
print("IMM.2  MARGIGA (SIGNAALI SUUNAS) TOOTLUS JA INKREMENDID")
print("=" * 112)
print("  0 -> +5 min SISALDAB hupet ja EI OLE kaubeldav (sisenemine ei jouaks).")
print("  Kaubeldavad on inkrementaalsed loigud alates +5 min.")
print()
Ls = I.liikumine(x5, H["A_M5"], 5, MIN_A)
sg = []
for (paar, ts, _k) in Ls.index:
    r = x5[(x5["paar"] == paar) & (x5["ts"] == ts)]
    sg.append(int(r["suund"].iloc[0]) if len(r) else 0)
sg = np.array(sg, float)
print(f"{'loik':<24s}{'n':>6s}{'keskm_bp':>11s}{'med_bp':>9s}{'wr%':>7s}"
      f"{'t':>7s}{'p':>8s}")
read = []
loigud = [(0, 5, "0 -> 5 min  HUPE"), (5, 15, "5 -> 15 min"),
          (15, 30, "15 -> 30 min"), (30, 60, "30 -> 60 min")]
for a, b, silt in loigud:
    v = (Ls[b] - (Ls[a] if a else 0.0)).values * sg
    v = v[np.isfinite(v)]
    if len(v) < 5:
        print(f"  {silt:<22s}   (alla 5)")
        continue
    sd = v.std(ddof=1)
    t = float(v.mean()/sd*math.sqrt(len(v))) if sd > 0 else 0.0
    kaub = "" if a else "   <- EI OLE KAUBELDAV"
    print(f"  {silt:<22s}{len(v):>6d}{1e4*v.mean():>+11.2f}"
          f"{1e4*np.median(v):>+9.2f}{100*(v>0).mean():>7.1f}"
          f"{t:>7.2f}{C.p_kahepoolne(t):>8.3f}{kaub}")
    read.append(dict(loik=silt, algus_min=a, lopp_min=b, n=len(v),
                     keskm_bp=1e4*float(v.mean()),
                     med_bp=1e4*float(np.median(v)),
                     wr=100*float((v > 0).mean()), t=t, p=C.p_kahepoolne(t),
                     kaubeldav=bool(a)))
salvesta("IMM_INCREMENTAL.csv", read)

# ================================================ 3. PRIMARY ==============
print()
print("=" * 112)
print("IMM.3  PRIMARY — D0 sisenemine, 30 min hoid, TIER 1, |z| >= 1")
print("=" * 112)
print(I.PAIS)
read = []
T = {}
for kood, r in I.RAJAD.items():
    if BAAR[kood] > I.PRIMARY_HOID:
        print(f"{r['nimi']+'  30 min hoid':<30s}   DATA INSUFFICIENT "
              f"(baar {BAAR[kood]} min > hoid 30 min)")
        read.append(dict(rada=kood, test="PRIMARY_D0_30min",
                         staatus="DATA INSUFFICIENT"))
        continue
    T[kood] = I.tehingud(x5, H[kood], BAAR[kood], 0, I.PRIMARY_HOID)
    m = I.moot(T[kood], 0.0)
    print(I.rida(f"{r['nimi']}  PRIMARY", m))
    read.append(rm(m, dict(rada=kood, test="PRIMARY_D0_30min",
                           viivitus_med_min=float(T[kood]["viivitus_tegelik_min"].median()),
                           hoid_med_min=float(T[kood]["hoid_tegelik_min"].median()))))
# RADA C: pikim valim, aga minimaalne samm on tund
T["C_H1"] = I.tehingud(x5, H["C_H1"], 60, 0, 60)
mC = I.moot(T["C_H1"], 0.0)
print(I.rida("RADA C  H1  D0 + 60 min", mC))
read.append(rm(mC, dict(rada="C_H1", test="D0_60min",
                        viivitus_med_min=float(T["C_H1"]["viivitus_tegelik_min"].median()),
                        hoid_med_min=float(T["C_H1"]["hoid_tegelik_min"].median()))))
print()
for kood in ("A_M5", "B_M15", "C_H1"):
    if kood in T and len(T[kood]):
        print(f"  {I.RAJAD[kood]['nimi']}: sisenemisviivitus mediaan "
              f"{T[kood]['viivitus_tegelik_min'].median():.0f} min "
              f"(min {T[kood]['viivitus_tegelik_min'].min():.0f}, "
              f"max {T[kood]['viivitus_tegelik_min'].max():.0f}), "
              f"hoid {T[kood]['hoid_tegelik_min'].median():.0f} min")

# --- lavede tundlikkus
print()
print("  ULLATUSE LAVE (eelmaaratud, EI OPTIMEERITA):")
print(I.PAIS)
for lavi in I.LAVID:
    xx = d_all[d_all["z"].abs() >= lavi]
    for kood in ("A_M5", "B_M15"):
        Tx = I.tehingud(xx, H[kood], BAAR[kood], 0, I.PRIMARY_HOID)
        m = I.moot(Tx, 0.0)
        print(I.rida(f"{I.RAJAD[kood]['nimi']}  |z|>={lavi}", m))
        read.append(rm(m, dict(rada=kood, test=f"lavi_{lavi}")))
salvesta("IMM_PRIMARY.csv", read)

# ================================================ 4. VIIVITUS =============
print()
print("=" * 112)
print("IMM.4  SISENEMISVIIVITUSE TUNDLIKKUS (eelregistreeritud, EI OPTIMEERITA)")
print("=" * 112)
print(I.PAIS)
read = []
for v in I.VIIVITUSED:
    if v == 1:
        print(f"{'D1  +1 min':<30s}   DATA INSUFFICIENT (M1-andmeid ei ole)")
        read.append(dict(viivitus_min=1, staatus="DATA INSUFFICIENT"))
        continue
    for kood in ("A_M5", "B_M15"):
        if v % BAAR[kood] and v != 0:
            continue
        Tx = I.tehingud(x5, H[kood], BAAR[kood], v, I.PRIMARY_HOID)
        m = I.moot(Tx, 0.0)
        print(I.rida(f"{I.RAJAD[kood]['nimi']}  D{v}", m))
        read.append(rm(m, dict(rada=kood, viivitus_min=v)))
salvesta("IMM_DELAY.csv", read)

# ================================================ 5. HOID =================
print()
print("=" * 112)
print("IMM.5  HOIDMISAJA TUNDLIKKUS (eelregistreeritud, EI OPTIMEERITA)")
print("=" * 112)
print(I.PAIS)
read = []
for h in I.HOIUD:
    for kood in ("A_M5", "B_M15"):
        if h < BAAR[kood]:
            print(f"{I.RAJAD[kood]['nimi']+f'  hoid {h} min':<30s}"
                  f"   DATA INSUFFICIENT (baar {BAAR[kood]} min)")
            read.append(dict(rada=kood, hoid_min=h,
                             staatus="DATA INSUFFICIENT"))
            continue
        Tx = I.tehingud(x5, H[kood], BAAR[kood], 0, h)
        m = I.moot(Tx, 0.0)
        tahis = "  <- PRIMARY" if h == I.PRIMARY_HOID else ""
        print(I.rida(f"{I.RAJAD[kood]['nimi']}  hoid {h} min", m) + tahis)
        read.append(rm(m, dict(rada=kood, hoid_min=h)))
salvesta("IMM_HOLD.csv", read)

# ================================================ 6. KULU / LIBISEMINE ====
print()
print("=" * 112)
print("IMM.6  TAITMISKULU JA SUNDMUSE LIBISEMINE  +  MURDEPUNKT")
print("=" * 112)
print("  Libisemine rakendub UKS KORD sisenemisel (uudise sisse libiseb;")
print("  valjumine 30 min hiljem on tavaline turg).")
print()
print(f"{'rada / libisemine':<30s}{'n':>6s}{'bruto_bp':>10s}{'kulu_bp':>9s}"
      f"{'lib_bp':>8s}{'kokku':>8s}{'neto_bp':>9s}")
read = []
for kood in ("A_M5", "B_M15", "C_H1"):
    Tk = T[kood]
    for lib in I.LIBISEMISED:
        m = I.moot(Tk, lib)
        kok = m["kulu_bp"] + lib
        print(f"{I.RAJAD[kood]['nimi']+f'  +{lib:.0f} bp':<30s}{m['n']:>6d}"
              f"{m['bruto_bp']:>+10.2f}{m['kulu_bp']:>9.2f}{lib:>8.1f}"
              f"{kok:>8.2f}{m['neto_bp']:>+9.2f}")
        read.append(rm(m, dict(rada=kood, libisemine_bp=lib,
                               kulu_kokku_bp=kok)))
    m0 = I.moot(Tk, 0.0)
    print(f"{'  MURDEPUNKT (ootus = 0)':<30s}{'':>6s}"
          f"{m0['bruto_bp']:>+10.2f}{'':>9s}{'':>8s}"
          f"{m0['bruto_bp']:>8.2f}{'  <- max talutav kulu':>9s}")
    print(f"{'  tegelik eeldatud kulu':<30s}{'':>6s}{'':>10s}"
          f"{m0['kulu_bp']:>9.2f}{'':>8s}{m0['kulu_bp']:>8.2f}"
          f"{m0['bruto_bp']-m0['kulu_bp']:>+9.2f}  varu")
    print()
salvesta("IMM_COST.csv", read)

# ================================================ 7. JUHUSLIK BAAS =======
print()
print("=" * 112)
print(f"IMM.7  PAARITATUD JUHUSLIKU SUUNA BAAS ({I.N_BOOT} katset)")
print("=" * 112)
print("  Samad sundmused, sama sisenemine ja valjumine, AINULT suund juhuslik.")
print("  Jarjekorra permutatsiooni EI KASUTATA.")
print()
print(f"{'rada':<16s}{'n':>6s}{'signaal_bp':>12s}{'juhuslik med':>14s}"
      f"{'juhuslik 95%':>14s}{'vahe_bp':>10s}{'p':>8s}{'boot 95% CI':>22s}")
read = []
for kood in ("A_M5", "B_M15", "C_H1"):
    Tk = T[kood]
    jaot, pv = I.juhuslik_baas(Tk)
    m = I.moot(Tk, 0.0)
    lo, hi = I.bootstrap_ci(Tk["bruto"].values)
    wr_j = 100.0 * float(np.mean([(np.random.RandomState(I.SEEME + i).choice(
        [-1.0, 1.0], size=len(Tk)) * (Tk["bruto"] / Tk["suund"]).values > 0).mean()
        for i in range(50)]))
    print(f"{I.RAJAD[kood]['nimi']:<16s}{m['n']:>6d}{m['bruto_bp']:>+12.2f}"
          f"{1e4*np.median(jaot):>+14.2f}{1e4*np.quantile(jaot,.95):>+14.2f}"
          f"{m['bruto_bp']-1e4*np.median(jaot):>+10.2f}{pv:>8.3f}"
          f"{f'[{lo:+.2f}, {hi:+.2f}]':>22s}")
    read.append(dict(rada=kood, n=m["n"], signaal_bp=m["bruto_bp"],
                     juhuslik_med_bp=1e4*float(np.median(jaot)),
                     juhuslik_p95_bp=1e4*float(np.quantile(jaot, .95)),
                     vahe_bp=m["bruto_bp"]-1e4*float(np.median(jaot)),
                     p=pv, boot_lo_bp=lo, boot_hi_bp=hi,
                     signaal_wr=m["wr"], juhuslik_wr=wr_j))
salvesta("IMM_RANDOM.csv", read)

# ================================================ 8. OOS =================
print()
print("=" * 112)
print("IMM.8  KRONOLOOGILINE JAOTUS")
print("=" * 112)
print("  RADA A (41 paeva) ja RADA B (80 paeva) on liiga luhikesed")
print("  kolmeosaliseks jaotuseks — seda EI SURUTA.")
print("  RADA C (2.79 a) kannab jaotust: kalendriaasta-pohine, sama mis B2.")
print()
print(I.PAIS)
read = []
TC = T["C_H1"]
for nimi, m_ in (("TRAIN  .. 2024", TC["ts"] <= pd.Timestamp("2024-12-31")),
                 ("VALID  2025", (TC["ts"] > pd.Timestamp("2024-12-31"))
                  & (TC["ts"] <= pd.Timestamp("2025-12-31"))),
                 ("FINAL OOS 2026", TC["ts"] > pd.Timestamp("2025-12-31"))):
    m = I.moot(TC[m_], 0.0)
    print(I.rida(f"RADA C  {nimi}", m))
    read.append(rm(m, dict(rada="C_H1", osa=nimi)))
for kood in ("A_M5", "B_M15"):
    print(f"{I.RAJAD[kood]['nimi']+'  jaotus':<30s}   "
          f"VALIM LIIGA LUHIKE (n={len(T[kood])})")
    read.append(dict(rada=kood, osa="—", staatus="VALIM LIIGA LUHIKE"))
salvesta("IMM_OOS.csv", read)

# ================================================ 9. VALUUTA ============
print()
print("=" * 112)
print("IMM.9  VALUUTA KAUPA (RADA C, ainus statistiliselt kandev valim)")
print("=" * 112)
print(I.PAIS)
read = []
for c in C.VALUUTAD:
    m = I.moot(TC[TC["cur"] == c], 0.0)
    print(I.rida(f"{c}  ({I.KAART[c][0]})", m))
    read.append(rm(m, dict(valuuta=c, paar=I.KAART[c][0])))
salvesta("IMM_CURRENCY.csv", read)

# ================================================ 10. INDIKAATOR =========
print()
print("=" * 112)
print("IMM.10  INDIKAATOR JA EELMAARATUD GRUPID (RADA C)")
print("=" * 112)
print(I.PAIS)
read = []
for ind in sorted(C.TIER1):
    m = I.moot(TC[TC["indicator"] == ind], 0.0)
    print(I.rida(f"{ind} ({C.TIER1[ind]:+d})", m))
    read.append(rm(m, dict(indikaator=ind, mark=C.TIER1[ind])))
GRUPID = {
    "CPI / inflatsioon": ["Inflation Rate", "Core Inflation Rate",
                          "Inflation Rate Mom"],
    "toohoive / NFP": ["Non Farm Payrolls", "Employment Change"],
    "tootus": ["Unemployment Rate"],
    "SKP": ["GDP Growth Rate", "GDP Annual Growth Rate"],
    "intressiotsus": ["Interest Rate"],
    "jaemuuk": ["Retail Sales MoM", "Retail Sales YoY"],
}
print()
for g, liikmed in GRUPID.items():
    m = I.moot(TC[TC["indicator"].isin(liikmed)], 0.0)
    print(I.rida(f"GRUPP {g}", m))
    read.append(rm(m, dict(grupp=g)))
print(I.rida("GRUPP PMI", None))
print("      (PMI ei kuulu B1 TIER 1 hulka; uut kategooriat EI LOODA)")
T2C = I.tehingud(d_t2[d_t2["z"].abs() >= 1], H["C_H1"], 60, 0, 60)
print()
print(I.rida("TIER 2 (vordluseks)", I.moot(T2C, 0.0)))
read.append(rm(I.moot(T2C, 0.0), dict(grupp="TIER2")))
salvesta("IMM_INDICATOR.csv", read)

# ================================================ 11. MAGNITUUD =========
print()
print("=" * 112)
print("IMM.11  ULLATUSE SUURUSE EELMAARATUD VAHEMIKUD (RADA C)")
print("=" * 112)
print(I.PAIS)
read = []
az = TC["z"].abs()
for lo, hi, silt in ((1.0, 1.5, "1.0 <= |z| < 1.5"),
                     (1.5, 2.0, "1.5 <= |z| < 2.0"),
                     (2.0, np.inf, "|z| >= 2.0")):
    m = I.moot(TC[(az >= lo) & (az < hi)], 0.0)
    print(I.rida(silt, m))
    read.append(rm(m, dict(vahemik=silt)))
salvesta("IMM_MAGNITUDE.csv", read)

# ================================================ 12. SESSIOON ==========
print()
print("=" * 112)
print("IMM.12  SESSIOON (kirjeldav, UTC; EI OPTIMEERITA aknaid)")
print("=" * 112)
print(I.PAIS)
tund = pd.DatetimeIndex(TC["ts"]).hour
for lo, hi, silt in ((0, 7, "Aasia 00-07"), (7, 12, "London 07-12"),
                     (12, 16, "London+NY kattuvus 12-16"),
                     (16, 21, "NY 16-21"), (21, 24, "Aasia avanemine 21-24")):
    print(I.rida(silt, I.moot(TC[(tund >= lo) & (tund < hi)], 0.0)))

# ================================================ 13. TEOSTATAVUS =======
print()
print("=" * 112)
print("IMM.13  TEOSTATAVUS 205 EUR KONTOL")
print("=" * 112)
KAPITAL, UHIKUD = 205.0, 1000.0
E5 = H["A_M5"]["EURUSD"]
eurusd = float(E5["close"].iloc[-1])
aastaid_C = (TC["ts"].max() - TC["ts"].min()).days / 365.25
print(f"  tehinguid RADA C: {len(TC)} / {aastaid_C:.2f} a = "
      f"{len(TC)/aastaid_C:.0f} aastas")
print(f"  hoidmisaeg: 30-60 min")
print()
print(f"{'paar':<10s}{'30min sigma%':>14s}{'0.01 lot EUR':>15s}"
      f"{'1-sigma EUR':>14s}{'% kontost':>12s}")
read = []
pnl_read = []
for paar in sorted(set(p for p, _ in I.KAART.values())):
    Tp = T["A_M5"][T["A_M5"]["paar"] == paar]
    if len(Tp) < 3:
        Tp = T["B_M15"][T["B_M15"]["paar"] == paar]
    if len(Tp) < 3:
        continue
    sig = float(Tp["bruto"].std(ddof=1))
    baas = paar[:3]
    nots = (UHIKUD if baas == "EUR" else UHIKUD / eurusd)
    pnl = nots * sig
    pnl_read.append(pnl)
    print(f"{paar:<10s}{100*sig:>14.3f}{nots:>15.0f}{pnl:>14.2f}"
          f"{100*pnl/KAPITAL:>12.2f}")
    read.append(dict(paar=paar, n=len(Tp), sigma_30min_pct=100*sig,
                     lot001_eur=nots, sigma_eur=pnl,
                     pct_kontost=100*pnl/KAPITAL))
for risk in (0.0025, 0.0050):
    eur = KAPITAL * risk
    ok = sum(1 for q in pnl_read if q <= eur)
    print(f"  kavatsetud risk {100*risk:.2f}% = {eur:.2f} EUR -> "
          f"taidetav {ok}/{len(pnl_read)} paaril; vajalik konto "
          f"{min(pnl_read)/risk:.0f}-{max(pnl_read)/risk:.0f} EUR")
    read.append(dict(paar="KOKKU", risk=risk, eur=eur,
                     taidetav=ok, n_paari=len(pnl_read),
                     vajalik_konto_min=min(pnl_read)/risk,
                     vajalik_konto_max=max(pnl_read)/risk))
salvesta("IMM_EXECUTION.csv", read)

print()
print("=" * 112)
print("VALJUNDFAILID")
print("=" * 112)
for nimi, n in VALJUND.items():
    print(f"  {nimi:<28s} {n} rida")
