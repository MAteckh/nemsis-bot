"""
cal_sub60_run.py — SUB-60-SECOND tulemused.
Jookseb PARAST cal_sub60_audit.py-d (21 kontrolli, 0 FAIL).
"""
import math
import os

import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I
import cal_sub60 as S

JUUR = S.JUUR
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


d_t1 = S.valim("T1")
d_t2 = S.valim("T2")
H = {kk: S.hinnad(v["sufiks"]) for kk, v in S.RAJAD.items()}
BAAR = {kk: v["baar_s"] for kk, v in S.RAJAD.items()}
x = d_t1[d_t1["z"].abs() >= 1.0]
x12 = pd.concat([d_t1, d_t2]).sort_values("ts")
x12 = x12[x12["z"].abs() >= 1.0]

print("=" * 112)
print("S60.0  ANDMEALLIKATE AUDIT JA VALIM")
print("=" * 112)
print("  KONTROLLITUD ALLIKAD (liivakastil otseuhendust EI OLE, curl = 000;")
print("  ainus valjapaas on Supabase http-laiendus):")
print()
print(f"  {'allikas':<26s}{'bid/ask':>9s}{'resolutsioon':>15s}"
      f"{'periood':>13s}{'saadav':>9s}")
for a, b, c_, dd, e in (
        ("Dukascopy .bi5 tick", "JAH", "tick", "2003-", "EI"),
        ("HistData M1/tick", "JAH", "M1/tick", "2000-", "EI"),
        ("TrueFX tick", "JAH", "tick", "2009-", "EI"),
        ("Yahoo Finance 1m", "EI", "M1 mid OHLC", "~28 paeva", "JAH"),
        ("Yahoo Finance 5m", "EI", "M5 mid OHLC", "~60 paeva", "JAH")):
    print(f"  {a:<26s}{b:>9s}{c_:>15s}{dd:>13s}{e:>9s}")
print()
print("  MIKS TICK EI OLE SAADAV: Dukascopy .bi5 on LZMA-pakitud BINAAR ja")
print("  HistData tagastab ZIP-i; pgsql-http annab `content` TEKSTINA, seega")
print("  binaar rikutakse. TrueFX ajalooarhiiv nouab sisselogimist —")
print("  kasutaja API-votit EI KUSITUD. Andmeid EI FABRITSEERITUD.")
print()
print("  YAHOO M1 PIIR ON MOOEDETUD, MITTE EELDATUD: 7-paevased period1/")
print("  period2 aknad 0-7, 7-14, 14-21 paeva tagasi annavad ~7100 baari;")
print("  28 ja 35 paeva tagasi annavad 0 rida.")
print()
for kk, v in S.RAJAD.items():
    Hx = H[kk]
    a = min(dd.index.min() for dd in Hx.values())
    b = max(dd.index.max() for dd in Hx.values())
    n1 = int(((x["ts"] >= a) & (x["ts"] <= b)).sum())
    n12 = int(((x12["ts"] >= a) & (x12["ts"] <= b)).sum())
    print(f"  {v['nimi']}  {a.date()} .. {b.date()}  {(b-a).days:>3d} paeva  "
          f"T1 |z|>=1: {n1:>3d}   T1+T2 |z|>=1: {n12:>3d}")
print()
print("  PRIMARY: RADA M1, D0 sisenemine (esimene sulgemine RANGELT parast")
print("           valjalaset), hoid 60 s, TIER 1, |z| >= 1")

# =========================================== 1. MIS ON MOOTMATU ==========
print()
print("=" * 112)
print("S60.1  MIDA SAAB JA MIDA EI SAA MOOTA")
print("=" * 112)
print(f"{'horisont':<14s}{'M1':>10s}{'M5':>10s}{'M15':>10s}   markus")
read = []
for s_ in S.VIIVITUSED_S:
    v = []
    for kk in ("M1", "M5", "M15"):
        v.append("JAH" if (s_ == 0 or s_ % BAAR[kk] == 0) else "EI")
    mk = "" if v[0] == "JAH" else "  <- DATA INSUFFICIENT, EI INTERPOLEERITA"
    print(f"  viivitus {s_:>3d}s{v[0]:>10s}{v[1]:>10s}{v[2]:>10s}{mk}")
    read.append(dict(tuup="viivitus", sekundeid=s_, M1=v[0], M5=v[1], M15=v[2]))
