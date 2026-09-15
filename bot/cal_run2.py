"""
cal_run2.py — B1 null-test, H1 (intraday) test, kontsentratsioon, falsifitseerimine.
"""
import math

import numpy as np
import pandas as pd

import cal_engine as C
import cal_run as R
import h1engine as H

d, V = R.ehita()
x = d[d["z"].abs() >= C.LAVI].copy()
KULU = R.KULU

print("=" * 104)
print("B1.9  PERMUTATION NULL — kas paris ullatus voidab juhusliku margistamise?")
print("=" * 104)
rs = np.random.RandomState(20260915)
r1 = (x["suund"] * x["r1"]).dropna()
tegelik = 1e4 * r1.mean()
suunad = x["suund"].values
rr = x["r1"].values
ok = np.isfinite(rr)
rr_ok = rr[ok]
n_perm = 500
# (a) juhuslik MARK: sama sundmuste hulk, sama hinnaseeria, suund juhuslik
a = np.array([1e4 * (rs.choice([-1.0, 1.0], size=len(rr_ok)) * rr_ok).mean()
              for _ in range(n_perm)])
# (b) SEGATUD ullatus: suunad segatakse sundmuste vahel (sagedus sailib)
s_ok = suunad[ok]
b = np.array([1e4 * (rs.permutation(s_ok) * rr_ok).mean() for _ in range(n_perm)])
print(f"  tegelik keskmine: {tegelik:+.3f} bp   (n = {len(rr_ok)})")
for nimi, arr in (("(a) juhuslik mark", a), ("(b) segatud ullatus", b)):
    print(f"  {nimi:<22s} mediaan {np.median(arr):+.3f}  "
          f"95% {np.quantile(arr,0.95):+.3f}  max {arr.max():+.3f}  "
          f"=> p = {float((arr >= tegelik).mean()):.4f}")

print()
print("=" * 104)
print("B1.10  H1 (INTRADAY) TEST — luhike valim, aga see on koht kus efekt peaks olema")
print("=" * 104)
PAARID = {"EUR": ("EURUSD", False), "GBP": ("GBPUSD", False),
          "AUD": ("AUDUSD", False), "NZD": ("NZDUSD", False),
          "JPY": ("USDJPY", True), "CHF": ("USDCHF", True),
          "CAD": ("USDCAD", True)}
h = {}
for c, (sym, inv) in PAARID.items():
    s = H.lae(sym)
    if s is None:
        continue
    h[c] = (1.0 / s["close"]) if inv else s["close"]
ix = None
for s in h.values():
    ix = s.index if ix is None else ix.intersection(s.index)
HV = pd.DataFrame({c: s.reindex(ix) for c, s in h.items()})
HV["USD"] = 1.0
HV = HV[C.VALUUTAD].dropna()
print(f"  H1 aken: {HV.index.min()} .. {HV.index.max()}  {len(HV)} baari")

dh = C.z_ullatus(C.lae_kalender())
hp = C.h1_sisenemine(dh["ts"].values, HV.index)
dh = dh.assign(bar=hp)
dh = dh[(dh["bar"] >= 0) & dh["z"].notna()].copy()
dh["suund"] = np.sign(dh["z"]) * dh["mark"]
LOG = np.log(HV)
for k in (1, 4, 24):
    rk = LOG.diff(k).shift(-k)
    rk = rk.sub(rk.mean(axis=1), axis=0)
    dh[f"h{k}"] = [rk.iloc[b][c] if b < len(rk) else np.nan
                   for b, c in zip(dh["bar"].values, dh["cur"].values)]
xh = dh[dh["z"].abs() >= C.LAVI]
print(f"  sundmusi H1 aknas: {len(dh)}, neist |z|>=1: {len(xh)}")
print(R.pais())
for k in (1, 4, 24):
    print(R.rida(C.moodikud((xh["suund"] * xh[f"h{k}"]).dropna()),
                 f"koik |z|>=1  +{k}h", KULU))
    t1 = xh[xh["tier"] == "T1"]
    print(R.rida(C.moodikud((t1["suund"] * t1[f"h{k}"]).dropna()),
                 f"  TIER 1       +{k}h", KULU))

