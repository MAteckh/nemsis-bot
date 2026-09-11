import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
import research as R

px = R.load_panel(); rets = R.returns(px)

def rp(p, r, target=0.15):
    return R.vol_target(R.w_equal_long(p, r), r, target)

print("=" * 118)
print("KONTROLL A — kui suur on BRUTO-POSITSIOON? (CFD-l maksab iga hoitud euro intressi)")
print("=" * 118)
w = rp(px, rets)
gross = w.abs().sum(axis=1)
print(f"  keskmine bruto-eksponeeritus: {gross.mean():.2f}x kapitalist")
print(f"  mediaan: {gross.median():.2f}x    90. protsentiil: {gross.quantile(0.9):.2f}x    max: {gross.max():.2f}x")

print()
print("=" * 118)
print("KONTROLL B — SAMA STRATEEGIA, AGA OONE FINANTSEERIMISTASUGA (swap)")
print("=" * 118)
for fin in (0.0, 0.02, 0.04, 0.06):
    net = (w.shift(1) * rets).sum(axis=1)
    turn = (w - w.shift(1)).abs().fillna(0.0)
    cb = pd.Series({c: R.COST_BP.get(c, 3.0) for c in rets.columns}) / 10000.0
    net = net - (turn * cb).sum(axis=1) - gross.shift(1).fillna(0) * fin / 252.0
    eq = (1 + net).cumprod(); yrs = len(net) / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    dd = (eq / eq.cummax() - 1).min()
    sh = net.mean() / net.std() * np.sqrt(252)
    print(f"  finantseerimine {100*fin:4.1f}%/a  ->  CAGR {100*cagr:+6.1f}%   Sharpe {sh:5.2f}   maxDD {100*dd:6.1f}%")

print()
print("=" * 118)
print("KONTROLL C — ILMA KRUPTOTA (kas BTC/ETH veab kogu tulemust?)")
print("=" * 118)
for excl, lbl in [([], "koik 21"),
                  (["BTCUSD","ETHUSD"], "ilma kruptota (19)"),
                  (["BTCUSD","ETHUSD","NAS100","SPX","GER40","JP225","UK100"], "ilma krupto+aktsiateta (14)")]:
    syms = [s for s in px.columns if s not in excl]
    p2 = px[syms]; r2 = R.returns(p2)
    R.show(R.evaluate(rp(p2, r2), r2, label=f"  RP {lbl}"))

print()
print("=" * 118)
print("KONTROLL D — ALAMPERIOODID (kas tulemus on stabiilne ajas?)")
print("=" * 118)
cuts = [("2016-09-12","2019-09-11"), ("2019-09-12","2022-09-11"),
        ("2022-09-12","2026-09-11"), ("2021-01-01","2023-12-31")]
for a, b in cuts:
    m = (px.index >= a) & (px.index <= b)
    p2 = px[m]; r2 = R.returns(p2)
    R.show(R.evaluate(rp(p2, r2), r2, label=f"  RP {a[:7]} .. {b[:7]}"))

print()
print("=" * 118)
print("KONTROLL E — AASTATE KAUPA (kus on valu?)")
print("=" * 118)
res = R.evaluate(rp(px, rets), rets, label="RP")
for y, v in res["yearly"].items():
    bar = "#" * max(0, int(abs(v) * 60))
    print(f"  {y}  {100*v:+7.1f}%  {'-' if v < 0 else '+'}{bar}")
