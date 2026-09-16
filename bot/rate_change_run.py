"""
rate_change_run.py — INTEREST-RATE DIFFERENTIAL CHANGE, tulemused.
Jookseb PARAST rate_change_audit.py-d (33 kontrolli, 0 FAIL).

PRIMARY on AINULT: CHANGE_D_4W -> jargmine ava -> 4 nadalat.
Koik muu on secondary/kirjeldav ja on nii ka margitud.
"""
import math
import os

import numpy as np
import pandas as pd

import cot_engine as E
import rate_change as RC

JUUR = RC.JUUR
rs = np.random.RandomState(RC.SEEME)
VALJUND = {}


def salvesta(nimi, read):
    df = pd.DataFrame(read)
    df.to_csv(os.path.join(JUUR, nimi), index=False)
    VALJUND[nimi] = len(df)
    return df


def rm(m, extra=None):
    if m is None:
        return dict(extra or {})
    d = {kk: m[kk] for kk in ("n", "bruto_bp", "med_bp", "neto_bp", "wr",
                              "sd_bp", "t", "p")}
    d.update(extra or {})
    return d


paarid = RC.paarid_28()
O, C = RC.valuuta_vaartused()
Rd = RC.maarad_paevas(C.index)
D = RC.diferentsiaal(Rd, paarid)
T = RC.tehingud(O, C, D, paarid)
KULU_KESK = 1e4 * float(T["kulu"].mean())

print("=" * 112)
print("RC.0  VALIM, ANDMED, EELREGISTREERITUD SPETSIFIKATSIOON")
print("=" * 112)
print(f"  maarad   BIS WS_CBPOL keskpankade poliitikamaarad, kuu lopp")
print(f"           2016-01 .. 2026-08, 8 valuutat, nihe 1 kuu (v6 reegel)")
print(f"  hinnad   Yahoo paevane _d25, USD-jalgadest, 8 valuutat sunkroonselt")
print(f"           {C.index.min().date()} .. {C.index.max().date()}, {len(C)} sessiooni")
print(f"  universum {len(paarid)} unikaalset paari")
print(f"  PRIMARY  CHANGE_D_4W = D(t) - D(t-4 nadalat)")
print(f"           sisenemine jargmise sessiooni AVAHIND, hoid 20 sessiooni")
print(f"  kulu     edasi-tagasi, keskmine {KULU_KESK:.2f} bp "
      f"(major {2*1.0:.1f}-{2*1.8:.1f}, rist {2*E.KULU_RIST:.1f})")
print(f"  tehinguid {len(T)},  {T['vaatlus'].min().date()} .. {T['vaatlus'].max().date()}"
      f"  = {(T['vaatlus'].max()-T['vaatlus'].min()).days/365.25:.2f} aastat")
print(f"  jaotus   TRAIN .. {RC.TRAIN_LOPP.date()}  VALID .. {RC.VALID_LOPP.date()}"
      f"  FINAL OOS {RC.VALID_LOPP.date()} ..")

# ==================================================== 1. PRIMARY ==========
print()
print("=" * 112)
print("RC.1  PRIMARY TULEMUS — CHANGE_D_4W, hoid 4 nadalat")
print("=" * 112)
prim = RC.moot(T["bruto"].values, T["kulu"].values)
pn = RC.moot(T["neto"].values)
KB = RC.kohordid(T, "bruto")
KN = RC.kohordid(T, "neto")
sh = float(KN["sharpe"].mean())
aastaid = (T["vaatlus"].max() - T["vaatlus"].min()).days / 365.25
print(RC.PAIS)
print(RC.rida("PRIMARY CHANGE_D_4W", prim))
print()
print(f"  bruto / kulu  = {prim['bruto_bp']/KULU_KESK:.2f} x   (NEMSIS noue >= 2.00)")
print(f"  neto bp       = {prim['neto_bp']:+.2f}")
print(f"  sd            = {prim['sd_bp']:.1f} bp")
print(f"  MITTEKATTUVAD KOHORDID (iga 4. vaatlusnadal; koik 4 faasi, faasi")
print(f"  EI VALITA tulemuse jargi). Ainult need on paris aktsiakover:")
print(f"{'faas':<8s}{'n':>6s}{'bruto kum%':>13s}{'neto kum%':>12s}"
      f"{'neto maxDD%':>14s}{'Sharpe':>9s}")
