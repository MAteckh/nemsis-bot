"""
v5 LOPLIK HINDAMINE — carry parandatud, multiple testing, kulla analuus,
205 EUR teostatavus.

PARANDUS: CS-CARRY kasutab nuud AINULT LUKATUD intressivahet (nihe >= 1
paev). Lukkamata versioon andis Sharpe 4.35, mis osutus ETF-i ja
spot-seeria erineva sulgemisaja artefaktiks — kogu serv kadus 1-paevase
nihkega (+12.03 -> -1.89 bp).
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import v5_engine as V
from v5_run import korv_tootlus, S, C, KESK
from v5_registry import REGISTER

OUT = "v5_final.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

N_REG = len(REGISTER)
N_VARASEM = 11500                      # v4 testide arv

# ── ehita KOIK huopoteesid, carry LUKATUD ──────────────────────
carry_lag = C.reindex(S.index).ffill().rolling(60).mean().shift(1)
z = lambda d: d.sub(d.mean(axis=1), axis=0).div(d.std(axis=1).replace(0, np.nan), axis=0)

H = {}
for hid, lb in (("H01",1),("H02",5),("H03",20),("H04",60)):
    H[hid] = (f"CS-MOM-{lb}D", korv_tootlus(S.rolling(lb).sum())[0])
H["H05"] = ("CS-CARRY (lag 1p)", korv_tootlus(carry_lag)[0])
H["H06"] = ("CS-CARRY+MOM", korv_tootlus(z(carry_lag).add(z(S.rolling(20).sum()), fill_value=0))[0])
haal = sum(np.sign(S.rolling(lb).sum()) for lb in (1,5,20,60,120))
Wt = (np.sign(haal)/8.0).shift(1).fillna(0.0)
ix = Wt.index.intersection(S.index)
br = (Wt.reindex(ix)*S.reindex(ix)).sum(axis=1)
H["H07"] = ("TS-MOM-MULTI", br - Wt.reindex(ix).diff().abs().sum(axis=1).fillna(0)*KESK["BASE"]/1e4)
m20 = S.rolling(20).sum()
H["H08"] = ("MOM-ACCEL", korv_tootlus(m20 - m20.shift(20))[0])
H["H09"] = ("MOM-PERSIST", korv_tootlus((S>0).rolling(20).mean())[0])

w("=" * 100)
w("1) KOIK HUPOTEESID — CARRY PARANDATUD (lükatud 1 päev)")
w("=" * 100)
w(f"  {'ID':4s} {'hüpotees':20s} {'TRAIN':>8s} {'VALID':>8s} {'FINAL OOS':>10s} "
  f"{'Sharpe OOS':>11s} {'t (kogu)':>9s}")
w("  " + "-" * 74)
tul = []
for hid in sorted(H):
    nimi, x = H[hid]
    if x is None: continue
    x = x.dropna()
    tr, va, fo = V.jaota(x)
    m = V.moodikud(x)
    if m is None: continue
    tul.append(dict(id=hid, nimi=nimi, x=x, tr=float(tr.mean()), va=float(va.mean()),
                    fo=float(fo.mean()) if len(fo)>60 else np.nan,
                    sh_oos=V.sharpe(fo) if len(fo)>60 else np.nan, t=m["tstat"], sh=m["sh"]))
    w(f"  {hid} {nimi:20s} {1e4*float(tr.mean()):+8.2f} {1e4*float(va.mean()):+8.2f} "
      f"{1e4*float(fo.mean()):+10.2f} {V.sharpe(fo):+11.2f} {m['tstat']:+9.2f}")

# ── MULTIPLE TESTING ───────────────────────────────────────────
w("")
w("=" * 100)
w("2) MULTIPLE TESTING (Phase 4)")
w("=" * 100)
try:
    from scipy.stats import norm, t as tdist
    pv = [(r["id"], r["nimi"], 1 - norm.cdf(r["t"])) for r in tul]   # ühepoolne
    pv_sorted = sorted(pv, key=lambda z_: z_[2])
    w(f"  Registris {N_REG} hüpoteesi. Varasemalt tehtud ~{N_VARASEM} testi.")
    w("")
    w(f"  {'ID':4s} {'hüpotees':20s} {'p (ühepoolne)':>14s} {'BH lävend':>11s} "
      f"{'Bonferroni':>11s} {'Defl.Sharpe':>12s}")
    w("  " + "-" * 76)
    for i, (hid, nimi, p) in enumerate(pv_sorted, 1):
        bh = 0.05 * i / len(pv_sorted)
        bonf = 0.05 / len(pv_sorted)
        r = next(x for x in tul if x["id"] == hid)
        ds = V.deflated_sharpe(r["sh"], len(r["x"]), N_VARASEM + N_REG)
        w(f"  {hid} {nimi:20s} {p:14.4f} {bh:11.4f} {bonf:11.4f} {ds:12.3f}")
    w("")
    labib_bh = [h for i,(h,n_,p) in enumerate(pv_sorted,1) if p <= 0.05*i/len(pv_sorted)]
    w(f"  Benjamini-Hochberg läbijad: {labib_bh if labib_bh else 'MITTE ÜKSKI'}")
    w(f"  Deflated Sharpe > 0.95 (arvestab {N_VARASEM+N_REG} katset): "
      f"{[r['id'] for r in tul if V.deflated_sharpe(r['sh'], len(r['x']), N_VARASEM+N_REG) > 0.95] or 'MITTE ÜKSKI'}")
except Exception as e:
    w(f"  scipy puudub: {e}")

# ── PHASE 10: KULD ─────────────────────────────────────────────
w("")
w("=" * 100)
w("3) PHASE 10 — KULD: EDGE VÕI DRIFT?")
w("=" * 100)
import gold_logic
DD = V.lae("XAUUSD")
MIN_LOT, PV, MAX_LOSS = 0.01, 100.0, 45.0

def donchian(lb, luba=("buy","sell"), d=None):
    d = DD if d is None else d
    teh, lahti = [], None
    for i in range(lb+20, len(d)):
        paev = d.index[i]
        if lahti is not None:
            hi, lo = float(d["high"].iloc[i]), float(d["low"].iloc[i])
            th = (hi>=lahti["tp"]) if lahti["dir"]=="buy" else (lo<=lahti["tp"])
            sh_ = (lo<=lahti["sl"]) if lahti["dir"]=="buy" else (hi>=lahti["sl"])
            v = "sl" if (th and sh_) else ("tp" if th else ("sl" if sh_ else None))
            if v:
                tase = lahti["tp"] if v=="tp" else lahti["sl"]
                p = ((tase-lahti["e"]) if lahti["dir"]=="buy" else (lahti["e"]-tase))*MIN_LOT*PV
                teh.append((paev, p - 0.60, lahti["dir"]))   # 0.60 EUR kulu
                lahti = None
        if lahti is not None or paev.weekday() >= 5 or i+1 >= len(d): continue
        w_ = d.iloc[max(0,i-260):i+1]
        prior = w_.iloc[-(lb+1):-1]
        hind = float(w_["close"].iloc[-1]); atr = gold_logic.calc_atr(w_)
        if not (np.isfinite(atr) and atr>0): continue
        sig = "buy" if hind > float(prior["high"].max()) else (
              "sell" if hind < float(prior["low"].min()) else None)
        if sig is None or sig not in luba: continue
        sl_d = min(1.5*atr, MAX_LOSS/(MIN_LOT*PV)); tp_d = 3.0*atr
        e = float(d["open"].iloc[i+1])
        lahti = dict(dir=sig, e=e, tp=e+(tp_d if sig=="buy" else -tp_d),
                     sl=e-(sl_d if sig=="buy" else -sl_d))
    return teh

w("  a) LONG-ONLY vs SHORT-ONLY vs MÕLEMAD (lookback 50, kuludega)")
w(f"     {'variant':>14s} {'tehinguid':>10s} {'NETO':>10s} {'võit%':>7s}")
w("     " + "-" * 44)
for nm, luba in (("ainult LONG",("buy",)), ("ainult SHORT",("sell",)), ("mõlemad",("buy","sell"))):
    t = donchian(50, luba)
    if not t: continue
    x = np.array([p for _,p,_ in t])
    w(f"     {nm:>14s} {len(t):10d} {x.sum():+9.2f}€ {100*(x>0).mean():6.1f}%")

w("")
w("  b) PERIOODIDE KAUPA (lookback 50, mõlemad suunad)")
t = donchian(50)
ser = pd.Series([p for _,p,_ in t], index=[d for d,_,_ in t])
w(f"     {'periood':>12s} {'tehinguid':>10s} {'NETO':>10s} {'kuld tõusis':>13s}")
w("     " + "-" * 50)
for a0, a1 in ((2020,2022),(2022,2024),(2024,2025),(2025,2027)):
    g = ser[(ser.index.year>=a0)&(ser.index.year<a1)]
    dp = DD[(DD.index.year>=a0)&(DD.index.year<a1)]
    bh = 100*(float(dp["close"].iloc[-1])/float(dp["close"].iloc[0])-1) if len(dp)>10 else 0
    if len(g): w(f"     {f'{a0}-{a1-1}':>12s} {len(g):10d} {g.sum():+9.2f}€ {bh:+12.1f}%")

w("")
w("  c) WALK-FORWARD lookbacki valikul (vali TRAIN-ist, mõõda edasi)")
tul_lb = {}
for lb in (20,30,40,50,60,80,100):
    t = donchian(lb)
    s = pd.Series([p for _,p,_ in t], index=[d for d,_,_ in t])
    tul_lb[lb] = s
tr_par = max(tul_lb, key=lambda k: tul_lb[k][tul_lb[k].index <= V.TRAIN_LOPP].sum())
w(f"     TRAIN-i parim lookback: {tr_par}")
for nm, msk in (("TRAIN", lambda s: s.index <= V.TRAIN_LOPP),
                ("VALID", lambda s: (s.index > V.TRAIN_LOPP)&(s.index <= V.VALID_LOPP)),
                ("FINAL OOS", lambda s: s.index > V.VALID_LOPP)):
    s = tul_lb[tr_par]
    g = s[msk(s)]
    w(f"       {nm:10s} {len(g):4d} tehingut, NETO {g.sum():+9.2f}€")

w("")
w("  d) RISK-ADJUSTED võrdlus OSTA-JA-HOIA'ga")
alg = ser.index[0]
dp = DD[DD.index >= alg]
bh_eur = (float(dp["close"].iloc[-1]) - float(dp["close"].iloc[0])) * MIN_LOT * PV
bh_r = dp["close"].pct_change().dropna()
eq_s = 205 + ser.cumsum()
dd_s = float((eq_s/eq_s.cummax()-1).min())
eq_b = (1+bh_r).cumprod()
dd_b = float((eq_b/eq_b.cummax()-1).min())
w(f"     {'':22s} {'NETO':>10s} {'maxDD':>9s} {'tulu/DD':>9s}")
w("     " + "-" * 52)
w(f"     {'Donchian 50':22s} {ser.sum():+9.2f}€ {100*dd_s:+8.1f}% {abs(ser.sum()/(205*dd_s)):8.2f}")
w(f"     {'osta-ja-hoia 1 unts':22s} {bh_eur:+9.2f}€ {100*dd_b:+8.1f}% {abs(bh_eur/(205*dd_b)):8.2f}")

# ── PHASE 7: 205 EUR TEOSTATAVUS ───────────────────────────────
w("")
w("=" * 100)
w("4) PHASE 7 — 205 EUR TEOSTATAVUS iga kandidaadi kohta")
w("=" * 100)
w("  Nõue: risk tehingu kohta 0.25-1.0%. Miinimum-lot 0.01.")
w("")
w(f"  {'kandidaat':22s} {'instrument':12s} {'SL väärtus':>11s} {'% 205€-st':>11s} {'0.25-1%?':>10s}")
w("  " + "-" * 70)
for nimi, sym, sl_e in (("CS-korv (8 paari)", "FX korv", 8*1.6),
                        ("CS-korv (2 paari)", "2 FX paari", 2*1.6),
                        ("Donchian 50", "XAUUSD päev", 45.0)):
    pct = 100*sl_e/205
    w(f"  {nimi:22s} {sym:12s} {sl_e:10.2f}€ {pct:10.1f}% "
      f"{('JAH' if pct<=1 else ('1-2%' if pct<=2 else 'EI')):>10s}")
w("")
w("  CS-korv nõuab 2k paari korraga lahti (k=2 => 4 positsiooni). Iga")
w("  positsioon on miinimum 0.01 lot. 4 x 1.6€ SL = 6.4€ = 3.1% kontost.")
w("VALMIS")
