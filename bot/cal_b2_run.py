"""
cal_b2_run.py — B2 tulemused. Jookseb PARAST cal_b2_audit.py-d.

Kogu event-time grid on KIRJELDAV. AINUS jareldav test on eelregistreeritud
T+8h -> T+32h (cal_b2.PRIMARY_SISSE / PRIMARY_VALJA).
"""
import math
import os

import numpy as np
import pandas as pd

import cal_b2 as B
import cal_engine as C
import cal_run as R1

JUUR = B.JUUR
rs = np.random.RandomState(B.SEEME)
VALJUND = {}


def salvesta(nimi, read):
    df = pd.DataFrame(read)
    df.to_csv(os.path.join(JUUR, nimi), index=False)
    VALJUND[nimi] = len(df)
    return df


def r_moot(m, extra=None):
    if m is None:
        return None
    d = {kk: m[kk] for kk in ("n", "bruto_bp", "med_bp", "neto_bp", "wr",
                              "sd_bp", "t", "p", "kum_bruto", "kum_neto")}
    if extra:
        d.update(extra)
    return d


# ============================================================ VALIM ========
d, HV = B.valim()
d = B.lisa_horisondid(d, HV, "SEINAKELL")
db = B.lisa_horisondid(B.valim()[0], HV, "BAARE")
LOGV = np.log(HV.values)
x = d[d["z"].abs() >= C.LAVI].copy()
xb = db[db["z"].abs() >= C.LAVI].copy()
K = B.KULU_RT_BP

print("=" * 110)
print("B2.0  VALIM JA AKEN")
print("=" * 110)
print(f"  H1 valuutamaatriks : {HV.index.min()} .. {HV.index.max()}  "
      f"{len(HV)} baari, 8 valuutat")
print(f"  TIER 1 sundmused z-ga H1 aknas : {len(d)}")
print(f"  neist |z| >= {C.LAVI} (primary valim)   : {len(x)}")
print(f"  periood: {x['ts'].min().date()} .. {x['ts'].max().date()}  "
      f"= {(x['ts'].max()-x['ts'].min()).days/365.25:.2f} aastat")
print(f"  kulu: {K:.2f} bp edasi-tagasi (1 valuutajalg)")
print(f"  VORDLUSEKS B1 paevane aken: 2013-08-16 .. 2026-09-15 = 13.1 aastat")

# ================================================= 1. EVENT-TIME PROFIILE ==
print()
print("=" * 110)
print("B2.1  EVENT-TIME PROFIIL (KIRJELDAV) — kumulatiivne ankrust (teate-eelne hind)")
print("=" * 110)
print("  NB: loik 0h->1h sisaldab teatehupet ennast ja EI OLE kaubeldav.")
print("      Kumulatiiv +1h.. sisaldab seda hupet. Kaubeldav osa on loikudes.")
print()
print(B.PAIS + f"{'kum_bruto%':>12s}{'sd_bp':>8s}")
read = []
for h in B.HORISONDID:
    xx = x[x[f"p{h}"] >= 0]
    r = (xx["suund"] * xx[f"h{h}"]).dropna()
    m = B.moot(r, K)
    if m is None:
        continue
    print(B.rida(f"SEINAKELL  +{h}h", m) +
          f"{100*m['kum_bruto']:>12.2f}{m['sd_bp']:>8.1f}")
    read.append(r_moot(m, dict(reziim="SEINAKELL", horisont_h=h,
                               valja_jaetud=len(x) - len(xx))))
print()
for h in B.HORISONDID:
    xx = xb[xb[f"p{h}"] >= 0]
    r = (xx["suund"] * xx[f"h{h}"]).dropna()
    m = B.moot(r, K)
    if m is None:
        continue
    print(B.rida(f"BAARILUGEMINE  +{h} baari", m) +
          f"{100*m['kum_bruto']:>12.2f}{m['sd_bp']:>8.1f}")
    read.append(r_moot(m, dict(reziim="BAARE", horisont_h=h,
                               valja_jaetud=len(xb) - len(xx))))
salvesta("B2_EVENT_TIME_PROFILE.csv", read)

# ==================================================== 2. LOIGUD (BUCKETS) ==
print()
print("=" * 110)
print("B2.2  LOIKUDE KAUPA (INCREMENTAL) — kus mojuI TEGELIKULT tekib")
print("=" * 110)
print("  Iga loik arvutatakse AINULT nendel sundmustel, millel on MOLEMAD")
print("  otspunktid olemas. Nii ei tule vahe erinevast valimist.")
print()
print(f"{'loik':<30s}{'n':>7s}{'inkr_bp':>10s}{'med_bp':>9s}{'wr%':>7s}"
      f"{'t':>7s}{'p':>8s}")
