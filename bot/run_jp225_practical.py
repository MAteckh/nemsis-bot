"""
JP225 lavendi-strateegia PRAKTILINE teostatavus 200EUR kontol
+ statistiline kindlus + edasine ajaline lohestus.

Kusimused, millele see vastab:
  A) Kas 2. poole serv on ISE ajas stabiilne? (lohesta 2. pool kaheks)
  B) Kas Sharpe +1.66 on juhusest eristatav? (permutatsioonitest)
  C) MIS JUHTUB 200EUR KONTOL? Miinimum-lot + JP225 notsionaal.
     (sama mehhanism, mis muutis kulla 1.5% riski 25-49% riskiks)
  D) Kas sama efekt on GER40/UK100 peal? (risttest — kui EI, on JP225
     kas eriline voi juhus)
  E) Halvimad paevad ja seeriad
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(20260911)

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open", "High", "Low", "Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

spx = load("SPX")
THR, SPREAD_BP = 1.00, 3.0
RT = 2 * SPREAD_BP / 10000.0


def build(target_sym):
    t = load(target_sym)
    ix = t.index.intersection(spx.index)
    t, s = t.reindex(ix), spx.reindex(ix)
    y = t["Close"] / t["Open"] - 1
    y = y[y.abs() < 0.25]
    r = s["Close"] / s["Close"].shift(1) - 1
    z = (r / r.rolling(60).std()).shift(1).reindex(y.index)
    w = (np.sign(z) * (z.abs() > THR)).fillna(0.0)
    return t.reindex(y.index), y, w


def stats(w, y, rt=RT):
    net = (w * y - (w != 0).astype(float) * rt).fillna(0.0)
    n = int((w != 0).sum())
    if n == 0: return dict(n=0, cagr=0.0, sh=0.0, bp=0.0)
    eq = (1 + net).cumprod(); yrs = len(net) / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1
    sh = net.mean() / net.std() * np.sqrt(252) if net.std() > 0 else 0.0
    return dict(n=n, cagr=cagr, sh=sh, bp=1e4 * net.mean(), net=net)


jp, y, w = build("JP225")

print("=" * 100)
print("A) 2. POOLE OMA LÕHESTUS — kas hiljutine serv on ise stabiilne?")
print("=" * 100)
mid = len(y) // 2
y2, w2 = y.iloc[mid:], w.iloc[mid:]
q = len(y2) // 2
for lbl, sl in [("2021-09..2024-03", slice(0, q)), ("2024-03..2026-09", slice(q, None))]:
    s = stats(w2.iloc[sl], y2.iloc[sl])
    print(f"  {lbl} ({y2.index[sl][0].date()}..{y2.index[sl][-1].date()}):  n={s['n']:3d}  "
          f"NETO {s['bp']:+6.2f}bp/p  CAGR {100*s['cagr']:+6.1f}%  Sharpe {s['sh']:+5.2f}")

print()
print("=" * 100)
print("B) PERMUTATSIOONITEST — kas +1.66 Sharpe on juhusest eristatav? (2. pool)")
print("=" * 100)
obs = stats(w2, y2)
base = (w2 != 0).values
yv = y2.values
sgn = np.sign(w2.values)
cnt = 0
N = 5000
sims = np.empty(N)
for i in range(N):
    perm = rng.permutation(sgn)          # sama arv tehinguid, juhuslik suund
    net = perm * yv - (perm != 0).astype(float) * RT
    sd = net.std()
    sims[i] = net.mean() / sd * np.sqrt(252) if sd > 0 else 0.0
p = float((sims >= obs["sh"]).mean())
print(f"  vaadeldud Sharpe: {obs['sh']:+.2f}")
print(f"  juhuslike suundade jaotus: mediaan {np.median(sims):+.2f}, "
      f"95. protsentiil {np.percentile(sims, 95):+.2f}, max {sims.max():+.2f}")
print(f"  p-väärtus (ühepoolne, {N} permutatsiooni): {p:.4f}")
BONF = 25
print(f"  Bonferroni korrektsioon ~{BONF} testitud idee kohta: lävend p < {0.05/BONF:.4f}  "
      f"--> {'LÄBIB' if p < 0.05/BONF else 'EI LÄBI'}")

print()
print("=" * 100)
print("C) 200€ KONTO REAALSUS — miinimum-lot vs JP225 notsionaal")
print("=" * 100)
px = float(jp["Close"].iloc[-1])
usdjpy = float(load("USDJPY")["Close"].iloc[-1])
eurusd = float(load("EURUSD")["Close"].iloc[-1])
print(f"  JP225 tase: {px:,.0f}   USDJPY {usdjpy:.1f}   EURUSD {eurusd:.4f}")
intraday_sd = float(y.std())
print(f"  päevasisene (open->close) std: {100*intraday_sd:.2f}%  "
      f"= {px*intraday_sd:,.0f} indeksipunkti")
print(f"  halvim päev valimis: {100*y.min():+.2f}%   parim: {100*y.max():+.2f}%")
print()
ACC_EUR = 200.0
print(f"  {'lepingu suurus':>28s} {'min lot':>8s} {'notsionaal €':>14s} "
      f"{'1 std päev €':>14s} {'% kontost':>11s}")
print("  " + "-" * 80)
for contract, minlot, kirjeldus in [
        (1,   0.10, "1 JPY/punkt (mikro)"),
        (1,   1.00, "1 JPY/punkt, min 1 lot"),
        (10,  0.10, "10 JPY/punkt"),
        (100, 0.10, "100 JPY/punkt (tavaline CFD)"),
        (100, 1.00, "100 JPY/punkt, min 1 lot")]:
    notional_jpy = px * contract * minlot
    notional_eur = notional_jpy / usdjpy / eurusd
    move_eur = notional_eur * intraday_sd
    print(f"  {kirjeldus:>28s} {minlot:8.2f} {notional_eur:14,.0f} "
          f"{move_eur:14,.2f} {100*move_eur/ACC_EUR:10.1f}%")
print()
print("  Sihiks: 1 std päev peaks olema ~1-2% kontost (tavaline riskijuhtimine).")
print(f"  => 200€ kontol lubatud notsionaal ~{ACC_EUR*0.015/intraday_sd:,.0f}€")

print()
print("=" * 100)
print("D) RISTTEST — sama loogika teistel indeksitel (SPX signaal, |z|>1.00)")
print("=" * 100)
print(f"  {'instrument':12s} {'n':>5s} {'NETO bp/p':>11s} {'CAGR':>8s} {'Sharpe':>8s} "
      f"{'2.pool Sh':>10s}")
print("  " + "-" * 62)
for sym in ("JP225", "GER40", "UK100", "NAS100"):
    try:
        _, yy, ww = build(sym)
    except Exception as e:
        print(f"  {sym:12s}  viga: {e}"); continue
    s = stats(ww, yy)
    m = len(yy) // 2
    s2 = stats(ww.iloc[m:], yy.iloc[m:])
    print(f"  {sym:12s} {s['n']:5d} {s['bp']:+11.2f} {100*s['cagr']:+7.1f}% "
          f"{s['sh']:+8.2f} {s2['sh']:+10.2f}")

print()
print("=" * 100)
print("E) HALVIMAD PÄEVAD JA SEERIAD (2. pool, |z|>1.00)")
print("=" * 100)
net = obs["net"]
traded = net[w2 != 0]
print(f"  tehinguid: {len(traded)}   võite: {100*(traded>0).mean():.1f}%")
print(f"  halvim päev {100*traded.min():+.2f}%   parim {100*traded.max():+.2f}%")
print(f"  keskmine võit {100*traded[traded>0].mean():+.2f}%   "
      f"keskmine kaotus {100*traded[traded<0].mean():+.2f}%")
eq = (1 + net).cumprod()
dd = eq / eq.cummax() - 1
print(f"  max drawdown {100*dd.min():+.2f}%  (kestus {int((dd<0).sum())} päeva kokku)")
s_ = np.sign(traded.values)
longest = cur = 0
for v in s_:
    cur = cur + 1 if v < 0 else 0
    longest = max(longest, cur)
print(f"  pikim kaotusseeria: {longest} tehingut järjest")
print(f"  kauplemispäevi aastas: ~{len(traded)/ (len(y2)/252):.0f}")