for i in range(len(KN)):
    print(f"{int(KN['faas'][i]):<8d}{int(KN['n'][i]):>6d}"
          f"{100*KB['kum'][i]:>+13.1f}{100*KN['kum'][i]:>+12.1f}"
          f"{KN['maxdd'][i]:>14.1f}{KN['sharpe'][i]:>9.2f}")
print(f"{'KESKMINE':<8s}{'':>6s}{100*KB['kum'].mean():>+13.1f}"
      f"{100*KN['kum'].mean():>+12.1f}{KN['maxdd'].mean():>14.1f}{sh:>9.2f}")
print(f"  aastane neto ~ {100*float(KN['keskm_bp'].mean())/1e4*52/RC.HOID_N:+.2f}%")
read = [rm(prim, dict(test="PRIMARY_CHANGE_D_4W", sharpe=sh,
                      kohort_neto_kum=float(KN["kum"].mean()),
                      kohort_maxdd=float(KN["maxdd"].mean()),
                      kulu_kordne=prim["bruto_bp"] / KULU_KESK))]

# ==================================================== 2. POORDKONTROLL ====
print()
print("=" * 112)
print("RC.2  POORDKONTROLL JA TASEMEKONTROLL (KIRJELDAV, mitte live-kandidaat)")
print("=" * 112)
T_inv = T.copy()
T_inv["bruto"] = -T_inv["bruto"]
T_inv["neto"] = T_inv["bruto"] - T_inv["kulu"]
T_lvl = RC.tehingud(O, C, D, paarid, signaal_alus="LEVEL")
print(RC.PAIS)
print(RC.rida("PRIMARY sign(CHANGE_D)", prim))
print(RC.rida("  poordsignaal (kirjeldav)",
              RC.moot(T_inv["bruto"].values, T_inv["kulu"].values)))
m_lvl = RC.moot(T_lvl["bruto"].values, T_lvl["kulu"].values)
print(RC.rida("  sign(D) TASE (v6 mehhanism)", m_lvl))
read.append(rm(RC.moot(T_inv["bruto"].values, T_inv["kulu"].values),
               dict(test="POORD_kirjeldav")))
read.append(rm(m_lvl, dict(test="LEVEL_sign_D_kirjeldav")))

# kui palju CHANGE ja LEVEL signaalid kattuvad?
liit = T.merge(T_lvl[["paar", "vaatlus", "suund", "signaal_vaartus"]],
               on=["paar", "vaatlus"], suffixes=("_ch", "_lv"))
kattuv = 100.0 * float((liit["suund_ch"] == liit["suund_lv"]).mean())
print(f"\n  CHANGE ja LEVEL signaalid on samasuunalised {kattuv:.1f}% ajast")
print(f"  korr(CHANGE_D, D) = "
      f"{float(np.corrcoef(liit['signaal_vaartus_ch'], liit['signaal_vaartus_lv'])[0,1]):+.4f}")
print("  => mehhanismid on statistiliselt eristatavad, CHANGE ei ole")
print("     TASEME umberpakendamine.")

# ==================================================== 3. PAARID ===========
print()
print("=" * 112)
print("RC.3  PAARIDE KAUPA (norku EI EEMALDATA)")
print("=" * 112)
print(RC.PAIS)
pread = []
for p in paarid:
    x = T[T["paar"] == p]
    m = RC.moot(x["bruto"].values, x["kulu"].values)
    print(RC.rida(p, m) if m else f"{p:<28s}{len(x):>7d}   (alla 20)")
    pread.append(rm(m, dict(paar=p, kulu_1suund_bp=RC.kulu_bp(p))))
