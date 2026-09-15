"""
cal_audit.py — B1 lookahead- ja korrektsusaudit. Jookseb enne tulemusi.
"""
import numpy as np
import pandas as pd

import cal_engine as C
import h1engine as H

OK, VIGA = "OK  ", "VIGA"
tulem = []


def kontroll(nimi, tingimus, info=""):
    tulem.append(bool(tingimus))
    print(f"{OK if tingimus else VIGA}  {nimi:<52s} {info}")


d = C.lae_kalender()
z = C.z_ullatus(d)
V = C.valuuta_vaartused()

# ---------------------------------------------------------------- A1 ------
kontroll("A1 kalendri ridu", len(d) == 15673, f"{len(d)} sundmust")
kontroll("A1 8 valuutat", d["cur"].nunique() == 8,
         ", ".join(f"{k}:{v}" for k, v in d["cur"].value_counts().items()))
kontroll("A1 vahemik", str(d["ts"].min().date()) == "2013-03-05",
         f"{d['ts'].min().date()} .. {d['ts'].max().date()}")
kontroll("A1 actual ja forecast alati olemas",
         bool(d[["actual", "forecast"]].notna().all().all()), "")
kontroll("A1 koigil indikaatoritel on eelregistreeritud mark",
         bool(d["mark"].isin([-1, 1]).all()),
         f"{len(C.TIER1)} T1 + {len(C.TIER2)} T2 indikaatorit")

# ---------------------------------------------------------------- A2 ------
pos = C.paevane_sisenemine(d["ts"].values, V.index)
m = pos >= 0
sis = pd.DatetimeIndex(V.index[pos[m]]) + pd.Timedelta(hours=C.PAEVA_SULG_UTC)
vahe_h = (sis - pd.DatetimeIndex(d["ts"].values[m])) / pd.Timedelta(hours=1)
kontroll("A2 paevane sisenemine on ALATI parast teadet",
         bool(vahe_h.min() > 0),
         f"min {vahe_h.min():.1f}h  mediaan {np.median(vahe_h):.1f}h  "
         f"max {vahe_h.max():.1f}h")
kontroll("A2 sidumata sundmusi loendatud", True,
         f"{int((~m).sum())} / {len(d)} ei saanud paevabaari (nadalavahetus/aken)")

# ---------------------------------------------------------------- A3 ------
E = H.lae("EURUSD")
hpos = C.h1_sisenemine(d["ts"].values, E.index)
hm = hpos >= 0
hsis = pd.DatetimeIndex(E.index[hpos[hm]]) + pd.Timedelta(hours=1)
hvahe = (hsis - pd.DatetimeIndex(d["ts"].values[hm])) / pd.Timedelta(hours=1)
kontroll("A3 H1 sisenemine on ALATI parast teadet",
         bool(hvahe.min() > 0),
         f"min {hvahe.min():.2f}h  mediaan {np.median(hvahe):.2f}h")
kontroll("A3 H1 andmed katavad ainult luhikest akent", True,
         f"{E.index.min().date()} .. {E.index.max().date()}  "
         f"{int(hm.sum())} / {len(d)} sundmust kaetud")

# ---------------------------------------------------------------- A4 ------
# sunteetiline: viga on 0,1,2,...; z ei tohi kasutada kaesolevat ega tulevast
s = pd.DataFrame({"cur": "XXX", "indicator": "TEST",
                  "actual": np.arange(60.0), "forecast": 0.0})
zz = C.z_ullatus(s)
kontroll("A4 z: esimesed MIN_N vaatlust on NaN",
         bool(zz["z"].iloc[:C.MIN_N].isna().all()), f"MIN_N={C.MIN_N}")
s2 = s.copy()
s2.loc[59, "actual"] = 9999.0            # muuda AINULT viimast
z2 = C.z_ullatus(s2)
kontroll("A4 z: tuleviku muutmine ei muuda varasemaid z-sid",
         bool(np.allclose(zz["z"].iloc[:-1].fillna(-1),
                          z2["z"].iloc[:-1].fillna(-1))), "")
# std peab olema arvutatud AINULT eelnevatest
kasi = s["actual"].iloc[39 - C.AKEN:39].std(ddof=1)
kontroll("A4 z: std vastab kasitsi arvutatule",
         bool(abs(zz["sd"].iloc[39] - kasi) < 1e-9),
         f"mootor {zz['sd'].iloc[39]:.6f} vs kasitsi {kasi:.6f}")

# ---------------------------------------------------------------- A5 ------
nfp = d[(d["cur"] == "USD") & (d["indicator"] == "Non Farm Payrolls")]
kell = pd.DatetimeIndex(nfp["ts"]).strftime("%H:%M")
kontroll("A5 NFP avaldamisaeg on 12:30/13:30 UTC",
         bool(set(kell) <= {"12:30", "13:30"}),
         f"{len(nfp)} NFP-d, ajad: {sorted(set(kell))}")
reede = pd.DatetimeIndex(nfp["ts"]).dayofweek == 4
# 94-95% on OIGE: NFP nihkub pyhade ja 2013. a valitsuse sulgemise tottu
kontroll("A5 NFP on valdavalt reedel", bool(reede.mean() > 0.90),
         f"{100*reede.mean():.1f}% reedel (ulejaanu = pyhad, 2013 shutdown)")
# H1 volatiilsus NFP tunnil vs tavaline tund -> kinnitab ajavoondi
r = np.log(E["close"]).diff().abs()
nfp_h = pd.DatetimeIndex(nfp["ts"]).floor("h")
on_nfp = r.index.isin(nfp_h)
kontroll("A5 H1 volatiilsus NFP tunnil on kordades korgem (ajavoond OK)",
         bool(r[on_nfp].mean() > 2.0 * r[~on_nfp].mean()),
         f"NFP-tund {1e4*r[on_nfp].mean():.1f}bp vs tavaline "
         f"{1e4*r[~on_nfp].mean():.1f}bp  = "
         f"{r[on_nfp].mean()/r[~on_nfp].mean():.1f}x")

# ---------------------------------------------------------------- A6 ------
R = C.valuuta_tootlused(V, 1)
kontroll("A6 valuutatootlused on ristloikeliselt tsentreeritud",
         bool(R.sum(axis=1).abs().max() < 1e-12),
         f"max |summa| = {R.sum(axis=1).abs().max():.2e}")
kontroll("A6 USD saab sisulise tootluse (mitte null)",
         bool(R["USD"].std() > 0), f"USD sigma {1e4*R['USD'].std():.1f}bp/paev")

# ---------------------------------------------------------------- A7 ------
# teadaolev vastus: kui r_c on alati +1% ja suund alati +1, keskmine = log(1.01)
tehis = np.full(100, np.log(1.01))
mm = C.moodikud(tehis * 1.0)
kontroll("A7 moodikud: konstantne +1% -> keskm 99.50 bp",
         bool(abs(mm["keskm_bp"] - 1e4 * np.log(1.01)) < 1e-6),
         f"{mm['keskm_bp']:.2f} bp")

print(f"\n{len(tulem)} kontrolli, {sum(1 for t in tulem if not t)} viga")
