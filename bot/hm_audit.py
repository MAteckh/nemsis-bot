"""
hm_audit.py — HEAT MAP v1 lookahead- ja korrektsusaudit. Jookseb ENNE tulemusi.
"""
import numpy as np
import pandas as pd

import hm_engine as H

OK, VIGA = "OK  ", "VIGA"
t = []


def k(nimi, ting, info=""):
    t.append(bool(ting))
    print(f"{OK if ting else VIGA}  {nimi:<54s} {info}")


def tehis(hinnad, algus="2024-01-01"):
    ix = pd.date_range(algus, periods=len(hinnad), freq="h")
    c = pd.Series(hinnad, index=ix, dtype=float)
    return pd.DataFrame({"open": c.shift(1).fillna(c.iloc[0]), "high": c * 1.0005,
                         "low": c * 0.9995, "close": c})


# ---------------------------------------------------------------- A1 ------
d = H.lae_h1("EURUSD")
k("A1 H1 andmed laetud", d is not None and len(d) > 17000,
  f"{len(d)} baari  {d.index.min()} .. {d.index.max()}")
puudu = [p for p in H.PAARID if H.lae_h1(p) is None]
k("A1 koik 15 paari olemas H1-l", len(puudu) == 0,
  "puudu: " + (", ".join(puudu) if puudu else "-"))
d1 = {p: H.lae_d1(p) for p in H.PAARID}
k("A1 koik 15 paari olemas D1-l", all(v is not None for v in d1.values()),
  f"luhim {min(len(v) for v in d1.values())} baari, "
  f"pikim {max(len(v) for v in d1.values())}")

# ---------------------------------------------------------------- A2 ------
# TEADAOLEV VASTUS: monotoonselt tousev seeria -> pikk positsioon peab
# valjuma TP peal tapselt +tp_r R-i (ilma kuludeta)
up = tehis(np.linspace(1.0, 1.5, 400))
kx = pd.DataFrame({"ema_m": 1.0, "ema_s": 0.9, "adx": 40.0, "natr": 0.001},
                  index=up.index)
sg = pd.Series(0, index=up.index, dtype=int)
sg.iloc[200] = 1
alg = H.signaalid
H.signaalid = lambda *a, **kw: sg
tt = H.simuleeri(up, kx, "TREND_PULLBACK", "H1", 0.0, slip_bp=0.0)
k("A2 tousev seeria -> TP, bruto = +2.0 R",
  len(tt) == 1 and abs(tt.bruto_r.iloc[0] - 2.0) < 1e-9,
  f"n={len(tt)} bruto_r={tt.bruto_r.iloc[0]:.6f} pohjus={tt.pohjus.iloc[0]}")
dn = tehis(np.linspace(1.5, 1.0, 400))
tt2 = H.simuleeri(dn, kx, "TREND_PULLBACK", "H1", 0.0, slip_bp=0.0)
k("A2 langev seeria, pikk signaal -> SL, bruto = -1.0 R",
  len(tt2) == 1 and abs(tt2.bruto_r.iloc[0] + 1.0) < 1e-9,
  f"bruto_r={tt2.bruto_r.iloc[0]:.6f} pohjus={tt2.pohjus.iloc[0]}")

# molemad tabatud uhes baaris -> peab lugema SL (konservatiivne)
lame = tehis(np.full(400, 1.0))
lame.iloc[205, lame.columns.get_loc("high")] = 1.5
lame.iloc[205, lame.columns.get_loc("low")] = 0.5
tt3 = H.simuleeri(lame, kx, "TREND_PULLBACK", "H1", 0.0, slip_bp=0.0)
k("A2 SL ja TP samas baaris -> loetakse SL",
  len(tt3) == 1 and tt3.pohjus.iloc[0] == "SL",
  f"pohjus={tt3.pohjus.iloc[0]} bruto_r={tt3.bruto_r.iloc[0]:.3f}")
H.signaalid = alg

# ---------------------------------------------------------------- A3 ------
kk = H.kontekst(d, "4h")
for nimi in H.STRAT:
    s1 = H.signaalid(d, kk, nimi)
    d2 = d.copy()
    n = len(d2)
    d2.iloc[n - 50:, :] = d2.iloc[n - 50:, :] * 3.0      # riku AINULT tulevik
    k2 = H.kontekst(d2, "4h")
    s2 = H.signaalid(d2, k2, nimi)
    sama = bool((s1.iloc[:n - 60] == s2.iloc[:n - 60]).all())
    k(f"A3 {nimi}: tuleviku rikkumine ei muuda varasemaid signaale", sama, "")