read = []
for a, b in [(0, 1)] + B.LOIGUD:
    if a == 0:
        xx = x[x[f"p{b}"] >= 0]
        r = (xx["suund"] * xx[f"h{b}"]).dropna()
        silt = "0h->1h  (TEATEHUPE, ei ole kaubeldav)"
    else:
        xx = x[(x[f"p{a}"] >= 0) & (x[f"p{b}"] >= 0)]
        i1 = xx[f"p{a}"].values
        i2 = xx[f"p{b}"].values
        rr = B.neutraalne(LOGV, i1, i2, xx["cur_idx"].values)
        r = pd.Series(xx["suund"].values * rr).dropna()
        silt = f"{a}h->{b}h"
    m = B.moot(r, 0.0)
    if m is None:
        continue
    print(f"{silt:<30s}{m['n']:>7d}{m['bruto_bp']:>+10.2f}{m['med_bp']:>+9.2f}"
          f"{m['wr']:>7.1f}{m['t']:>7.2f}{m['p']:>8.3f}")
    read.append(r_moot(m, dict(loik=silt, algus_h=a, lopp_h=b)))
salvesta("B2_INCREMENTAL.csv", read)

# ====================================================== 3. PRIMARY TEST ====
print()
print("=" * 110)
print(f"B2.3  PRIMARY — eelregistreeritud T+{B.PRIMARY_SISSE}h -> "
      f"T+{B.PRIMARY_VALJA}h  (AINUS jareldav test)")
print("=" * 110)
A, Z = B.PRIMARY_SISSE, B.PRIMARY_VALJA
xp = x[(x[f"p{A}"] >= 0) & (x[f"p{Z}"] >= 0)].copy()
xp["pnl"] = xp["suund"].values * B.neutraalne(
    LOGV, xp[f"p{A}"].values, xp[f"p{Z}"].values, xp["cur_idx"].values)
xp = xp[xp["pnl"].notna()].copy()
prim = B.moot(xp["pnl"].values, K)
print(B.PAIS)
print(B.rida(f"PRIMARY T+{A}h -> T+{Z}h", prim))
print(f"\n  kumulatiivne bruto {100*prim['kum_bruto']:+.2f}%   "
      f"neto {100*prim['kum_neto']:+.2f}%   sd {prim['sd_bp']:.1f} bp")
print(f"  bruto / kulu = {prim['bruto_bp']/K:.2f} x   "
      f"(NEMSIS noue >= 2.00)")
read = [r_moot(prim, dict(test="PRIMARY_T8_T32", reziim="SEINAKELL",
                          bruto_kulu_kordne=prim["bruto_bp"] / K))]

xpb = xb[(xb[f"p{A}"] >= 0) & (xb[f"p{Z}"] >= 0)].copy()
rrb = xpb["suund"].values * B.neutraalne(
    LOGV, xpb[f"p{A}"].values, xpb[f"p{Z}"].values, xpb["cur_idx"].values)
mb = B.moot(rrb, K)
print(B.rida(f"  sama, BAARILUGEMINE", mb))
read.append(r_moot(mb, dict(test="PRIMARY_T8_T32", reziim="BAARE",
                            bruto_kulu_kordne=mb["bruto_bp"] / K)))

# =============================================== 4. POSITIIVNE / NEGATIIVNE
print()
print("=" * 110)
print("B2.4  POSITIIVNE vs NEGATIIVNE ULLATUS (primary aknas)")
print("=" * 110)
print(B.PAIS)
for silt, sel in (("A positiivne ullatus z>=+1", xp[xp["z"] >= C.LAVI]),
                  ("B negatiivne ullatus z<=-1", xp[xp["z"] <= -C.LAVI]),
                  ("C moLEMAD koos", xp)):
    m = B.moot(sel["pnl"].values, K)
    print(B.rida(silt, m))
    read.append(r_moot(m, dict(test=silt, reziim="SEINAKELL")))
salvesta("B2_PRIMARY.csv", read)