print()
for s_ in S.HOIUD_S:
    v = ["JAH" if s_ % BAAR[kk] == 0 else "EI" for kk in ("M1", "M5", "M15")]
    mk = "" if v[0] == "JAH" else "  <- DATA INSUFFICIENT, EI INTERPOLEERITA"
    print(f"  hoid     {s_:>3d}s{v[0]:>10s}{v[1]:>10s}{v[2]:>10s}{mk}")
    read.append(dict(tuup="hoid", sekundeid=s_, M1=v[0], M5=v[1], M15=v[2]))
print()
print("  KOKKUVOTE: 1 / 3 / 5 / 10 / 15 / 30 SEKUNDI horisonte EI SAA MOOTA")
print("  UHELGI rajal. Vaikseim baar on 60 s. Need jaavad TOESTAMATA.")
salvesta("SUB60_DATA_QUALITY.csv", read + [
    dict(tuup="katvus", rada=kk,
         algus=str(min(dd.index.min() for dd in H[kk].values())),
         lopp=str(max(dd.index.max() for dd in H[kk].values())),
         n_t1=int(((x["ts"] >= min(dd.index.min() for dd in H[kk].values()))
                   & (x["ts"] <= max(dd.index.max() for dd in H[kk].values()))).sum()),
         n_t1t2=int(((x12["ts"] >= min(dd.index.min() for dd in H[kk].values()))
                     & (x12["ts"] <= max(dd.index.max() for dd in H[kk].values()))).sum()))
    for kk in S.RAJAD])

# =========================================== 2. PRIMARY ==================
print()
print("=" * 112)
print("S60.2  PRIMARY — RADA M1, D0 sisenemine, hoid 60 s")
print("=" * 112)
print(S.PAIS)
read = []
T = {}
for kk in ("M1", "M5", "M15"):
    T[kk] = S.tehingud(x, H[kk], BAAR[kk], 0, 60 if kk == "M1" else BAAR[kk])
    m = S.moot(T[kk], 0.0)
    silt = (f"{S.RAJAD[kk]['nimi']}  D0 + 60s" if kk == "M1"
            else f"{S.RAJAD[kk]['nimi']}  D0 + {BAAR[kk]}s")
    print(S.rida(silt + ("   <- PRIMARY" if kk == "M1" else ""), m))
    read.append(rm(m, dict(rada=kk, test="PRIMARY" if kk == "M1" else "kontroll",
                           viivitus_med_s=(float(T[kk]["viivitus_s"].median())
                                           if len(T[kk]) else np.nan),
                           hoid_med_s=(float(T[kk]["hoid_s"].median())
                                       if len(T[kk]) else np.nan))))
print()
for kk in ("M1", "M5", "M15"):
    if len(T[kk]):
        print(f"  {S.RAJAD[kk]['nimi']}: viivitus mediaan "
              f"{T[kk]['viivitus_s'].median():.0f}s "
              f"(min {T[kk]['viivitus_s'].min():.0f}, "
              f"max {T[kk]['viivitus_s'].max():.0f}), "
              f"hoid {T[kk]['hoid_s'].median():.0f}s, n={len(T[kk])}")
print()
print("  SAMA, TIER 1 + TIER 2 koos (rohkem sundmusi; eelmaaratud laiendus):")
T12 = {kk: S.tehingud(x12, H[kk], BAAR[kk], 0, 60 if kk == "M1" else BAAR[kk])
       for kk in ("M1", "M5", "M15")}
for kk in ("M1", "M5", "M15"):
    m = S.moot(T12[kk], 0.0)
    print(S.rida(f"{S.RAJAD[kk]['nimi']}  T1+T2", m))
    read.append(rm(m, dict(rada=kk, test="T1+T2")))
print()
print("  ULLATUSE LAVE (eelmaaratud, EI OPTIMEERITA):")
for lavi in S.LAVID:
    for kk in ("M1", "M5"):
        xx = d_t1[d_t1["z"].abs() >= lavi]
        m = S.moot(S.tehingud(xx, H[kk], BAAR[kk], 0,
                              60 if kk == "M1" else BAAR[kk]), 0.0)
        print(S.rida(f"{S.RAJAD[kk]['nimi']}  |z|>={lavi}", m))
        read.append(rm(m, dict(rada=kk, test=f"lavi_{lavi}")))