salvesta("RC_PAIR.csv", pread)
kokku = float(T["bruto"].sum())
g = T.groupby("paar")["bruto"].sum().sort_values(ascending=False)
pos_p = int((g > 0).sum())
print(f"\n  positiivseid paare (bruto): {pos_p}/{len(paarid)}")
print(f"  kogu bruto logsumma {100*kokku:+.2f}%")
print(f"    top 1 paar  {g.index[0]:<8s} {100*g.iloc[0]:+7.2f}% = "
      f"{100*g.iloc[0]/kokku:6.1f}% kogusummast")
print(f"    top 2 paari {g.index[0]}+{g.index[1]:<8s} "
      f"{100*g.iloc[:2].sum():+7.2f}% = {100*g.iloc[:2].sum()/kokku:6.1f}%")
print(f"  NEMSIS standard: top-1 osakaal < 30%  =>  "
      f"{'LABIB' if 100*g.iloc[0]/kokku < 30 else 'KUKUB'}")
print()
print("  FALSIFITSEERIMINE — kas serv jaab alles, kui suurim panustaja")
print("  eemaldada? (See EI OLE paaride valimine, vaid vastupidine test.)")
print(RC.PAIS)
for silt, sel in ((f"ilma {g.index[0]}",
                   T[T['paar'] != g.index[0]]),
                  (f"ilma {g.index[0]}+{g.index[1]}",
                   T[~T['paar'].isin([g.index[0], g.index[1]])])):
    print(RC.rida(silt, RC.moot(sel["bruto"].values, sel["kulu"].values)))

# ==================================================== 4. AASTAD ===========
print()
print("=" * 112)
print("RC.4  AASTATE KAUPA (halbu aastaid EI EEMALDATA)")
print("=" * 112)
print(f"{'aasta':<10s}{'n':>7s}{'bruto_bp':>10s}{'neto_bp':>10s}{'wr%':>8s}{'t':>7s}")
yread = []
pos_y = tot_y = 0
for y in sorted(T["vaatlus"].dt.year.unique()):
    x = T[T["vaatlus"].dt.year == y]
    m = RC.moot(x["bruto"].values, x["kulu"].values)
    if m is None:
        print(f"{y:<10d}{len(x):>7d}   (alla 20)")
        yread.append(dict(aasta=int(y), n=len(x)))
        continue
    tot_y += 1
    pos_y += m["neto_bp"] > 0
    print(f"{y:<10d}{m['n']:>7d}{m['bruto_bp']:>+10.2f}{m['neto_bp']:>+10.2f}"
          f"{m['wr']:>8.1f}{m['t']:>7.2f}")
    yread.append(rm(m, dict(aasta=int(y))))
salvesta("RC_YEAR.csv", yread)
print(f"\n  neto positiivseid aastaid: {pos_y}/{tot_y}")

# ==================================================== 5. WALK-FORWARD =====
print()
print("=" * 112)
print("RC.5  WALK-FORWARD (jaotus fikseeritud ENNE tulemusi, kalendriaastad)")
print("=" * 112)
print(RC.PAIS)
wread = []
for nimi, m_ in (("TRAIN", T["vaatlus"] <= RC.TRAIN_LOPP),
                 ("VALID", (T["vaatlus"] > RC.TRAIN_LOPP)
                  & (T["vaatlus"] <= RC.VALID_LOPP)),
                 ("FINAL OOS", T["vaatlus"] > RC.VALID_LOPP)):
    x = T[m_]
    m = RC.moot(x["bruto"].values, x["kulu"].values)
    print(RC.rida(nimi, m))
    wread.append(rm(m, dict(osa=nimi)))
salvesta("RC_WALKFORWARD.csv", wread)

# ==================================================== 6. RANDOMIZATION ====
print()
print("=" * 112)
print(f"RC.6  RANDOMIZATION ({RC.N_PERM} korda)")
print("=" * 112)
suund = T["suund"].values.astype(float)
alus = T["bruto"].values / suund                 # suunata tootlus
tegelik = 1e4 * float(T["bruto"].mean())
a = np.array([1e4 * (rs.choice([-1.0, 1.0], size=len(alus)) * alus).mean()
              for _ in range(RC.N_PERM)])