# ==================================================== 5. PIDEV ULLATUS =====
print()
print("=" * 110)
print("B2.5  PIDEV ULLATUS — signal = z * mark, ilma uute teisendusteta")
print("=" * 110)
dp = d[(d[f"p{A}"] >= 0) & (d[f"p{Z}"] >= 0)].copy()
dp["r"] = B.neutraalne(LOGV, dp[f"p{A}"].values, dp[f"p{Z}"].values,
                       dp["cur_idx"].values)
dp = dp[dp["r"].notna()]
zz = np.clip((dp["z"] * dp["mark"]).values, -5, 5)
rr = dp["r"].values
kor = float(np.corrcoef(zz, rr)[0, 1])
beta = float(np.cov(zz, rr, ddof=1)[0, 1] / np.var(zz, ddof=1))
tk = kor * math.sqrt(len(zz) - 2) / math.sqrt(max(1 - kor ** 2, 1e-12))
print(f"  n = {len(zz)}  (KOIK TIER 1 sundmused, mitte ainult |z|>=1)")
print(f"  korr(z*mark, r) = {kor:+.4f}")
print(f"  beeta           = {1e4*beta:+.2f} bp 1 z-uhiku kohta")
print(f"  t               = {tk:+.2f}   p = {C.p_kahepoolne(tk):.4f}")

# ================================================= 6. B1 PAEVANE SEOS ======
print()
print("=" * 110)
print("B2.6  SEOS B1 PAEVASE TESTIGA")
print("=" * 110)
d1, V1 = R1.ehita()
x1 = d1[(d1["z"].abs() >= C.LAVI) & (d1["tier"] == "T1")]
H1_ALGUS = pd.Timestamp("2023-11-27")
print(B.PAIS)
for silt, sel, kol in (
        ("B1 TIER1 1d KOGU 13.1a", x1, "r1"),
        ("B1 TIER1 2d KOGU 13.1a", x1, "r2"),
        ("B1 TIER1 5d KOGU 13.1a", x1, "r5"),
        ("B1 TIER1 1d H1-aknas", x1[x1["ts"] >= H1_ALGUS], "r1"),
        ("B1 TIER1 2d H1-aknas", x1[x1["ts"] >= H1_ALGUS], "r2"),
        ("B1 TIER1 5d H1-aknas", x1[x1["ts"] >= H1_ALGUS], "r5")):
    m = B.moot((sel["suund"] * sel[kol]).dropna().values, K)
    print(B.rida(silt, m))
print(B.rida(f"B2 PRIMARY T+{A}->T+{Z} H1-aknas", prim))
print()
print("  Miks EI OLE need uks-uhele vorreldavad:")
print("   - B1 1d = paevabaari sulgemisest sulgemiseni. Sisenemine on")
print("     esimene sulgemine PARAST teadet, mis on teate kellaajast")
print("     soltuvalt 0.1 .. 24 h hiljem (mediaan ~8.5 h).")
print("   - B2 primary on IGAL sundmusel tapselt T+8h -> T+32h.")
print("   - B1 hoiab 24 h KALENDRIAEGA (sh nadalavahetus), B2 hoiab 24 h,")
print("     aga jatab nadalavahetusele sattuvad valja (tolerants 4 h).")
print("   - Valimid on erineva suurusega: B1 H1-aknas n="
      f"{len(x1[x1['ts']>=H1_ALGUS])}, B2 primary n={len(xp)}.")

# ======================================= 6B. LAHKNEVUSE DIAGNOOS ==========
print()
print("=" * 110)
print("B2.6B  LAHKNEVUSE DIAGNOOS — miks B1 paevane +7.28 bp ja B2 primary +1.47 bp?")
print("=" * 110)
print("  Molemad vaidavad: sisenen PARAST teadet, hoian ~24 h. Vahe on 5x.")
print("  Enne jareldust tuleb see lahti votta. Kolm kandidaati:")
print("    (i)   ajastus — B1 ankurdub PAEVA SULGEMISELE, B2 teate hetkele")
print("    (ii)  andmeallikas — B1 Yahoo paevane _d25, B2 H1-baarid")
print("    (iii) valim — B1 n=408, B2 n=276 (nadalavahetuse valjajatmised)")
print()

