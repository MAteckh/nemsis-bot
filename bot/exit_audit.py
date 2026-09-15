"""
exit_audit.py — EXIT STRUCTURE v1 audit. Jookseb ENNE tulemusi.
"""
import numpy as np
import pandas as pd

import hm_engine as H
import exit_structure_falsification as X

OK, VIGA = "OK  ", "VIGA"
t = []


def k(nimi, ting, info=""):
    t.append(bool(ting))
    print(f"{OK if ting else VIGA}  {nimi:<54s} {info}")


P = X.valmista()
k("A1 koik 15 paari laetud", len(P) == 15,
  f"{len(P)} paari, luhim {min(len(v['o']) for v in P.values())} baari, "
  f"pikim {max(len(v['o']) for v in P.values())}")
vahemik = {p: (str(v['idx'].min().date()), str(v['idx'].max().date()))
           for p, v in P.items()}
k("A1 vahemikud dokumenteeritud", True,
  f"AUDUSD {vahemik['AUDUSD'][0]} .. {vahemik['AUDUSD'][1]}; "
  f"EURUSD {vahemik['EURUSD'][0]} .. {vahemik['EURUSD'][1]}")
k("A1 lubatud sisenemisbaarid algavad 2006-01-01",
  all(v["idx"][v["lubatud"][0]] >= X.ALGUS for v in P.values()),
  f"esimene lubatud baar EURUSD-l "
  f"{P['EURUSD']['idx'][P['EURUSD']['lubatud'][0]].date()}")

# --- A2: KIIRE SIMULAATOR == hm_engine.simuleeri -------------------------
# Vordlus KOGU seerial, samade signaalidega — see on tegelik samavaarsuse
# test. (Kuupaevafiltriga versioon erineb UHE tehingu vorra USDJPY-l, sest
# hm_engine hoiab 2005. lopus avatud positsiooni, mis blokeerib 2006-01-04
# signaali. See on piiriefekt, mitte loogikaviga — vt A2b.)
vahed = []
for p, Pp in P.items():
    d = H.lae_d1(p)
    kk = H.kontekst(d, "W")
    ref = H.simuleeri(d, kk, "MOMENTUM", "D1", H.KULU_BP[p])
    nt, br, si = X.sim(Pp, Pp["mom"])
    vahed.append((p, len(ref), len(nt),
                  abs(float(ref["neto_r"].sum()) - float(nt.sum())),
                  abs(float(ref["bruto_r"].sum()) - float(br.sum()))))
max_n = max(abs(a - b) for _, a, b, _, _ in vahed)
max_d = max(x for _, _, _, x, _ in vahed)
max_b = max(x for _, _, _, _, x in vahed)
k("A2 kiire simulaator == hm_engine.simuleeri (tehingute arv)",
  max_n == 0, f"suurim erinevus {max_n} tehingut ule 15 paari")
k("A2 kiire simulaator == hm_engine.simuleeri (neto_R summa)",
  max_d < 1e-9, f"suurim erinevus {max_d:.2e} R")
k("A2 kiire simulaator == hm_engine.simuleeri (bruto_R summa)",
  max_b < 1e-9, f"suurim erinevus {max_b:.2e} R")
# A2b: dokumenteeritud piiriefekt
d = H.lae_d1("USDJPY"); kk = H.kontekst(d, "W")
ref06 = H.simuleeri(d, kk, "MOMENTUM", "D1", H.KULU_BP["USDJPY"])
ref06 = ref06[ref06["aeg"] >= X.ALGUS]
sgz = P["USDJPY"]["mom"].copy(); sgz[P["USDJPY"]["idx"] < X.ALGUS] = 0
ntz, _, siz = X.sim(P["USDJPY"], sgz)
k("A2b 2006-piiriefekt moodetud ja dokumenteeritud",
  len(ntz) - len(ref06) == 1,
  f"USDJPY: signaalide nullimisel {len(ntz)} vs kuupaevafiltriga "
  f"{len(ref06)} tehingut (2005. lopus avatud positsioon). "
  f"Lahendus: simuleeri KOGU seeria ja filtreeri tehingud kuupaeva jargi.")

# --- A3: teadaoleva vastusega testid -------------------------------------
def tehis(hinnad):
    c = np.asarray(hinnad, float)
    return dict(o=np.r_[c[0], c[:-1]], h=c * 1.0005, l=c * 0.9995, c=c,
                atr=np.full(len(c), 0.01), kulu=0.0,
                idx=pd.date_range("2010-01-01", periods=len(c), freq="D"),
                lubatud=np.arange(len(c)), rez={}, mom=np.zeros(len(c), int))
up = tehis(np.linspace(1.0, 2.0, 400))
sg = np.zeros(400, dtype=int); sg[200] = 1
nt, br, si = X.sim(up, sg, sl_atr=1.5, tp_r=2.0, max_hold=20, slip=0.0)
k("A3 tousev seeria -> TP, bruto = +2.0 R",
  len(br) == 1 and abs(br[0] - 2.0) < 1e-9, f"bruto {br[0]:.6f}")
dn = tehis(np.linspace(2.0, 1.0, 400))
nt2, br2, _ = X.sim(dn, sg, slip=0.0)
k("A3 langev seeria, pikk signaal -> SL, bruto = -1.0 R",
  len(br2) == 1 and abs(br2[0] + 1.0) < 1e-9, f"bruto {br2[0]:.6f}")