sv = T["signaal_vaartus"].values
b = np.array([1e4 * (np.sign(rs.permutation(sv)) * alus).mean()
              for _ in range(RC.N_PERM)])
print(f"  tegelik bruto {tegelik:+.3f} bp  (n = {len(alus)})")
nread = []
for nimi, arr in (("A juhuslik suund", a), ("B segatud CHANGE_D", b)):
    pp = float((arr >= tegelik).mean())
    print(f"  {nimi:<22s} mediaan {np.median(arr):+.3f}  "
          f"95% {np.quantile(arr,0.95):+.3f}  max {arr.max():+.3f}   p = {pp:.4f}")
    nread.append(dict(null=nimi, n_perm=RC.N_PERM, tegelik_bp=tegelik,
                      mediaan_bp=float(np.median(arr)),
                      p95_bp=float(np.quantile(arr, 0.95)),
                      max_bp=float(arr.max()), p=pp))
salvesta("RC_NULL.csv", nread)

# ==================================================== 7. KULUTUNDLIKKUS ===
print()
print("=" * 112)
print("RC.7  KULUTUNDLIKKUS")
print("=" * 112)
print(f"{'kulu uhesuunaline':<26s}{'edasi-tagasi':>14s}{'bruto_bp':>10s}"
      f"{'neto_bp':>10s}{'kordne':>9s}{'verdikt':>10s}")
cread = []
for c1 in RC.KULU_TASEMED:
    rt = 2 * c1
    neto = prim["bruto_bp"] - rt
    kord = prim["bruto_bp"] / rt if rt > 0 else float("inf")
    v = "—" if rt == 0 else ("LABIB" if kord >= 2 else "KUKUB")
    print(f"{f'{c1:.2f} bp':<26s}{rt:>14.2f}{prim['bruto_bp']:>+10.2f}"
          f"{neto:>+10.2f}{kord:>9.2f}{v:>10s}")
    cread.append(dict(kulu_1suund_bp=c1, kulu_rt_bp=rt,
                      bruto_bp=prim["bruto_bp"], neto_bp=neto, kordne=kord,
                      verdikt=v))
print(f"{'NEMSIS BASE (paaripohine)':<26s}{KULU_KESK:>14.2f}"
      f"{prim['bruto_bp']:>+10.2f}{prim['neto_bp']:>+10.2f}"
      f"{prim['bruto_bp']/KULU_KESK:>9.2f}"
      f"{('LABIB' if prim['bruto_bp']/KULU_KESK >= 2 else 'KUKUB'):>10s}")
cread.append(dict(kulu_1suund_bp=KULU_KESK / 2, kulu_rt_bp=KULU_KESK,
                  bruto_bp=prim["bruto_bp"], neto_bp=prim["neto_bp"],
                  kordne=prim["bruto_bp"] / KULU_KESK,
                  verdikt="NEMSIS BASE"))
salvesta("RC_COST.csv", cread)

# ==================================================== 8. BENCHMARK ========
print()
print("=" * 112)
print("RC.8  BENCHMARK (valitud ENNE tulemuste nagemist)")
print("=" * 112)
T_long = T.copy()
T_long["bruto"] = T_long["bruto"] * T_long["suund"]     # taasta marketa tootlus
m_ew = RC.moot(T_long["bruto"].values, T_long["kulu"].values)
bh = np.log(RC.paari_hind(C, "EURUSD"))
bh = bh[(bh.index >= T["sisse"].min()) & (bh.index <= T["valja"].max())]
bh_kum = float(np.expm1(bh.iloc[-1] - bh.iloc[0]))
print(RC.PAIS)
print(RC.rida("PRIMARY CHANGE_D_4W", prim))
print(RC.rida("A vordkaaluline FX (LONG baas)", m_ew))
print(f"{'B osta-ja-hoia EURUSD':<28s}  kumulatiivne {100*bh_kum:+.1f}% "
      f"({bh.index[0].date()} .. {bh.index[-1].date()})")