# (i) korda B1 AJASTUST H1-baaridel: sisene 21:00 UTC sulgemisel, valju
#     jargmisel 21:00 UTC sulgemisel. Sama kell, sama reegel, AGA H1-hinnad.
h1ix = pd.DatetimeIndex(HV.index)
sulg_ix = h1ix + pd.Timedelta(hours=1)
on_21 = np.where(sulg_ix.hour == C.PAEVA_SULG_UTC)[0]      # sulgub 21:00 UTC
s21 = sulg_ix[on_21]
def b1_ajastus(ts_arr):
    """Esimene 21:00 UTC sulgemine PARAST T, ja sellele jargnev 21:00."""
    pos = np.searchsorted(s21.values, np.asarray(ts_arr, dtype="datetime64[ns]"),
                          side="right")
    ok = (pos >= 0) & (pos + 1 < len(s21))
    i_in = np.where(ok, on_21[np.clip(pos, 0, len(on_21) - 1)], -1)
    i_out = np.where(ok, on_21[np.clip(pos + 1, 0, len(on_21) - 1)], -1)
    return i_in, i_out, np.where(ok, (s21.values[np.clip(pos, 0, len(s21)-1)]
                                      - np.asarray(ts_arr, dtype="datetime64[ns]"))
                                 / np.timedelta64(1, "h"), np.nan)

xd = x.copy()
i_in, i_out, viivitus = b1_ajastus(xd["ts"].values)
xd["i_in"], xd["i_out"], xd["viivitus_h"] = i_in, i_out, viivitus
xd = xd[(xd["i_in"] >= 0) & (xd["i_out"] >= 0)].copy()
# nouame, et sisenemine ja valjumine on tapselt 24 h vahega (mitte nadalavahetus)
vahe = (sulg_ix[xd["i_out"].values] - sulg_ix[xd["i_in"].values]) / pd.Timedelta(hours=1)
xd["hoid_h"] = vahe.values
xd["pnl_b1aeg"] = xd["suund"].values * B.neutraalne(
    LOGV, xd["i_in"].values, xd["i_out"].values, xd["cur_idx"].values)
print(B.PAIS)
print(B.rida("B1 TIER1 1d H1-aknas (Yahoo _d)",
             B.moot((x1[x1["ts"] >= H1_ALGUS]["suund"]
                     * x1[x1["ts"] >= H1_ALGUS]["r1"]).dropna().values, K)))
print(B.rida("B1 AJASTUS, aga H1-hindadega",
             B.moot(xd["pnl_b1aeg"].dropna().values, K)))
print(B.rida("B2 PRIMARY T+8 -> T+32", prim))
print(f"\n  B1-ajastuse sisenemisviivitus H1-baaridel: mediaan "
      f"{np.nanmedian(xd['viivitus_h']):.1f} h, "
      f"5% {np.nanpercentile(xd['viivitus_h'],5):.1f} h, "
      f"95% {np.nanpercentile(xd['viivitus_h'],95):.1f} h")
print(f"  hoidmisaeg: mediaan {np.median(xd['hoid_h']):.0f} h, "
      f"max {xd['hoid_h'].max():.0f} h (nadalavahetus)")

# (ii) B1 paevane efekt SISENEMISVIIVITUSE kaupa — kas efekt on seal,
#      kus viivitus on luhike (st teate lahedal)?
print()
print("  B1 paevase efekti jaotus SISENEMISVIIVITUSE jargi (kogu 13.1 a valim):")
pos_d = C.paevane_sisenemine(x1["ts"].values, V1.index)
mm = pos_d >= 0
x1d = x1[mm].copy()
# cal_run.ehita sailitab cal_engine.lae_kalender'i RangeIndeksi => sama voti
x1d["algne_idx"] = x1d.index
sis_d = pd.DatetimeIndex(V1.index[pos_d[mm]]) + pd.Timedelta(hours=C.PAEVA_SULG_UTC)
x1d["viivitus_h"] = (sis_d - pd.DatetimeIndex(x1d["ts"])) / pd.Timedelta(hours=1)
print(f"{'viivitus':<30s}{'n':>7s}{'bruto':>9s}{'med':>8s}{'neto':>8s}"
      f"{'wr%':>7s}{'t':>7s}{'p':>8s}")
for lo, hi in [(0, 2), (2, 6), (6, 10), (10, 16), (16, 25)]:
    sel = x1d[(x1d["viivitus_h"] >= lo) & (x1d["viivitus_h"] < hi)]
    m = B.moot((sel["suund"] * sel["r1"]).dropna().values, K)
    print(B.rida(f"  {lo}-{hi} h parast teadet", m))

