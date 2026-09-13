"""
cot_audit.py — kontrollid ENNE tulemuste uskumist.

A1 andmete terviklikkus
A2 avaldamisajastus: sisenemine on alati >= report_date + 6 paeva
A3 rullpertsentiil ei kasuta tulevikku (sunteetiline test)
A4 sunteetiline rist vs PARIS EURJPY seeria
A5 portfellimootor: teadaoleva signaaliga peab andma teadaoleva tulemuse
A6 kulu rakendub: 0bp bruto == neto
"""
import numpy as np
import pandas as pd

import cot_engine as E

OK = "OK  "
VIGA = "VIGA"
tulem = []


def kontroll(nimi, tingimus, info=""):
    tulem.append((OK if tingimus else VIGA, nimi, info))
    print(f"{OK if tingimus else VIGA}  {nimi:<46s} {info}")
    return tingimus


# ---------------------------------------------------------------- A1 ------
d = E.lae_cot()
N = E.net_pct_tabel(d)
kontroll("A1 COT ridu", len(d) == 12160, f"{len(d)} rida, {d['cur'].nunique()} valuutat")
kontroll("A1 vahemik", str(d["date"].min().date()) == "2000-01-04",
         f"{d['date'].min().date()} .. {d['date'].max().date()}")
kontroll("A1 net_pct vahemikus [-1,1]",
         bool(d["net_pct"].abs().max() <= 1.0), f"max|net_pct|={d['net_pct'].abs().max():.3f}")
puudu = N.isna().sum()
kontroll("A1 puuduvad vaatlused loendatud", True,
         ", ".join(f"{c}:{int(puudu[c])}" for c in N.columns))

# ---------------------------------------------------------------- A2 ------
V = E.usd_vaartused()
sis = E.sisenemispaevad(N.index, V.index)
vahe = pd.Series({k: (v - k).days for k, v in sis.items()})
kontroll("A2 sisenemine >= report+6 paeva", bool(vahe.min() >= E.VIIVE_PAEVI),
         f"min={vahe.min()}d  mediaan={int(vahe.median())}d  max={vahe.max()}d")
esm = pd.DatetimeIndex(sis.values).dayofweek
kontroll("A2 sisenemispaev on E/T (nadala algus)", bool((esm <= 1).mean() > 0.95),
         f"esmaspaev {100*(esm==0).mean():.1f}%  teisipaev {100*(esm==1).mean():.1f}%")

# ---------------------------------------------------------------- A3 ------
# sunteetiline: 0..299 kasvav. Viimane vaatlus on alati suurim => pertsentiil 1.0
s = pd.Series(np.arange(300.0))
p = E.rull_pertsentiil(s, aken=52)
kontroll("A3 kasvav seeria -> pertsentiil 1.0", bool(np.nanmax(p) == 1.0 and np.nanmin(p[51:]) == 1.0),
         f"min={np.nanmin(p[51:]):.2f} max={np.nanmax(p):.2f}")
# kahanev => 0.0
p2 = E.rull_pertsentiil(pd.Series(np.arange(300.0)[::-1]), aken=52)
kontroll("A3 kahanev seeria -> pertsentiil 0.0", bool(np.nanmax(p2[51:]) == 0.0), "")
# tulevik ei mojuta: muuda ainult viimast vaatlust, varasemad pertsentiilid samad
s3 = pd.Series(np.random.RandomState(1).randn(300))
a = E.rull_pertsentiil(s3, aken=52)
s4 = s3.copy(); s4.iloc[-1] = 999.0
b = E.rull_pertsentiil(s4, aken=52)
kontroll("A3 tuleviku muutmine ei muuda minevikku",
         bool((a.iloc[:-1].fillna(-1) == b.iloc[:-1].fillna(-1)).all()), "")
# min_periods: enne akna taitumist NaN
kontroll("A3 warmup NaN kuni aken taidetud", bool(a.iloc[:51].isna().all()), "")

# ---------------------------------------------------------------- A4 ------
rist = E.paari_hind(V, "EURJPY")
paris = E.lae_hind("EURJPY")
ix = rist.index.intersection(paris.index)
suht = (rist.reindex(ix) / paris.reindex(ix) - 1).abs()
korr = np.corrcoef(np.log(rist.reindex(ix)).diff().dropna(),
                   np.log(paris.reindex(ix)).diff().dropna())[0, 1]
kontroll("A4 sunteetiline EURJPY ~ paris EURJPY",
         bool(suht.median() < 0.002 and korr > 0.99),
         f"mediaan hinnaviga {100*suht.median():.3f}%  tootluse korr {korr:.4f}")

# ---------------------------------------------------------------- A5 ------
# teadaolev vastus: hind touseb iga nadal tapselt +1%, signaal alati +1
ix2 = pd.date_range("2018-01-01", periods=60, freq="7D")
H = pd.DataFrame({"EURUSD": 1.0 * (1.01 ** np.arange(60))}, index=ix2)
W = pd.DataFrame({"EURUSD": np.ones(60)}, index=ix2)
r = E.portfell(W, H, 0.0)
kontroll("A5 +1%/nadal, kaal +1 -> keskm log-tootlus 0.00995",
         bool(abs(r["bruto"].mean() - np.log(1.01)) < 1e-9),
         f"saadud {r['bruto'].mean():.8f}, oodatud {np.log(1.01):.8f}")
Wn = -W
rn = E.portfell(Wn, H, 0.0)
kontroll("A5 kaalu margi pooramine pooral tootluse",
         bool(abs(rn["bruto"].mean() + r["bruto"].mean()) < 1e-12), "")

# ---------------------------------------------------------------- A6 ------
r0 = E.portfell(W, H, 0.0)
kontroll("A6 0bp: neto == bruto", bool((r0["neto"] == r0["bruto"]).all()), "")
# turnover: kaal hupab +1 -> -1 iga nadal => |dw| = 2 => kulu = 2 * bp
Wv = pd.DataFrame({"EURUSD": np.where(np.arange(60) % 2 == 0, 1.0, -1.0)}, index=ix2)
r1 = E.portfell(Wv, H, 1.0)
kontroll("A6 1bp, |dw|=2 -> kulu 2bp nadalas",
         bool(abs(r1["kulu"].iloc[1:].mean() - 2e-4) < 1e-12),
         f"saadud {1e4*r1['kulu'].iloc[1:].mean():.4f} bp")

# ---------------------------------------------------------------- A7 ------
# sisenemispaeva nihe: kui viive on 6 paeva, siis reede-release on juba moodas
rd = pd.Timestamp("2024-03-05")           # teisipaev
kontroll("A7 teisipaeva aruanne -> esmaspaev (+6d)",
         bool((E.sisenemispaevad(pd.DatetimeIndex([rd]), V.index)[rd]
               - rd).days >= 6),
         str(E.sisenemispaevad(pd.DatetimeIndex([rd]), V.index)[rd].date()))

vigu = sum(1 for t in tulem if t[0] == VIGA)
print(f"\n{len(tulem)} kontrolli, {vigu} viga")