print()
print("  BENCHMARKI PIIRANG: NEMSIS-is ei ole standardiseeritud FX-")
print("  benchmarki. Primary moot on paari log-tootlus, mis on 28 paari")
print("  ristloikes juba turuneutraalne: ristloikeline tsentreerimine")
print("  taandub paaritasemel valja, sest log(V_b/V_q) miinus keskmine")
print("  kahel jalal annab tapselt sama arvu. Seetottu on 'pair return'")
print("  ja 'market-neutral excess return' SIIN MATEMAATILISELT SAMA.")
read.append(rm(m_ew, dict(test="BENCHMARK_A_equal_weight_long")))
salvesta("RC_PRIMARY.csv", read)

# ==================================================== 9. KVARTIILID =======
print()
print("=" * 112)
print("RC.9  CHANGE_D SUURUSE KVARTIILID (KIRJELDAV — mitte uus strateegia)")
print("=" * 112)
T2 = T.copy()
T2["abs_sig"] = T2["signaal_vaartus"].abs()
qs = T2["abs_sig"].quantile([0.25, 0.5, 0.75]).values
print(f"  |CHANGE_D| kvartiilipiirid: {qs[0]:.3f} / {qs[1]:.3f} / {qs[2]:.3f} pp")
print(f"  KVARTIILID KOLLAPSEERUVAD. Pohjus: keskpangad liiguvad 0.25 pp")
print(f"  sammudega, seega |CHANGE_D| EI OLE pidev suurus. Jaotus:")
jaot = T2["abs_sig"].round(3).value_counts().sort_index()
for v, n in jaot.items():
    print(f"    |CHANGE_D| = {v:.2f} pp : {n:>5d} tehingut "
          f"({100*n/len(T2):5.1f}%)")
print()
print("  Raporteerin selle asemel TEGELIKUD tasemed (kirjeldav):")
print(RC.PAIS)
qread = []
for v in jaot.index:
    x = T2[T2["abs_sig"].round(3) == v]
    m = RC.moot(x["bruto"].values, x["kulu"].values)
    print(RC.rida(f"|CHANGE_D| = {v:.2f} pp", m)
          if m else f"{f'|CHANGE_D| = {v:.2f} pp':<28s}{len(x):>7d}   (alla 20)")
    qread.append(rm(m, dict(change_d_pp=float(v), n_kokku=len(x))))
salvesta("RC_QUARTILE.csv", qread)
print("  HOIATUS: kvartiilid on kirjeldavad. Neist EI TEHTA strateegiat.")

# ================================================ 10. KESKPANGA DIAGNOOS ==
print()
print("=" * 112)
print("RC.10  KESKPANGA OTSUSE DIAGNOSTIKA (mitte uus strateegia)")
print("=" * 112)
print("  PIIRANG: NEMSIS-il EI OLE keskpankade istungite kuupaevi.")
print("  BIS-i andmed on KUISED, seega 'otsuse hetk' on teada ainult kuu")
print("  tapsusega. Diagnostika tehakse selle piiri sees.")
R0 = pd.read_csv(f"{RC.DATA}/policy_rates.csv")
R0["Month"] = pd.to_datetime(R0["Month"] + "-01")
R0 = R0.set_index("Month").sort_index()
muut = (R0.diff().abs() > 1e-9)
print(f"\n  maara MUUTUSI kuude kaupa 2016-2026:")
for c in RC.VALUUTAD:
    n = int(muut[c].sum())
    kk = int(R0[c].notna().sum())
    print(f"    {c}: {n:>3d} muutust {kk} kuu jooksul = {100*n/max(kk,1):4.1f}% kuudest")

# Kui suur osa NADALASTEST vaatlustest annab uldse signaali?
T_lvl_n = len(T_lvl)
print(f"\n  KOIK nadalased vaatlused (kus D on olemas): {T_lvl_n}")
print(f"  neist CHANGE_D != 0 ehk kaubeldavaid:       {len(T)}  "
      f"({100*len(T)/T_lvl_n:.1f}%)")