# (iii) sama valim: B2 primary sundmused, mootedetud B1 paevase reegliga
print()
print("  SAMA VALIM, KAKS MOOTU (ainult sundmused, mis on molemas):")
ristu = xp.merge(x1d[["algne_idx", "r1", "viivitus_h"]], on="algne_idx",
                 how="inner")
m_b2 = B.moot(ristu["pnl"].values, K)
m_b1 = B.moot((ristu["suund"] * ristu["r1"]).dropna().values, K)
print(B.PAIS)
print(B.rida(f"  B1 paevane 1d  (n ristub)", m_b1))
print(B.rida(f"  B2 T+8 -> T+32 (n ristub)", m_b2))
print(f"\n  => vahe EI OLE valim: samadel sundmustel on B1 "
      f"{m_b1['bruto_bp']:+.2f} bp ja B2 {m_b2['bruto_bp']:+.2f} bp.")

# ==================================== 6C. KUMB HINNASEERIA ON SUNKROONNE? ==
print()
print("=" * 110)
print("B2.6C  ANDMEALLIKA KONTROLL — kas paevane seeria on fikseeritud")
print("       kellaajaga hetktoomsvott?")
print("=" * 110)
import h1engine as HE
h_e = HE.lae("EURUSD")["close"]
sulg_e = pd.DatetimeIndex(h_e.index) + pd.Timedelta(hours=1)
d_e = C.lae_hind("EURUSD", "_d25")
print("  EURUSD paevatootluse korrelatsioon (Yahoo _d25 vs H1 kell X sulgemine):")
korr = []
for hh_ in range(24):
    sel = np.where(sulg_e.hour == hh_)[0]
    if len(sel) < 400:
        continue
    S = h_e.iloc[sel].copy()
    S.index = sulg_e[sel].normalize()
    S = S[~S.index.duplicated(keep="last")]
    ixx = S.index.intersection(d_e.index)
    if len(ixx) < 300:
        continue
    korr.append((hh_, float(np.log(S.reindex(ixx)).diff()
                            .corr(np.log(d_e.reindex(ixx)).diff())), len(ixx)))
korr.sort(key=lambda r: -r[1])
for hh_, kk_, nn_ in korr[:3]:
    print(f"    parim {hh_:02d}:00 UTC -> korr {kk_:.3f}  (n={nn_})")
print(f"    halvim {korr[-1][0]:02d}:00 UTC -> korr {korr[-1][1]:.3f}")
print("    Sunkroonse hetktoomsvotu korral peaks parim korr olema ~0.99.")
print(f"    Mooedetud maksimum on {korr[0][1]:.2f} => paevane sulgemine EI OLE")
print("    fikseeritud kellaajal. Sellest tuleneb, et ristloikeline")
print("    tsentreerimine (8 valuutat) kasutab MITTESUNKROONSEID hindu.")

# vaaljalaske kellaaja jaotus — kas B1 sisenemine sai olla teate-eelne?
print()
print("  B1 paevane TIER 1 efekt VALJALASKE KELLAAJA jargi (kogu 13.1 a):")
x1h = x1.copy()
x1h["tund"] = pd.DatetimeIndex(x1h["ts"]).hour
print(f"{'kellaaeg UTC':<30s}{'n':>7s}{'bruto':>9s}{'med':>8s}{'neto':>8s}"
      f"{'wr%':>7s}{'t':>7s}{'p':>8s}")
for lo, hi, silt in [(0, 6, "00-06 Aasia"), (6, 12, "06-12 Euroopa"),
                     (12, 17, "12-17 US hommik"),
                     (17, 21, "17-21 enne paeva sulgemist"),
                     (21, 24, "21-24 parast paeva sulgemist")]:
    sel = x1h[(x1h["tund"] >= lo) & (x1h["tund"] < hi)]
    m = B.moot((sel["suund"] * sel["r1"]).dropna().values, K)
    print(B.rida(f"  {silt}", m) if m
          else f"  {silt:<28s}{len(sel):>7d}   (alla 20)")
print("  Kui B1 sisenemishind oleks susteemselt TEATE-EELNE, peaks efekt")
print("  olema koige suurem hilise valjalaskega sundmustel (17-21 UTC),")
print("  sest just seal on eeldatud 21:00 sulgemine teatele koige lahemal.")