salvesta("SUB60_PRIMARY.csv", read)

# =========================================== 3. VIIVITUS / HOID ==========
print()
print("=" * 112)
print("S60.3  SISENEMISVIIVITUSE VORK (eelregistreeritud)")
print("=" * 112)
print(S.PAIS)
read = []
for s_ in S.VIIVITUSED_S:
    if s_ not in (0, 60):
        print(f"{f'viivitus +{s_}s':<30s}   DATA INSUFFICIENT "
              f"(vaikseim baar 60 s; EI INTERPOLEERITA)")
        read.append(dict(viivitus_s=s_, staatus="DATA INSUFFICIENT"))
        continue
    m = S.moot(S.tehingud(x, H["M1"], 60, s_, 60), 0.0)
    print(S.rida(f"RADA M1  viivitus +{s_}s", m)
          + ("   <- PRIMARY" if s_ == 0 else ""))
    read.append(rm(m, dict(rada="M1", viivitus_s=s_)))
salvesta("SUB60_DELAY.csv", read)

print()
print("=" * 112)
print("S60.4  HOIDMISAJA VORK (eelregistreeritud)")
print("=" * 112)
print(S.PAIS)
read = []
for s_ in S.HOIUD_S:
    if s_ % 60:
        print(f"{f'hoid {s_}s':<30s}   DATA INSUFFICIENT "
              f"(vaikseim baar 60 s; EI INTERPOLEERITA)")
        read.append(dict(hoid_s=s_, staatus="DATA INSUFFICIENT"))
        continue
    m = S.moot(S.tehingud(x, H["M1"], 60, 0, s_), 0.0)
    print(S.rida(f"RADA M1  hoid {s_}s", m)
          + ("   <- PRIMARY" if s_ == 60 else ""))
    read.append(rm(m, dict(rada="M1", hoid_s=s_)))
for s_ in (300, 600):
    m = S.moot(S.tehingud(x, H["M1"], 60, 0, s_), 0.0)
    print(S.rida(f"RADA M1  hoid {s_}s (lisa)", m))
    read.append(rm(m, dict(rada="M1", hoid_s=s_)))
salvesta("SUB60_HOLD.csv", read)

# =========================================== 5. SIGNED PROFIIL ===========
print()
print("=" * 112)
print("S60.5  MARGIGA EVENT-TIME PROFIIL (ankur = valjalaske-EELNE hind)")
print("=" * 112)
print("  Loik 0 -> 60s SISALDAB hupet ja EI OLE kaubeldav.")
print()
SEK = [60, 120, 300, 600, 1800, 3600]
L = S.signed_profiil(x, H["M1"], 60, SEK)
print(f"{'kumulatiiv':<20s}{'n':>6s}{'keskm_bp':>11s}{'med_bp':>9s}"
      f"{'wr%':>7s}{'t':>7s}{'p':>8s}")
read = []
for s_ in SEK:
    v = L[s_].dropna().values
    if len(v) < 5:
        continue
    sd = v.std(ddof=1)
    t = float(v.mean()/sd*math.sqrt(len(v))) if sd > 0 else 0.0
    mk = "   <- SISALDAB HUPET" if s_ == 60 else ""
    print(f"  0 -> +{s_:<13d}{len(v):>6d}{1e4*v.mean():>+11.2f}"
          f"{1e4*np.median(v):>+9.2f}{100*(v>0).mean():>7.1f}{t:>7.2f}"
          f"{C.p_kahepoolne(t):>8.3f}{mk}")
    read.append(dict(tuup="kumulatiiv", sek=s_, n=len(v),
                     keskm_bp=1e4*float(v.mean()),
                     med_bp=1e4*float(np.median(v)),
                     wr=100*float((v > 0).mean()), t=t, p=C.p_kahepoolne(t)))
print()
print(f"{'inkrement':<20s}{'n':>6s}{'keskm_bp':>11s}{'med_bp':>9s}"
      f"{'wr%':>7s}{'t':>7s}{'p':>8s}")