print()
print("=" * 104)
print("B1.11  TIER 1 ERALDI (eelregistreeritud prioriteet, mitte tagantjarele valik)")
print("=" * 104)
print(R.pais())
t1 = x[x["tier"] == "T1"]
for k in R.HOR_D:
    print(R.rida(C.moodikud((t1["suund"] * t1[f"r{k}"]).dropna()),
                 f"TIER 1  {k}d", KULU))
tr, va, oos = C.jaota(t1["ts"])
for nimi, m in (("TRAIN", tr), ("VALID", va), ("FINAL OOS", oos)):
    print(R.rida(C.moodikud((t1[m]["suund"] * t1[m]["r1"]).dropna()),
                 f"TIER 1  1d {nimi}", KULU))
print()
print(f"{'aasta':<8s}{'n':>7s}{'bruto_bp':>10s}{'neto_bp':>9s}{'t':>7s}")
pg = pn = 0
aastad = sorted(t1["ts"].dt.year.unique())
for y in aastad:
    xx = t1[t1["ts"].dt.year == y]
    m = C.moodikud((xx["suund"] * xx["r1"]).dropna())
    if m is None:
        continue
    pg += m["keskm_bp"] > 0
    pn += (m["keskm_bp"] - KULU) > 0
    print(f"{y:<8d}{m['n']:>7d}{m['keskm_bp']:>10.2f}"
          f"{m['keskm_bp']-KULU:>9.2f}{m['t']:>7.2f}")
print(f"\nTIER 1: bruto positiivseid aastaid {pg}/{len(aastad)}, "
      f"neto positiivseid {pn}/{len(aastad)}")

print()
print("=" * 104)
print("B1.12  KONTSENTRATSIOON — suurim kasumi- ja kahjumiallikas (1d, |z|>=1)")
print("=" * 104)
x = x.assign(pnl=(x["suund"] * x["r1"]))
xx = x.dropna(subset=["pnl"])
kokku = xx["pnl"].sum()
print(f"  kogu bruto logsumma {100*kokku:+.2f}%  ({len(xx)} sundmust)")
for veerg, silt in (("cur", "VALUUTA"), ("indicator", "INDIKAATOR"),
                    ("tier", "TIER")):
    g = xx.groupby(veerg)["pnl"].sum().sort_values(ascending=False)
    print(f"\n  {silt}:")
    print(f"    parim   {g.index[0]:<32s} {100*g.iloc[0]:+7.2f}% = "
          f"{100*g.iloc[0]/kokku:6.1f}% kogusummast")
    print(f"    halvim  {g.index[-1]:<32s} {100*g.iloc[-1]:+7.2f}%")
    print(f"    positiivseid {int((g > 0).sum())}/{len(g)}  "
          f"mediaan {100*g.median():+.2f}%")
g = xx.groupby(xx["ts"].dt.year)["pnl"].sum().sort_values(ascending=False)
print(f"\n  AASTA: parim {g.index[0]} {100*g.iloc[0]:+.2f}% = "
      f"{100*g.iloc[0]/kokku:.1f}% kogusummast; "
      f"halvim {g.index[-1]} {100*g.iloc[-1]:+.2f}%")

print()
print("=" * 104)
print("B1.13  FALSIFITSEERIMINE — kas see on sama lugu mis COT (uus periood = kogu efekt)?")
print("=" * 104)
print(R.pais())
for nimi, a, b in (("2013-2016", "2013-01-01", "2016-12-31"),
                   ("2017-2020", "2017-01-01", "2020-12-31"),
                   ("2021-2026", "2021-01-01", "2026-12-31")):
    m = (x["ts"] >= pd.Timestamp(a)) & (x["ts"] <= pd.Timestamp(b))
    print(R.rida(C.moodikud(x[m]["pnl"].dropna()), f"koik {nimi}", KULU))
    mt = m & (x["tier"] == "T1")
    print(R.rida(C.moodikud(x[mt]["pnl"].dropna()), f"  TIER 1 {nimi}", KULU))