salvesta("B2_DIAGNOSTIC.csv", [
    dict(test="B1 paevane 1d, Yahoo _d25, H1-aken", n=m_b1["n"],
         bruto_bp=m_b1["bruto_bp"], t=m_b1["t"], p=m_b1["p"]),
    dict(test="B1 AJASTUS (21:00->21:00), H1-hinnad",
         **{kk: B.moot(xd["pnl_b1aeg"].dropna().values, K)[kk]
            for kk in ("n", "bruto_bp", "t", "p")}),
    dict(test="B2 PRIMARY T+8 -> T+32, H1-hinnad", n=m_b2["n"],
         bruto_bp=m_b2["bruto_bp"], t=m_b2["t"], p=m_b2["p"]),
    dict(test="EURUSD paevatootluse korr Yahoo vs H1 (parim tund)",
         n=korr[0][2], bruto_bp=np.nan, t=np.nan, p=np.nan,
         korr=korr[0][1], tund=korr[0][0]),
])

# ================================================== 7. WALK-FORWARD ========
print()
print("=" * 110)
print("B2.7  WALK-FORWARD — eelregistreeritud KALENDRIAASTA-jaotus")
print("=" * 110)
print(f"  TRAIN     .. {B.B2_TRAIN_LOPP.date()}")
print(f"  VALID     {(B.B2_TRAIN_LOPP+pd.Timedelta(seconds=1)).date()} .. "
      f"{B.B2_VALID_LOPP.date()}")
print(f"  FINAL OOS {(B.B2_VALID_LOPP+pd.Timedelta(seconds=1)).date()} ..")
print("  Jaotus on valitud ENNE tulemuste vaatamist, kalendriaasta jargi,")
print("  MITTE tulemuse jargi. B1 jaotus siin ei toota (vt audit F3).")
print()
print(B.PAIS)
read = []
jaotus = [("TRAIN", xp["ts"] <= B.B2_TRAIN_LOPP),
          ("VALID", (xp["ts"] > B.B2_TRAIN_LOPP) & (xp["ts"] <= B.B2_VALID_LOPP)),
          ("FINAL OOS", xp["ts"] > B.B2_VALID_LOPP)]
for nimi, m_ in jaotus:
    m = B.moot(xp[m_]["pnl"].values, K)
    print(B.rida(nimi, m))
    read.append(r_moot(m, dict(osa=nimi)))
salvesta("B2_WALKFORWARD.csv", read)

# ================================================= 8. RANDOMIZATION =======
print()
print("=" * 110)
print(f"B2.8  RANDOMIZATION NULL ({B.N_PERM} korda, primary aknas)")
print("=" * 110)
suunad = xp["suund"].values.astype(float)
baas = xp["pnl"].values / suunad          # suunata tootlus
tegelik = 1e4 * float(xp["pnl"].mean())
a = np.array([1e4 * (rs.choice([-1.0, 1.0], size=len(baas)) * baas).mean()
              for _ in range(B.N_PERM)])
b = np.array([1e4 * (rs.permutation(suunad) * baas).mean()
              for _ in range(B.N_PERM)])
print(f"  tegelik bruto: {tegelik:+.3f} bp  (n = {len(baas)})")
read = []
for nimi, arr in (("A juhuslik suund", a), ("B segatud ullatus", b)):
    p = float((arr >= tegelik).mean())
    print(f"  {nimi:<22s} mediaan {np.median(arr):+.3f}  5% {np.quantile(arr,0.05):+.3f}"
          f"  95% {np.quantile(arr,0.95):+.3f}  max {arr.max():+.3f}   p = {p:.4f}")
    read.append(dict(null=nimi, n_perm=B.N_PERM, tegelik_bp=tegelik,
                     mediaan_bp=float(np.median(arr)),
                     p05_bp=float(np.quantile(arr, 0.05)),
                     p95_bp=float(np.quantile(arr, 0.95)),
                     max_bp=float(arr.max()), p=p))
salvesta("B2_NULL.csv", read)

# ================================================= 9. KULUTUNDLIKKUS ======
print()
print("=" * 110)
print("B2.9  KULUTUNDLIKKUS (primary T+8 -> T+32)")
print("=" * 110)
print(f"{'kulu uhesuunaline':<30s}{'edasi-tagasi':>14s}{'bruto_bp':>10s}"
      f"{'neto_bp':>10s}{'kordne':>9s}{'verdikt':>10s}")