for a, b in zip([0] + SEK[:-1], SEK):
    v = (L[b] - (L[a] if a else 0.0)).dropna().values
    if len(v) < 5:
        continue
    sd = v.std(ddof=1)
    t = float(v.mean()/sd*math.sqrt(len(v))) if sd > 0 else 0.0
    mk = "   <- EI OLE KAUBELDAV" if a == 0 else ""
    print(f"  {a}s -> {b}s{'':<{max(0,10-len(str(a))-len(str(b)))}}"
          f"{len(v):>6d}{1e4*v.mean():>+11.2f}{1e4*np.median(v):>+9.2f}"
          f"{100*(v>0).mean():>7.1f}{t:>7.2f}{C.p_kahepoolne(t):>8.3f}{mk}")
    read.append(dict(tuup="inkrement", algus_s=a, lopp_s=b, n=len(v),
                     keskm_bp=1e4*float(v.mean()),
                     med_bp=1e4*float(np.median(v)),
                     wr=100*float((v > 0).mean()), t=t, p=C.p_kahepoolne(t),
                     kaubeldav=bool(a)))
print()
print("  ALLA 60 SEKUNDI: MOOTMATU. Loigu 0 -> 60s sisemust ei saa avada.")
salvesta("SUB60_INCREMENTAL.csv", read)

# =========================================== 6. JUHUSLIK BAAS ============
print()
print("=" * 112)
print(f"S60.6  PAARITATUD JUHUSLIKU SUUNA BAAS ({S.N_BOOT} katset)")
print("=" * 112)
print(f"{'rada':<20s}{'n':>6s}{'signaal':>10s}{'juh.med':>10s}"
      f"{'juh.95%':>10s}{'pertsentiil':>13s}{'p':>8s}{'boot 95% CI':>22s}")
read = []
for kk in ("M1", "M5", "M15"):
    Tk = T[kk]
    if len(Tk) < 5:
        continue
    jaot, pv = S.juhuslik_baas(Tk)
    m = S.moot(Tk, 0.0)
    lo, hi = S.bootstrap_ci(Tk["bruto"].values)
    pert = 100.0 * float((jaot < m["bruto_bp"] / 1e4).mean())
    print(f"{S.RAJAD[kk]['nimi']:<20s}{m['n']:>6d}{m['bruto_bp']:>+10.2f}"
          f"{1e4*np.median(jaot):>+10.2f}{1e4*np.quantile(jaot,.95):>+10.2f}"
          f"{pert:>12.1f}%{pv:>8.3f}{f'[{lo:+.2f}, {hi:+.2f}]':>22s}")
    read.append(dict(rada=kk, n=m["n"], signaal_bp=m["bruto_bp"],
                     juhuslik_med_bp=1e4*float(np.median(jaot)),
                     juhuslik_p95_bp=1e4*float(np.quantile(jaot, .95)),
                     pertsentiil=pert, p=pv, boot_lo_bp=lo, boot_hi_bp=hi))
salvesta("SUB60_RANDOM.csv", read)

# =========================================== 7. KULU / LIBISEMINE ========
print()
print("=" * 112)
print("S60.7  KULU JA LIBISEMINE (SIMULEERITUD — bid/ask puudub)")
print("=" * 112)
print(f"{'rada / libisemine':<26s}{'n':>6s}{'bruto':>9s}{'kulu':>8s}"
      f"{'lib':>7s}{'kokku':>8s}{'neto':>9s}")
read = []
for kk in ("M1", "M5", "M15"):
    Tk = T[kk]
    if len(Tk) < 5:
        continue
    for lib in S.LIBISEMISED:
        m = S.moot(Tk, lib)
        print(f"{S.RAJAD[kk]['nimi']+f' +{lib:.0f}bp':<26s}{m['n']:>6d}"
              f"{m['bruto_bp']:>+9.2f}{m['kulu_bp']:>8.2f}{lib:>7.1f}"
              f"{m['kulu_bp']+lib:>8.2f}{m['neto_bp']:>+9.2f}")
        read.append(rm(m, dict(rada=kk, libisemine_bp=lib,
                               kulu_kokku_bp=m["kulu_bp"] + lib)))
    m0 = S.moot(Tk, 0.0)
    print(f"{'  MURDEPUNKT':<26s}{'':>6s}{m0['bruto_bp']:>+9.2f}"
          f"{'':>8s}{'':>7s}{max(m0['bruto_bp'],0):>8.2f}   max talutav kulu")
    print()
