"""
PDF-I 15 KONFIGURATSIOONI AUS TEST.

PROTOKOLL on PDF-i punktist 5, jargitud tahttahelt:
  * 60% in-sample (parameetrite valik) / 20% validation / 20% FINAL OOS
  * FINAL OOS-i ei kasutata valikul MITTE KUIDAGI
  * spread + komisjon sees, kahel tasemel
  * vordlus baseline'iga: JUHUSLIK sisenemine sama SL/TP-ga
    (PDF: "buy-and-hold ei ole FX-is ideaalne vordlus, seega kasuta
     naiteks random-entry + sama SL/TP")
  * koik punkti 6 moodikud

MIDA SEE TEST EI KATA — oluline oelda:
  PDF soovitab 1H trend / 15m entry. Mul on ainult 1H. Seega
  sisenemine on jamedam kui dokument ette naeb. 15m sisenemine voib
  anda tapsema tayotuse, aga ka rohkem tehinguid ja rohkem kulu.
  Yahoo annab 15m ainult 60 paeva, millest ei piisa valideerimiseks.
"""
import warnings; warnings.filterwarnings("ignore")
import itertools, math
import numpy as np, pandas as pd
import h1engine as E
import paar_engine as P
import paar_config as C

rng = np.random.default_rng(1509)
OUT = "paarid_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()


def variandid(sym, cfg):
    """Koik parameetrikombinatsioonid, mida PDF selle paari kohta lubab."""
    out = []
    if cfg["rezim"] == "trend_pullback":
        for am, sl, tp in itertools.product(cfg["adx_min"], cfg["atr_sl"], cfg["tp_r"]):
            out.append(dict(tuup="trend_pullback", adx=am, sl=sl, tp=tp))
    elif cfg["rezim"] == "breakout_retest":
        for am, sl, tp, rt in itertools.product(cfg["adx_min"], cfg["atr_sl"],
                                                cfg["tp_r"], (True, False)):
            out.append(dict(tuup="breakout", adx=am, sl=sl, tp=tp, retest=rt))
    elif cfg["rezim"] == "mean_reversion":
        for am, sl, tp in itertools.product(cfg["adx_max"], cfg["atr_sl"], cfg["tp_r"]):
            out.append(dict(tuup="mean_rev", adx=am, sl=sl, tp=tp))
    elif cfg["rezim"] == "regime_switch":
        for al, sl, tp in itertools.product(cfg["adx_madal"], cfg["atr_sl_range"],
                                            cfg["tp_r"]):
            out.append(dict(tuup="mean_rev", adx=al, sl=sl, tp=tp, alam="range"))
        for ah, sl, tp in itertools.product(cfg["adx_korge"], cfg["atr_sl_murre"],
                                            cfg["tp_r"]):
            out.append(dict(tuup="breakout", adx=ah, sl=sl, tp=tp,
                            retest=False, alam="murre"))
    return out


def signaal(d, cfg, v, ind):
    if v["tuup"] == "trend_pullback":
        return P.sig_trend_pullback(d, cfg, v["adx"], ind)
    if v["tuup"] == "breakout":
        c2 = dict(cfg)
        c2.setdefault("ema", (20, 50, None))
        return P.sig_breakout(d, c2, v["adx"], ind, retest=v.get("retest", True))
    if v["tuup"] == "mean_rev":
        c2 = dict(cfg)
        c2.setdefault("bb", (20, 2.0))
        return P.sig_mean_rev(d, c2, v["adx"], ind)
    raise ValueError(v["tuup"])


w("=" * 104)
w("PDF-I 15 PAARIPÕHIST KONFIGURATSIOONI — AUS TEST")
w("=" * 104)
w("protokoll: 60% valik / 20% validation / 20% FINAL OOS (viimast ei kasutata valikul)")
w("kulud: retail-CFD spread + komisjon, edasi-tagasi")
w("")