read = []
for c1 in B.KULU_TASEMED:
    rt = 2 * c1
    neto = prim["bruto_bp"] - rt
    kord = prim["bruto_bp"] / rt if rt > 0 else float("inf")
    v = "LABIB" if (rt > 0 and kord >= 2) else ("—" if rt == 0 else "KUKUB")
    silt = f"{c1:.2f} bp" + ("  <= NEMSIS BASE" if abs(c1 - 1.25) < 1e-9 else "")
    print(f"{silt:<30s}{rt:>14.2f}{prim['bruto_bp']:>+10.2f}{neto:>+10.2f}"
          f"{kord:>9.2f}{v:>10s}")
    read.append(dict(kulu_1suund_bp=c1, kulu_rt_bp=rt,
                     bruto_bp=prim["bruto_bp"], neto_bp=neto,
                     kordne=kord, verdikt=v))
salvesta("B2_COST.csv", read)

# ================================================== 10. AASTATE KAUPA =====
print()
print("=" * 110)
print("B2.10  AASTATE KAUPA (primary, halbu aastaid EI EEMALDATA)")
print("=" * 110)
print(f"{'aasta':<10s}{'n':>7s}{'bruto_bp':>10s}{'neto_bp':>10s}{'wr%':>7s}{'t':>7s}")
read = []
for y in sorted(xp["ts"].dt.year.unique()):
    xx = xp[xp["ts"].dt.year == y]
    m = B.moot(xx["pnl"].values, K)
    if m is None:
        print(f"{y:<10d}{len(xx):>7d}   (alla 20 sundmuse — ei raporteerita)")
        read.append(dict(aasta=int(y), n=len(xx)))
        continue
    print(f"{y:<10d}{m['n']:>7d}{m['bruto_bp']:>+10.2f}{m['neto_bp']:>+10.2f}"
          f"{m['wr']:>7.1f}{m['t']:>7.2f}")
    read.append(r_moot(m, dict(aasta=int(y))))
salvesta("B2_YEAR.csv", read)

# ================================================ 11. VALUUTA KAUPA =======
print()
print("=" * 110)
print("B2.11  VALUUTA KAUPA (primary, norku EI EEMALDATA)")
print("=" * 110)
print(B.PAIS)
read = []
for c in C.VALUUTAD:
    xx = xp[xp["cur"] == c]
    m = B.moot(xx["pnl"].values, K)
    print(B.rida(c, m, 30) if m else f"{c:<30s}{len(xx):>7d}   (alla 20)")
    read.append(r_moot(m, dict(valuuta=c)) or dict(valuuta=c, n=len(xx)))
salvesta("B2_CURRENCY.csv", read)

kokku = float(xp["pnl"].sum())
g = xp.groupby("cur")["pnl"].sum().sort_values(ascending=False)
print(f"\n  KONTSENTRATSIOON (B1 standard: osakaal kogu bruto logsummast)")
print(f"  kogu bruto logsumma {100*kokku:+.2f}%")
print(f"    top 1 valuuta  {g.index[0]:<6s} {100*g.iloc[0]:+7.2f}% = "
      f"{100*g.iloc[0]/kokku:6.1f}% kogusummast")
print(f"    top 2 valuutat {g.index[0]}+{g.index[1]:<4s} "
      f"{100*g.iloc[:2].sum():+7.2f}% = {100*g.iloc[:2].sum()/kokku:6.1f}%")
print(f"    positiivseid valuutasid (bruto) {int((g>0).sum())}/{len(g)}")

# ============================================== 12. INDIKAATORI KAUPA =====
print()
print("=" * 110)
print("B2.12  INDIKAATORI KAUPA (primary, KOIK TIER 1, ka halvad)")
print("=" * 110)
print(B.PAIS)
read = []
for ind in sorted(C.TIER1):
    xx = xp[xp["indicator"] == ind]
    m = B.moot(xx["pnl"].values, K)
    print(B.rida(f"{ind} ({C.TIER1[ind]:+d})", m, 30) if m
          else f"{ind + ' (' + f'{C.TIER1[ind]:+d}' + ')':<30s}{len(xx):>7d}   (alla 20)")
    read.append(r_moot(m, dict(indikaator=ind, mark=C.TIER1[ind]))
                or dict(indikaator=ind, mark=C.TIER1[ind], n=len(xx)))
salvesta("B2_INDICATOR.csv", read)
gi = xp.groupby("indicator")["pnl"].sum().sort_values(ascending=False)
print(f"\n  top 1 indikaator {gi.index[0]:<28s} "
      f"{100*gi.iloc[0]/kokku:6.1f}% kogusummast")
print(f"  top 2 indikaatorit                             "
      f"{100*gi.iloc[:2].sum()/kokku:6.1f}%")