salvesta("SUB60_COST.csv", read)

# =========================================== 8. OOS ======================
print()
print("=" * 112)
print("S60.8  OUT-OF-SAMPLE")
print("=" * 112)
print("  RADA M1 katab 28 paeva (2026-08-19 .. 2026-09-16).")
print("  TRAIN through 2024 / VALID 2025 / FINAL OOS 2026 jaotus EI OLE")
print("  voimalik — kogu valim on uhe kuu sees.")
print("  AUS SONA: sample too short for meaningful OOS.")
print("  See EI OLE FAIL. See on DATA INSUFFICIENT.")
salvesta("SUB60_OOS.csv", [dict(rada=kk, staatus="sample too short",
                                paevi=int((max(dd.index.max() for dd in H[kk].values())
                                           - min(dd.index.min() for dd in H[kk].values())).days))
                           for kk in S.RAJAD])

# =========================================== 9. VALUUTA / INDIKAATOR =====
print()
print("=" * 112)
print("S60.9  VALUUTA KAUPA (RADA M1, kogu universum, midagi EI EEMALDATA)")
print("=" * 112)
print(S.PAIS)
read = []
for c in C.VALUUTAD:
    sel = T["M1"][T["M1"]["cur"] == c]
    m = S.moot(sel, 0.0)
    print(S.rida(f"{c} ({I.KAART[c][0]})", m) if m
          else f"{c+' ('+I.KAART[c][0]+')':<30s}   n={len(sel)}  (alla 5)")
    read.append(rm(m, dict(valuuta=c, paar=I.KAART[c][0], n_toores=len(sel))))
salvesta("SUB60_CURRENCY.csv", read)

print()
print("=" * 112)
print("S60.10  INDIKAATOR JA GRUPID (RADA M1 + M5 koos, kogu universum)")
print("=" * 112)
TM = pd.concat([T["M1"], T["M5"]], ignore_index=True)
print(S.PAIS)
read = []
for ind in sorted(C.TIER1):
    sel = TM[TM["indicator"] == ind]
    m = S.moot(sel, 0.0)
    print(S.rida(f"{ind} ({C.TIER1[ind]:+d})", m) if m
          else f"{ind:<30s}   n={len(sel)}  (alla 5)")
    read.append(rm(m, dict(indikaator=ind, mark=C.TIER1[ind], n_toores=len(sel))))
GRUPID = {"CPI/inflatsioon": ["Inflation Rate", "Core Inflation Rate",
                              "Inflation Rate Mom"],
          "toohoive/NFP": ["Non Farm Payrolls", "Employment Change"],
          "tootus": ["Unemployment Rate"],
          "SKP": ["GDP Growth Rate", "GDP Annual Growth Rate"],
          "intressiotsus": ["Interest Rate"],
          "jaemuuk": ["Retail Sales MoM", "Retail Sales YoY"]}
print()
for g, liikmed in GRUPID.items():
    sel = TM[TM["indicator"].isin(liikmed)]
    m = S.moot(sel, 0.0)
    print(S.rida(f"GRUPP {g}", m) if m
          else f"{'GRUPP '+g:<30s}   n={len(sel)}  (alla 5)")
    read.append(rm(m, dict(grupp=g, n_toores=len(sel))))
salvesta("SUB60_INDICATOR.csv", read)

print()
print("=" * 112)
print("S60.11  ULLATUSE SUURUS (RADA M1 + M5 koos)")
print("=" * 112)
print(S.PAIS)
read = []
az = TM["z"].abs()
for lo, hi, silt in ((1.0, 1.5, "1.0 <= |z| < 1.5"),
                     (1.5, 2.0, "1.5 <= |z| < 2.0"),
                     (2.0, np.inf, "|z| >= 2.0")):
    sel = TM[(az >= lo) & (az < hi)]
    m = S.moot(sel, 0.0)
    print(S.rida(silt, m) if m else f"{silt:<30s}   n={len(sel)}  (alla 5)")
    read.append(rm(m, dict(vahemik=silt, n_toores=len(sel))))
salvesta("SUB60_MAGNITUDE.csv", read)