koik_read = []
kokku_variante = 0
for sym, cfg in C.PAARID.items():
    d = E.lae(sym)
    if d is None:
        w(f"{sym}: ANDMEID EI OLE"); continue
    ind = P.valmista(d)
    kulu = E.KULU_RETAIL.get(sym, 1.5)
    sess = C.SESS[cfg["sess"]]
    n = len(d)
    i60, i80 = int(n * 0.60), int(n * 0.80)
    aastaid_k = (d.index[-1] - d.index[0]).days / 365.25

    vs = variandid(sym, cfg)
    kokku_variante += len(vs)
    for v in vs:
        sg = signaal(d, cfg, v, ind)
        if int((sg != 0).sum()) < 40:
            continue
        t = P.simuleeri(d, sg, v["sl"], v["tp"], kulu, ind, sess)
        if t is None or len(t) < 30:
            continue
        # jaota ajaliselt
        p60, p80 = d.index[i60], d.index[i80]
        tA = t[t["aeg"] < p60]
        tB = t[(t["aeg"] >= p60) & (t["aeg"] < p80)]
        tC = t[t["aeg"] >= p80]
        aA = max((p60 - d.index[0]).days / 365.25, .1)
        aB = max((p80 - p60).days / 365.25, .1)
        aC = max((d.index[-1] - p80).days / 365.25, .1)
        mA, mB, mC = (P.moodikud(tA, aA), P.moodikud(tB, aB), P.moodikud(tC, aC))
        mK = P.moodikud(t, aastaid_k)
        if mK is None:
            continue
        koik_read.append(dict(
            sym=sym, rezim=cfg["rezim"], **{k: v[k] for k in ("tuup", "adx", "sl", "tp")},
            retest=v.get("retest", None), alam=v.get("alam", ""),
            n=mK["n"], teh_kuus=mK["teh_kuus"], ootus=mK["ootus"], pf=mK["pf"],
            wr=mK["wr"], maxdd=mK["maxdd"], sharpe=mK["sharpe"], tstat=mK["tstat"],
            neto=mK["neto"], taastumis=mK["taastumis"],
            mae_r=mK["mae_r"], mfe_r=mK["mfe_r"], kestus=mK["kestus"],
            A=mA["ootus"] if mA else np.nan, nA=mA["n"] if mA else 0,
            B=mB["ootus"] if mB else np.nan, nB=mB["n"] if mB else 0,
            Cc=mC["ootus"] if mC else np.nan, nC=mC["n"] if mC else 0))

df = pd.DataFrame(koik_read)
df.to_csv("data/paarid.csv", index=False)
w(f"variante genereeritud: {kokku_variante}, piisavalt tehinguid: {len(df)}")
w(f"(salvestatud data/paarid.csv)")

# ══ 1) IGA PAAR: PDF-I KESKMISED PARAMEETRID, KOGU PERIOOD ══════
w("")
w("=" * 104)
w("1) IGA PAAR PDF-i KESKMISTE PARAMEETRITEGA — kogu periood")
w("=" * 104)
w(f"  {'paar':8s} {'režiim':16s} {'teh':>5s} {'teh/kuus':>9s} {'võit%':>7s} "
  f"{'ootus bp':>9s} {'PF':>6s} {'maxDD':>8s} {'Sharpe':>7s} {'t':>6s}")
w("  " + "-" * 92)
for sym in C.PAARID:
    g = df[df["sym"] == sym]
    if not len(g):
        w(f"  {sym:8s} — liiga vähe tehinguid"); continue
    # PDF-i keskmine: vota mediaan-SL ja mediaan-TP
    g2 = g.iloc[(g["sl"] - g["sl"].median()).abs().argsort()[:1]]
    r = g2.iloc[0]
    w(f"  {r['sym']:8s} {r['rezim']:16s} {r['n']:5d} {r['teh_kuus']:9.1f} "
      f"{r['wr']:6.1f}% {1e4*r['ootus']:+9.1f} {r['pf']:6.2f} "
      f"{100*r['maxdd']:+7.1f}% {r['sharpe']:+7.2f} {r['tstat']:+6.2f}")

# ══ 2) ULDPILT ══════════════════════════════════════════════════
w("")
w("=" * 104)
w("2) ÜLDPILT — kõik variandid koos")
w("=" * 104)
w(f"   variante kokku: {len(df)}")
w(f"   ootus > 0     : {int((df['ootus']>0).sum())} ({100*(df['ootus']>0).mean():.1f}%)")
w(f"   profit factor > 1: {int((df['pf']>1).sum())} ({100*(df['pf']>1).mean():.1f}%)")
w(f"   keskmine ootus: {1e4*df['ootus'].mean():+.1f}bp   parim {1e4*df['ootus'].max():+.1f}bp")
w("")
w(f"   {'režiim':18s} {'variante':>9s} {'plussis':>9s} {'keskm bp':>10s} {'parim bp':>10s}")
w("   " + "-" * 60)
for rz, g in df.groupby("rezim"):
    w(f"   {rz:18s} {len(g):9d} {100*(g['ootus']>0).mean():8.1f}% "
      f"{1e4*g['ootus'].mean():+10.1f} {1e4*g['ootus'].max():+10.1f}")