print(f"\n  => SEE ONGI DIAGNOOS. CHANGE_D on nullist erinev TAPSELT SIIS,")
print(f"     kui uks kahest keskpangast muutis maara viimase 4 nadala")
print(f"     jooksul. Signaal EI OLE pidev muutuja, vaid SUNDMUSSIGNAAL:")
print(f"     100% tehingutest jargneb poliitikaotsusele. Jaotust")
print(f"     'otsuse ajal vs otsuste vahel' EI SAA teha — 'otsuste vahel'")
print(f"     grupp on definitsiooni jargi tuhi.")
print(f"\n  Millise valuuta otsus signaali kannab (tehingute arv paari jalas):")
jalad = {}
for c in RC.VALUUTAD:
    jalad[c] = int(T["paar"].str[:3].eq(c).sum() + T["paar"].str[3:].eq(c).sum())
for c, n in sorted(jalad.items(), key=lambda r: -r[1]):
    print(f"    {c}: {n:>5d} tehingujalga ({100*n/(2*len(T)):4.1f}%)")
print(f"\n  PIIRANG JAAB: ilma istungite kuupaevadeta ei saa eristada")
print(f"  'otsuse hetke reaktsiooni' ja 'otsuse-jargset drifti'.")

# ================================================ 11. TEOSTATAVUS =========
print()
print("=" * 112)
print("RC.11  TEOSTATAVUS 205 EUR KONTOL")
print("=" * 112)
n_a = len(T) / aastaid
korraga = float(T.groupby("vaatlus").size().mean()) * RC.HOID_N
print(f"  tehinguid {len(T)} / {aastaid:.2f} a = {n_a:.0f} aastas")
print(f"  keskmine hoidmisaeg {float((T['valja']-T['sisse']).dt.days.mean()):.1f} "
      f"kalendripaeva (20 sessiooni)")
print(f"  KORRAGA AVATUD positsioone keskmiselt {korraga:.0f} "
      f"(uus korv iga nadal, hoid 4 nadalat)")
KAPITAL, UHIKUD = 205.0, 1000.0
eurusd = float(RC.paari_hind(C, "EURUSD").iloc[-1])
print()
print(f"{'paar':<10s}{'4-nad sigma%':>14s}{'0.01 lot EUR':>15s}"
      f"{'1-sigma EUR':>14s}{'% kontost':>12s}")
pnl_read = []
for p in paarid[:7] + ["EURJPY", "AUDNZD"]:
    x = T[T["paar"] == p]
    if len(x) < 20:
        continue
    sig = float(x["bruto"].std(ddof=1))
    baas = p[:3]
    nots = (UHIKUD if baas == "EUR" else UHIKUD / eurusd if baas == "USD"
            else UHIKUD * float(RC.paari_hind(C, baas + "USD").iloc[-1]) / eurusd
            if baas + "USD" in paarid
            else UHIKUD / float(RC.paari_hind(C, "USD" + baas).iloc[-1]) / eurusd)
    pnl = nots * sig
    pnl_read.append(pnl)
    print(f"{p:<10s}{100*sig:>14.2f}{nots:>15.0f}{pnl:>14.2f}"
          f"{100*pnl/KAPITAL:>12.1f}")
for risk in (0.0025, 0.0050):
    eur = KAPITAL * risk
    ok = sum(1 for q in pnl_read if q <= eur)
    print(f"  kavatsetud risk {100*risk:.2f}% = {eur:.2f} EUR -> "
          f"taidetav {ok}/{len(pnl_read)} paaril; vajalik konto "
          f"{min(pnl_read)/risk:.0f}-{max(pnl_read)/risk:.0f} EUR "
          f"UHE positsiooni kohta")
print(f"  NB: korraga on avatud ~{korraga:.0f} positsiooni => vajalik konto")
print(f"      korrutub sellega, kui positsioone ei netita.")

print()
print("=" * 112)
print("VALJUNDFAILID")
print("=" * 112)
for nimi, n in VALJUND.items():
    print(f"  {nimi:<28s} {n} rida")