# =========================================== 12. SPREAD ==================
print()
print("=" * 112)
print("S60.12  SPREAD")
print("=" * 112)
print("  BID/ASK EI OLE SAADAVAL — vt allikate audit S60.0.")
print("  Seetottu EI SAA raporteerida: normal spread, release-time spread,")
print("  mediaan / p75 / p90 / p95 / max spread, spread widening.")
print("  KOIK need on DATA INSUFFICIENT. Neid EI HINNATA ega MODELLEERITA.")
print()
print("  MIDA SAAB OELDA: eeldatud tavaline round-trip kulu on")
print("  2.0-3.6 bp (paaripohine). Murdepunkt (max talutav kulu) on")
print(f"  RADA M1 {S.moot(T['M1'],0.0)['bruto_bp']:+.2f} bp.")
print("  Uudise ajal spread LAIENEB. Kui palju, seda me EI TEA.")
salvesta("SUB60_SPREAD.csv", [dict(moot=m, staatus="DATA INSUFFICIENT",
                                   pohjus="bid/ask puudub")
                              for m in ("normal_spread", "release_spread",
                                        "median", "p75", "p90", "p95", "max",
                                        "widening")])

# =========================================== 13. TEOSTATAVUS =============
print()
print("=" * 112)
print("S60.13  205 EUR / 0.01 LOT TEOSTATAVUS")
print("=" * 112)
KAPITAL, UHIKUD = 205.0, 1000.0
eurusd = float(H["M1"]["EURUSD"]["close"].iloc[-1])
m1 = S.moot(T["M1"], 0.0)
print(f"{'paar':<10s}{'60s sigma%':>13s}{'0.01 lot EUR':>15s}"
      f"{'1-sigma EUR':>14s}{'% kontost':>12s}{'oodatav bruto EUR':>19s}")
read, pnl_read = [], []
for paar in sorted(set(p for p, _ in I.KAART.values())):
    sel = T["M1"][T["M1"]["paar"] == paar]
    if len(sel) < 2:
        continue
    sig = float(sel["bruto"].std(ddof=1)) if len(sel) > 1 else np.nan
    nots = UHIKUD if paar[:3] == "EUR" else UHIKUD / eurusd
    pnl = nots * sig
    bruto_eur = nots * (m1["bruto_bp"] / 1e4)
    pnl_read.append(pnl)
    print(f"{paar:<10s}{100*sig:>13.3f}{nots:>15.0f}{pnl:>14.2f}"
          f"{100*pnl/KAPITAL:>12.2f}{bruto_eur:>19.3f}")
    read.append(dict(paar=paar, n=len(sel), sigma_60s_pct=100*sig,
                     lot001_eur=nots, sigma_eur=pnl,
                     pct_kontost=100*pnl/KAPITAL, oodatav_bruto_eur=bruto_eur))
nots_e = UHIKUD
print()
print(f"  oodatav BRUTO   0.01 lot EURUSD: "
      f"{nots_e*(m1['bruto_bp']/1e4):+.3f} EUR/tehing")
print(f"  tavaline kulu   0.01 lot EURUSD: "
      f"{nots_e*(m1['kulu_bp']/1e4):.3f} EUR/tehing")
print(f"  oodatav NETO    0.01 lot EURUSD: "
      f"{nots_e*(m1['neto_bp']/1e4):+.3f} EUR/tehing")
print(f"  uudise libisemine +5 bp lisaks : "
      f"{nots_e*5/1e4:.3f} EUR/tehing")
for risk in (0.0025, 0.0050):
    eur = KAPITAL * risk
    ok = sum(1 for q in pnl_read if q <= eur)
    print(f"  risk {100*risk:.2f}% = {eur:.2f} EUR -> taidetav "
          f"{ok}/{len(pnl_read)} paaril; vajalik konto "
          f"{min(pnl_read)/risk:.0f}-{max(pnl_read)/risk:.0f} EUR")
    read.append(dict(paar="KOKKU", risk=risk, eur=eur, taidetav=ok,
                     n_paari=len(pnl_read),
                     vajalik_konto_min=min(pnl_read)/risk,
                     vajalik_konto_max=max(pnl_read)/risk))
salvesta("SUB60_EXECUTION.csv", read)

print()
print("=" * 112)
print("VALJUNDFAILID")
print("=" * 112)
for nimi, n in VALJUND.items():
    print(f"  {nimi:<28s} {n} rida")