# ══ 3) 60/20/20 — PDF-I NOUTUD PROTOKOLL ═══════════════════════
w("")
w("=" * 104)
w("3) 60/20/20 PROTOKOLL — vali A-st, kinnita B-l, MÕÕDA C-l (C-d ei kasutata valikul)")
w("=" * 104)
w(f"   {'paar':8s} {'valitud: ADX/SL/TP':>20s} {'A (valik)':>11s} "
  f"{'B (valid.)':>11s} {'C (FINAL OOS)':>14s} {'C teh':>7s}")
w("   " + "-" * 80)
oos_pos = oos_n = 0
c_vals = []
for sym in C.PAARID:
    g = df[(df["sym"] == sym) & (df["nA"] >= 15)]
    if not len(g):
        w(f"   {sym:8s} — liiga vähe tehinguid valikuaknas"); continue
    r = g.loc[g["A"].idxmax()]          # VALIK AINULT A PEALT
    oos_n += 1
    oos_pos += (r["Cc"] > 0)
    c_vals.append(r["Cc"])
    mark = "  <<<" if r["Cc"] > 0 else ""
    w(f"   {sym:8s} {f'{r.adx:.0f}/{r.sl:.2f}/{r.tp:.1f}':>20s} "
      f"{1e4*r['A']:+10.1f} {1e4*r['B']:+10.1f} {1e4*r['Cc']:+13.1f} "
      f"{int(r['nC']):7d}{mark}")
w("")
w(f"   FINAL OOS plussis: {oos_pos}/{oos_n}  (mündivisega oodatav {oos_n/2:.1f})")
if c_vals:
    w(f"   FINAL OOS keskmine ootus: {1e4*np.mean(c_vals):+.1f}bp")

# ══ 4) BASELINE: JUHUSLIK SISENEMINE SAMA SL/TP-GA ═════════════
w("")
w("=" * 104)
w("4) BASELINE (PDF punkt 5) — JUHUSLIK sisenemine sama SL/TP-ga")
w("=" * 104)
w("   Kui strateegia ei löö juhuslikku sisenemist, ei ole signaalis midagi.")
w(f"   {'paar':8s} {'strateegia bp':>14s} {'JUHUSLIK bp':>13s} {'vahe':>9s} {'järeldus':>14s}")
w("   " + "-" * 64)
parem = 0
for sym in C.PAARID:
    g = df[df["sym"] == sym]
    if not len(g):
        continue
    r = g.loc[g["ootus"].idxmax()]
    d = E.lae(sym); ind = P.valmista(d)
    kulu = E.KULU_RETAIL.get(sym, 1.5)
    sess = C.SESS[C.PAARID[sym]["sess"]]
    # juhuslik: sama arv signaale, juhuslikud ajad, juhuslik suund
    n = len(d)
    juh = []
    for _ in range(5):
        idx = rng.choice(np.arange(250, n - 1), size=min(int(r["n"]) * 3, n - 300),
                         replace=False)
        s2 = pd.Series(0.0, index=d.index)
        s2.iloc[np.sort(idx)] = rng.choice([-1.0, 1.0], size=len(idx))
        t2 = P.simuleeri(d, s2, r["sl"], r["tp"], kulu, ind, sess)
        m2 = P.moodikud(t2, 1.0)
        if m2:
            juh.append(m2["ootus"])
    if not juh:
        continue
    jm = float(np.mean(juh))
    vahe = r["ootus"] - jm
    parem += (vahe > 0)
    w(f"   {sym:8s} {1e4*r['ootus']:+13.1f} {1e4*jm:+12.1f} {1e4*vahe:+8.1f} "
      f"{'parem' if vahe > 0 else 'HALVEM':>14s}")
w("")
w(f"   Juhuslikust parem: {parem}/{len(C.PAARID)}")
w("VALMIS")