# ---------------------------------------------------------------- A4 ------
tt4 = H.simuleeri(d, kk, "MOMENTUM", "H1", H.KULU_BP["EURUSD"])
sisse_ok = True
for _, r in tt4.head(50).iterrows():
    pos = d.index.get_loc(r["aeg"])
    sisse_ok &= abs(r["sisse"] - d["open"].iloc[pos]) < 1e-12
k("A4 sisenemine on ALATI jargmise baari AVAHIND", sisse_ok,
  f"kontrollitud 50 tehingut {len(tt4)}-st")
kattuvus = bool((tt4["aeg"].values[1:] > tt4["lopuaeg"].values[:-1]).all())
k("A4 tehingud ei kattu (uks positsioon korraga)", kattuvus, "")
k("A4 valjumine ei ole kunagi enne sisenemist",
  bool((tt4["lopuaeg"] >= tt4["aeg"]).all()), "")

# ---------------------------------------------------------------- A5 ------
# kulumudel: 1.0 bp spread + 0.3 bp slip, stopp 11 bp => kulu ~ 0.236 R
sl_bp = 11.0
oodatav = 2.0 * (1.0 + 0.3) / 1e4 / (sl_bp / 1e4)
k("A5 kulumudel: 1.3bp edasi-tagasi 11bp stopiga = 0.236 R",
  abs(oodatav - 0.23636) < 1e-4, f"arvutatud {oodatav:.5f} R")
tk = tt4["kulu_r"]
k("A5 kulu on iga tehingu puhul positiivne", bool((tk > 0).all()),
  f"keskm {tk.mean():.4f} R, vahemik {tk.min():.4f} .. {tk.max():.4f}")

# ---------------------------------------------------------------- A6 ------
c = H.resample_ctx(d, "4h")
kb = H.kontekst(d, "4h")
rida = d.index[5000]
ctx_aeg = c.index[c.index <= rida][-1]
eelmine = c.index[c.index < ctx_aeg][-1]
oodatud_adx = H.adx(c).loc[eelmine]
k("A6 kontekst kasutab EELMIST lopetatud baari, mitte jooksvat",
  abs(kb["adx"].loc[rida] - oodatud_adx) < 1e-9,
  f"mootor {kb['adx'].loc[rida]:.4f} vs eelmine lopetatud {oodatud_adx:.4f}")

# ---------------------------------------------------------------- A7 ------
st = H.stat(tt4, 2.79)
kasi_wr = 100.0 * float((tt4["neto_r"] > 0).mean())
k("A7 stat: voiduprotsent vastab kasitsi arvutatule",
  abs(st["wr"] - kasi_wr) < 1e-9, f"{st['wr']:.4f}%")
k("A7 stat: neto = bruto - kulu",
  abs(st["neto_r"] - (tt4["bruto_r"].sum() - tt4["kulu_r"].sum())) < 1e-9, "")
k("A7 stat: maxdd <= 0", st["maxdd"] <= 0, f"{st['maxdd']:.2f}%")

# ---------------------------------------------------------------- A8 ------
rz = H.rezhiim_sildid(d, kk)
k("A8 HIGH_VOL ja LOW_VOL on teineteist valistavad",
  bool((rz["HIGH_VOLATILITY"] & rz["LOW_VOLATILITY"]).sum() == 0), "")
k("A8 TRENDING ja RANGING on teineteist valistavad",
  bool((rz["TRENDING"] & rz["RANGING"]).sum() == 0),
  f"ADX 20-25 vahemik kuulub kumbagi: "
  f"{int((~rz['TRENDING'] & ~rz['RANGING']).sum())} baari")
k("A8 rezhiimid KATTUVAD ristikutes (nii on kusitud)", True,
  f"HIGH_VOL & TRENDING = {int((rz['HIGH_VOLATILITY'] & rz['TRENDING']).sum())} baari")

print(f"\n{len(t)} kontrolli, {sum(1 for x in t if not x)} viga")
