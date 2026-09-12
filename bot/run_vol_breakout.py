"""
MUSTER 2 (PARANDATUD: ATR nihutatud, vaata allpool): VOLATIILSUS ON ENNUSTATAV — kas sellest saab raha?

Suund ei ole ennustatav (3.9% seletusvoime). AGA volatiilsus on:
suured paevad tulevad kobaras. Seda teab iga rahandusinimene.

Kusimus: kas sellest saab raha ILMA optsioonideta?
Ainus viis: BREAKOUT-STRADDLE. Pane ostu-stopp ulespoole ja
muugi-stopp allapoole. Kui tuleb suur liikumine, tabab uks neist ja
soidad kaasa. Kui ei tule, kaotad spread'i.

See EI NOUA suuna ennustamist — ainult liikumise SUURUSE ennustamist.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

SYMS = ["SPX","NAS100","GER40","JP225","XAUUSD","XAGUSD","WTI","BTCUSD","ETHUSD","COPPER"]

def load(s):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

print("=" * 100)
print("1) KUI HÄSTI ON VOLATIILSUS ENNUSTATAV? (vs suund)")
print("=" * 100)
print(f"  {'sümbol':9s} {'suuna ennustatavus':>20s} {'VOLATIILSUSE ennustatavus':>28s}")
print("  " + "-" * 60)
for s in SYMS:
    d = load(s)
    if d is None: continue
    r = (d["Close"]/d["Close"].shift(1)-1).dropna()
    # suund: eilne tootlus -> tanane tootlus
    a, b = r.shift(1).dropna(), r.loc[r.shift(1).dropna().index]
    r_dir = float(np.corrcoef(a, b)[0,1])
    # vol: eilne |tootlus| -> tanane |tootlus|
    aa, bb = r.abs().shift(1).dropna(), r.abs().loc[r.abs().shift(1).dropna().index]
    r_vol = float(np.corrcoef(aa, bb)[0,1])
    print(f"  {s:9s} {100*r_dir*r_dir:19.1f}% {100*r_vol*r_vol:27.1f}%")

print()
print("=" * 100)
print("2) BREAKOUT-STRADDLE — ostu-stopp üles, müügi-stopp alla")
print("=" * 100)
print("   Reegel: iga päev ava (eelmine Close +/- k*ATR). Kui tabab, sõida")
print("   sulgemiseni. Päevasisene => EI MINGIT finantseerimist.")
print()
print(f"  {'sümbol':9s} {'k':>5s} {'tehinguid':>10s} {'võit%':>7s} {'NETO/p':>10s} "
      f"{'CAGR':>8s} {'Sharpe':>8s} {'2.pool Sh':>10s}")
print("  " + "-" * 74)
best = []
for s in SYMS:
    d = load(s)
    if d is None or len(d) < 800: continue
    o, h, l, c = d["Open"], d["High"], d["Low"], d["Close"]
    pc = c.shift(1)
    tr = pd.concat([h-l, (h-pc).abs(), (l-pc).abs()], axis=1).max(axis=1)
    # NIHUTA: tanase ATR-i arvutamine kasutaks tanast High/Low'd = TULEVIK
    atr = tr.rolling(14).mean().shift(1)
    cost = 2*R.COST_BP.get(s, 5.0)/1e4
    for k in (0.25, 0.5, 0.75, 1.0):
        up, dn = o + k*atr, o - k*atr
        long_hit  = h >= up
        short_hit = l <= dn
        # kumb tabas esimesena — konservatiivselt: kui molemad, votame kaotuse
        ret = pd.Series(0.0, index=o.index)
        only_l = long_hit & ~short_hit
        only_s = short_hit & ~long_hit
        both   = long_hit & short_hit
        ret[only_l] = (c/up - 1)[only_l]
        ret[only_s] = (1 - c/dn)[only_s]
        ret[both]   = -(2*k*atr/o)[both]      # whipsaw: sisse ja valja molemal pool
        n = int((long_hit | short_hit).sum())
        net = (ret - (long_hit|short_hit).astype(float)*cost).fillna(0.0)
        net = net.where(net.abs() < 0.30, 0.0)
        if n < 200: continue
        eq = (1+net).cumprod(); yrs = len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
        sh = net.mean()/net.std()*np.sqrt(252) if net.std() > 0 else 0
        m = len(net)//2
        n2 = net.iloc[m:]
        sh2 = n2.mean()/n2.std()*np.sqrt(252) if n2.std() > 0 else 0
        wins = 100*float((net[net != 0] > 0).mean())
        if sh > 0.3:
            best.append((s, k, sh, sh2, cagr))
        print(f"  {s:9s} {k:5.2f} {n:10d} {wins:6.1f}% {1e4*net.mean():+9.2f}bp "
              f"{100*cagr:+7.1f}% {sh:+8.2f} {sh2:+10.2f}")

print()
print("=" * 100)
print("3) KOKKUVÕTE")
print("=" * 100)
if best:
    print("   Sharpe > 0.3 kandidaadid:")
    for s, k, sh, sh2, cg in sorted(best, key=lambda x: -x[2]):
        ok = "MÕLEMAD pooled OK" if sh2 > 0 else "2. pool NEGATIIVNE -> välja"
        print(f"     {s:9s} k={k:.2f}  Sharpe {sh:+.2f} / 2.pool {sh2:+.2f}  "
              f"CAGR {100*cg:+.1f}%  {ok}")
else:
    print("   MITTE ÜKSKI kombinatsioon ei anna Sharpe > 0.3.")