# ============================================== 13. MULTIPLE TESTING ======
print()
print("=" * 110)
print("B2.13  MITMIKTESTIMINE")
print("=" * 110)
prof = pd.read_csv(os.path.join(JUUR, "B2_EVENT_TIME_PROFILE.csv"))
sk = prof[prof["reziim"] == "SEINAKELL"]
labis, lavi = B.bh(sk["p"].values)
pos = ((sk["bruto_bp"].values > 0) & labis)
print(f"  Event-time grid = {len(sk)} horisonti. Need on KIRJELDAVAD,")
print(f"  mitte {len(sk)} soltumatut kinnitavat testi.")
print(f"  BH q=0.05: labib {int(labis.sum())}/{len(sk)}, lavi p <= {lavi:.4f}")
print(f"  NEIST POSITIIVSEID: {int(pos.sum())}  "
      f"(oluline negatiivne EI OLE serv)")
print(f"  Bonferroni p-lavi {0.05/len(sk):.4f}; "
      f"labib {int((sk['p'].values <= 0.05/len(sk)).sum())}")
print()
print(f"  PRIMARY (eelregistreeritud, 1 test): p = {prim['p']:.4f}")
print(f"  Primary EI VAJA mitmiktestimise korrektsiooni, sest ta oli")
print(f"  valitud ENNE tulemusi. Profiil vajab ja on markitud kirjeldavaks.")

# ================================================= 14. TEOSTATAVUS ========
print()
print("=" * 110)
print("B2.14  TEOSTATAVUS 205 EUR KONTOL")
print("=" * 110)
aastaid = (xp["ts"].max() - xp["ts"].min()).days / 365.25
n_a = len(xp) / aastaid
hoid = np.median((pd.DatetimeIndex(HV.index[xp[f"p{Z}"].values])
                  - pd.DatetimeIndex(HV.index[xp[f"p{A}"].values]))
                 / pd.Timedelta(hours=1))
print(f"  tehinguid {len(xp)} / {aastaid:.2f} a = {n_a:.0f} aastas")
print(f"  keskmine hoidmisaeg {hoid:.1f} h ({hoid/24:.2f} paeva)")
print(f"  aastane bruto {n_a*prim['bruto_bp']/100:+.2f}%  "
      f"kulu {n_a*K/100:.2f}%  neto {n_a*(prim['bruto_bp']-K)/100:+.2f}%")
print()
KAPITAL, UHIKUD = 205.0, 1000.0
eurusd = float(HV["EUR"].iloc[-1])
sig = {}
for c in C.VALUUTAD:
    i1 = xp[f"p{A}"].values
    i2 = xp[f"p{Z}"].values
    dd = LOGV[i2] - LOGV[i1]
    dd = dd - dd.mean(axis=1, keepdims=True)
    sig[c] = float(dd[:, C.VALUUTAD.index(c)].std())
BAAS = {"EUR": "EUR", "GBP": "GBP", "AUD": "AUD", "NZD": "NZD",
        "JPY": "USD", "CHF": "USD", "CAD": "USD", "USD": "USD"}
print(f"{'valuuta':<10s}{'24h sigma%':>13s}{'0.01 lot EUR':>15s}"
      f"{'1-sigma EUR':>14s}{'% kontost':>12s}")
pnl_read = []
for c in C.VALUUTAD:
    bb = BAAS[c]
    nots = (UHIKUD if bb == "EUR" else UHIKUD / eurusd if bb == "USD"
            else UHIKUD * float(HV[bb].iloc[-1]) / eurusd)
    pnl = nots * sig[c]
    pnl_read.append(pnl)
    print(f"{c:<10s}{100*sig[c]:>13.2f}{nots:>15.0f}{pnl:>14.2f}"
          f"{100*pnl/KAPITAL:>12.1f}")
for risk in (0.0025, 0.0050):
    eur = KAPITAL * risk
    ok = sum(1 for p in pnl_read if p <= eur)
    print(f"  kavatsetud risk {100*risk:.2f}% = {eur:.2f} EUR -> "
          f"taidetav {ok}/8 valuutal; vajalik konto "
          f"{min(pnl_read)/risk:.0f}-{max(pnl_read)/risk:.0f} EUR")

print()
print("=" * 110)
print("VALJUNDFAILID")
print("=" * 110)
for nimi, n in VALJUND.items():
    print(f"  {nimi:<34s} {n} rida")
