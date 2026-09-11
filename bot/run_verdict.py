import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R

px = R.load_panel(); rets = R.returns(px); rates = R.load_rates(px.index)
MK = 0.030

print("=" * 124)
print("A) MIS MAKSAB UKS EURO EKSPONEERITUST AASTAS?")
print("=" * 124)
print(f"  CFD pikk positsioon : intress {100*rates.mean():.2f}% + juurdehindlus {100*MK:.2f}%"
      f"  = {100*(rates.mean()+MK):.2f}%/a")
print(f"  CFD turuneutraalne  : ainult juurdehindlus bruto pealt       = {100*MK:.2f}%/a")
print(f"  ETF / paris aktsia  : haldustasu ~0.07-0.20%                 =   0.15%/a")
print(f"  -> CFD-l on iga strateegia stardis {100*(rates.mean()+MK-0.0015):.2f} protsendipunkti taga.")

print()
print("=" * 124)
print("B) LOPLIK VORDLUS — KOIK TAISKULUDEGA, SAMA PERIOOD, SAMA KAPITAL")
print("=" * 124)
rows = []
def add(lbl, net, note=""):
    eq = (1+net).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
    dd = (eq/eq.cummax()-1).min()
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() else 0
    yy = net.groupby(net.index.year).apply(lambda x:(1+x).prod()-1)
    rows.append((lbl, cagr, sh, dd, (yy>0).sum(), len(yy), note))

# aktiivsed strateegiad, taiskulu
for lbl, w in [("TS momentum ANSAMBEL (CFD)", R.w_tsmom_ensemble(px, rets)),
               ("Donchian breakout (CFD)",    R.w_breakout(px, rets, 126)),
               ("Ristloikeline momentum (CFD)", R.w_xsmom(px, rets, 126, 5)),
               ("Faber trend pikk (CFD)",     R.w_long_only_trend(px, rets, 200)),
               ("Riskipariteet (CFD)",        R.w_equal_long(px, rets))]:
    r = R.evaluate_full(R.vol_target(w, rets, 0.15), rets, rates, markup=MK, label=lbl)
    add(lbl, r["net"])

# osta-ja-hoia, kahes umbrises
for s in ("SPX", "XAUUSD"):
    base = rets[s].copy()
    div = R.DIVI.get(s, 0.0)/252
    add(f"Osta-ja-hoia {s} (CFD 1x)", base + div - (rates+MK)/252)
    add(f"Osta-ja-hoia {s} (ETF/aktsia)", base + div - 0.0015/252)

# 60/40 tuupi segu ETF-ina
mix = 0.6*rets["SPX"] + 0.25*rets["XAUUSD"] + 0.15*rets["US10Y"]
add("Segu 60 SPX/25 kuld/15 vlk (ETF)", mix + 0.008/252 - 0.0015/252)

rows.sort(key=lambda r: -r[1])
print(f"{'':42s} {'CAGR':>8s} {'Sharpe':>8s} {'maxDD':>8s} {'+aastaid':>10s}")
print("-" * 124)
for lbl, cagr, sh, dd, p, n, note in rows:
    mark = "  <<<" if cagr == rows[0][1] else ""
    print(f"{lbl:42s} {100*cagr:+7.1f}% {sh:+8.2f} {100*dd:+7.1f}% {p:7d}/{n}{mark}")

print()
print("=" * 124)
print("C) FX CARRY — kas saab intressi ENDA KASUKS poorata?")
print("   Loomulik katse: JPY intress oli ~0 kogu perioodi, USA oma 0-5.3%.")
print("=" * 124)
uj = rets["USDJPY"]
for thr in (0.0, 0.01, 0.02, 0.03):
    sig = (rates > thr).astype(float).shift(1).fillna(0)
    # pikk USDJPY kui USA intress > thr: hinnaliikumine + saadud swap - juurdehindlus
    swap = (rates - 0.0) / 252.0          # intressivahe USD vs JPY
    net = sig * (uj + swap) - sig.abs() * MK/252.0
    add2 = (1+net).cumprod()
    yrs = len(net)/252
    cg = add2.iloc[-1]**(1/yrs)-1
    dd = (add2/add2.cummax()-1).min()
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() else 0
    inm = 100*sig.mean()
    print(f"  pikk USDJPY kui USA intress > {100*thr:.0f}%  (turul {inm:4.0f}% ajast)  "
          f"CAGR {100*cg:+6.2f}%  Sharpe {sh:+5.2f}  maxDD {100*dd:+6.1f}%")
print("  vordluseks: sama, AGA ilma saadud intressita (ainult hind):")
for thr in (0.02,):
    sig = (rates > thr).astype(float).shift(1).fillna(0)
    net = sig * uj - sig.abs()*MK/252.0
    e=(1+net).cumprod(); yrs=len(net)/252
    print(f"  pikk USDJPY kui intress > 2%, ilma carryta        "
          f"CAGR {100*(e.iloc[-1]**(1/yrs)-1):+6.2f}%  "
          f"Sharpe {net.mean()/net.std()*np.sqrt(252):+5.2f}")
