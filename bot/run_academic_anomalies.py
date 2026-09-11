"""
Kolm akadeemiliselt dokumenteeritud, seni testimata anomaaliat:
  1. Luhiajaline poordumine parast aarmuslikku uhepaevast liikumist
     (short-term reversal, Jegadeesh 1990)
  2. Kuuvahetuse efekt (turn-of-month, Ariel 1987)
  3. Esmaspaeva lunga sulgumine FX-is (nadalavahetuse ule-reaktsioon)

Sama range kontroll, mis kogu sessiooni jooksul: paris kulud
(spread+finantseerimine), parameetri-tundlikkus, kahepoolne test.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

MK = 0.030

def cost_full(w, sym, spread_bp):
    """w ja tagastus on PUHTAD Series'id (mitte DataFrame'id) - varasem
    .to_frame() moepakkimine tekitas DataFrame*Series joondusvea (jooniti
    veergude, mitte ridade jargi), mis andis vaikimisi kulud=0 KOGU
    real'is. Parandatud: kasutame labivalt Series'eid."""
    turn = (w - w.shift(1)).abs().fillna(0.0)
    sp = turn * spread_bp / 10000.0
    rate = R.load_rates(w.index).reindex(w.index).ffill()
    fin = w.shift(1).clip(lower=0) * rate / 252.0   # ainult pikk maksab intressi
    fin = fin + w.shift(1).abs() * MK / 252.0        # juurdehindlus mollel suunal
    return sp.fillna(0.0), fin.fillna(0.0)

print("=" * 108)
print("1) LÜHIAJALINE PÖÖRDUMINE PÄRAST ÄÄRMUSLIKKU ÜHEPÄEVAST LIIKUMIST")
print("=" * 108)
print("   Idee: kui hind liigub ühe päevaga > K standardhälvet, siis järgmine päev")
print("   kaldub OSALISELT tagasi pöörduma (üleliigne reaktsioon parandub).\n")

for K in (1.5, 2.0, 2.5, 3.0):
    results = []
    for sym in sorted(R.COST_BP):
        p = os.path.join(R.DATA, f"{sym}_d.csv")
        if not os.path.exists(p): continue
        d = load(sym)
        r = d["close"].pct_change()
        vol = r.rolling(20).std()
        z = r / vol
        sig = -np.sign(r) * (z.abs() > K)   # fade eilset liikumist
        w = sig.shift(1).fillna(0.0)   # sisene jargmisel paeval
        fwd = r.shift(-1) * 0  # pole vaja, kasutame otse r't jargmisel paeval position-weighted
        strat_ret = w * r  # w on juba nihutatud, r on TANANE tootlus
        sp, fin = cost_full(w, sym, R.COST_BP[sym])
        net = strat_ret - sp - fin
        n_trades = (w != 0).sum()
        if n_trades < 20: continue
        eq = (1+net.fillna(0)).cumprod()
        yrs = len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
        sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
        results.append((sym, n_trades, cagr, sh))
    avg_sh = np.mean([r[3] for r in results]) if results else 0
    pos = sum(1 for r in results if r[2]>0)
    print(f"  K={K:.1f}std:  {len(results):2d} instrumenti testitud, {pos} positiivse CAGR-iga, "
          f"keskm Sharpe {avg_sh:+.2f}")

print("\n  Detailid K=2.0 juures:")
K = 2.0
for sym in sorted(R.COST_BP):
    p = os.path.join(R.DATA, f"{sym}_d.csv")
    if not os.path.exists(p): continue
    d = load(sym)
    r = d["close"].pct_change()
    vol = r.rolling(20).std()
    z = r / vol
    sig = -np.sign(r) * (z.abs() > K)
    w = sig.shift(1).fillna(0.0)
    sp, fin = cost_full(w, sym, R.COST_BP[sym])
    net = w*r - sp - fin
    n = (w!=0).sum()
    if n < 20: continue
    eq = (1+net.fillna(0)).cumprod(); yrs=len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
    print(f"    {sym:8s} n={n:4d}  CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}")

print()
print("=" * 108)
print("1b) SPX/NAS100 ROBUSTSUSKONTROLL — kas silmapaistvad tulemused on stabiilsed?")
print("=" * 108)
for sym in ("SPX", "NAS100"):
    d = load(sym); r = d["close"].pct_change()
    print(f"\n  {sym} — K-tundlikkus:")
    for K in (1.0, 1.5, 2.0, 2.5, 3.0, 3.5):
        vol = r.rolling(20).std(); z = r/vol
        sig = -np.sign(r) * (z.abs() > K)
        w = sig.shift(1).fillna(0.0)
        sp, fin = cost_full(w, sym, R.COST_BP[sym])
        net = w*r - sp - fin
        n = int((w!=0).sum())
        if n < 15: print(f"    K={K:.1f}  liiga vähe tehinguid ({n})"); continue
        eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
        sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
        print(f"    K={K:.1f}  n={n:4d}  CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}")

    K = 2.0
    vol = r.rolling(20).std(); z = r/vol
    sig = -np.sign(r) * (z.abs() > K)
    w = sig.shift(1).fillna(0.0)
    mid = len(d)//2
    print(f"  {sym} K=2.0 pooleks jagatud:")
    for lbl, sl in [("1. pool", slice(0,mid)), ("2. pool", slice(mid,None))]:
        w2, r2 = w.iloc[sl], r.iloc[sl]
        sp, fin = cost_full(w2, sym, R.COST_BP[sym])
        net = w2*r2 - sp - fin
        n = int((w2!=0).sum())
        eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
        print(f"    {lbl} ({r2.index[0].date()}..{r2.index[-1].date()}): n={n:3d}  CAGR {100*cagr:+6.1f}%")

print()
print("=" * 108)
print("2) KUUVAHETUSE EFEKT (turn-of-month, Ariel 1987)")
print("=" * 108)
print("   Idee: aktsiaindeksite tootlus koondub kuu VIIMASELE + esimesele N")
print("   kauplemispaevale. Osta ainult neil paevadel, muidu ole valjas.\n")

for sym in ("SPX", "NAS100", "GER40", "JP225", "UK100"):
    d = load(sym); r = d["close"].pct_change()
    trading_days = d.index
    # leia iga kuu viimane kauplemispaev
    month_end = pd.Series(trading_days, index=trading_days).groupby(
        trading_days.to_period("M")).transform("max")
    for N in (1, 2, 3, 4):
        is_tom = pd.Series(False, index=trading_days)
        me_dates = sorted(set(month_end))
        for me in me_dates:
            pos = trading_days.get_loc(me)
            for k in range(-(N-1), N+1):  # N-1 paeva enne kuulopu, N paeva parast
                idx = pos + k
                if 0 <= idx < len(trading_days):
                    is_tom.iloc[idx] = True
        w = is_tom.astype(float).shift(1).fillna(0.0)
        sp, fin = cost_full(w, sym, R.COST_BP[sym])
        net = w*r - sp - fin
        n_days = int(is_tom.sum())
        eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
        cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
        sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
        # vordlus: koik paevad (osta-ja-hoia)
        bh = (1+r.fillna(0)).cumprod(); bh_cagr = bh.iloc[-1]**(1/yrs)-1
        print(f"  {sym:8s} N={N}  ({100*n_days/len(trading_days):4.1f}% ajast turul)  "
              f"CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}   (v6rdluseks osta-hoia {100*bh_cagr:+6.1f}%)")
    print()