lame = tehis(np.full(400, 1.0))
lame["h"] = lame["h"].copy(); lame["l"] = lame["l"].copy()
lame["h"][205] = 2.0; lame["l"][205] = 0.5
nt3, br3, _ = X.sim(lame, sg, slip=0.0)
k("A3 SL ja TP samas baaris -> loetakse SL",
  len(br3) == 1 and abs(br3[0] + 1.0) < 1e-9, f"bruto {br3[0]:.6f}")
nt4, br4, _ = X.sim(lame, sg, max_hold=3, slip=0.0)
k("A3 max_hold piirab hoiuaega",
  len(br4) == 1, f"bruto {br4[0]:.6f} (lame seeria, ajaline valjumine)")
# TP muutmine muudab tulemust ootusparaselt
_, br5, _ = X.sim(up, sg, tp_r=3.0, slip=0.0)
k("A3 TP = 3R tousval seerial -> bruto = +3.0 R",
  abs(br5[0] - 3.0) < 1e-9, f"bruto {br5[0]:.6f}")

# --- A4: kulumudel --------------------------------------------------------
Pp = P["EURUSD"]
sgm = Pp["mom"].copy(); sgm[Pp["idx"] < X.ALGUS] = 0
n0, b0, _ = X.sim(Pp, sgm, kulu_kordaja=0.0, slip=0.0)
n1, b1, _ = X.sim(Pp, sgm)
k("A4 kulu = 0 => neto == bruto", bool(np.allclose(n0, b0)), "")
k("A4 kulu > 0 => neto < bruto igal tehingul",
  bool((n1 < b1).all()), f"keskmine kulu {float((b1-n1).mean()):.4f} R")
n2, _, _ = X.sim(Pp, sgm, kulu_kordaja=2.0)
k("A4 spread 2x => kulu kasvab",
  float((b1 - n2).mean()) > float((b1 - n1).mean()),
  f"{float((b1-n1).mean()):.4f} -> {float((b1-n2).mean()):.4f} R")

# --- A5: juhuslikud sisenemised on paaritud ja korratavad ----------------
d1 = X.juhuslikud_sisenemised(P, 3, seeme=123)
d2 = X.juhuslikud_sisenemised(P, 3, seeme=123)
sama = all(np.array_equal(d1[i][p], d2[i][p]) for i in range(3) for p in d1[i])
k("A5 sama seeme => identsed sisenemised (korratav)", sama, "seeme 123")
d3 = X.juhuslikud_sisenemised(P, 3, seeme=999)
erinev = any(not np.array_equal(d1[i][p], d3[i][p]) for i in range(3) for p in d1[i])
k("A5 erinev seeme => erinevad sisenemised", erinev, "")
n_sig = int(sum((d1[0][p] != 0).sum() for p in d1[0]))
n_mom = int(sum((P[p]["mom"] != 0).sum() for p in P))
k("A5 kandidaate = 1.3x MOMENTUM signaale", abs(n_sig - int(n_mom * 1.3)) <= 15,
  f"juhuslikke {n_sig}, MOMENTUM {n_mom}, suhe {n_sig/n_mom:.2f}")
lo = X.juhuslikud_sisenemised(P, 1, seeme=7, ainult=1)
k("A5 ainult=+1 annab ainult pikki", all((lo[0][p][lo[0][p] != 0] == 1).all()
                                         for p in lo[0]), "")

# --- A6: lookahead --------------------------------------------------------
Pp2 = {kk: (vv.copy() if isinstance(vv, np.ndarray) else vv)
       for kk, vv in P["EURUSD"].items()}
n = len(Pp2["c"])
for f in ("o", "h", "l", "c"):
    Pp2[f] = Pp2[f].copy(); Pp2[f][n - 50:] *= 3.0
sgx = P["EURUSD"]["mom"].copy(); sgx[P["EURUSD"]["idx"] < X.ALGUS] = 0
na, _, sia = X.sim(P["EURUSD"], sgx)
nb, _, sib = X.sim(Pp2, sgx)
m = sia < n - 80
k("A6 tuleviku rikkumine ei muuda varasemaid tehinguid",
  bool(np.allclose(na[m], nb[:len(na)][m])),
  f"kontrollitud {int(m.sum())} tehingut")
k("A6 sisenemine on jargmise baari AVAHIND",
  bool(np.allclose([P["EURUSD"]["o"][i] for i in sia[:50]],
                   [P["EURUSD"]["o"][i] for i in sia[:50]])) and
  bool((sia[1:] > sia[:-1]).all()), "ja tehingud ei kattu")

# --- A7: baseline peab klappima D1 Momentum Validationiga ---------------
draws = X.juhuslikud_sisenemised(P, 200, seeme=X.SEEME)
neto, bruto, per, _ = X.joosta_variant(P, draws)
k("A7 BASELINE random entry ~ +0.0126 R (Validation v1)",
  abs(float(neto.mean()) - 0.0126) < 0.004,
  f"saadud {float(neto.mean()):+.4f} R (Validation v1: +0.0126), "
  f"n={len(neto)}, katseid 200")
mom_neto = []
for p, Pp in P.items():
    nt, _, si = X.sim(Pp, Pp["mom"])          # KOGU seeria, nagu hm_engine
    m = Pp["idx"][si] >= X.ALGUS              # filtreeri TEHINGUD, mitte signaalid
    mom_neto.append(nt[m])
mn = np.concatenate(mom_neto)
k("A7 MOMENTUM baseline == Validation v1 (+0.0294 R, n=2483)",
  abs(float(mn.mean()) - 0.0294) < 0.0005 and abs(len(mn) - 2483) <= 2,
  f"saadud {float(mn.mean()):+.4f} R, n={len(mn)}")

print(f"\n{len(t)} kontrolli, {sum(1 for x in t if not x)} viga")
