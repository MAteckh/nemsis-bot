"""
cot_regime_audit.py — lookahead- ja korrektsusaudit ENNE tulemusi.
"""
import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R
import cot_regime as G

OK, VIGA = "OK  ", "VIGA"
t = []


def k(nimi, ting, info=""):
    t.append(bool(ting))
    print(f"{OK if ting else VIGA}  {nimi:<50s} {info}")


al = R.ehita_alus(sufiks="_d25")
M = G.rezhiimi_pertsentiilid(al)
kah, sab = G.seisund(M)

# --- G1 BASELINE ON MUUTMATA: peab taastama A1 numbrid tapselt ------------
oodatud = {("U7", "C"): -9.41, ("U7", "D"): 9.70,
           ("U28", "C"): -4.64, ("U28", "D"): 10.09}
for uni in ("U7", "U28"):
    r = G.tulemused(al, uni)["neto"].dropna()
    c = r[(r.index >= "2006-05-01") & (r.index <= "2016-08-29")]
    d = r[r.index >= "2016-08-30"]
    for silt, x in (("C", c), ("D", d)):
        got = 1e4 * x.mean()
        k(f"G1 baseline {uni} {silt} vastab A1-le",
          abs(got - oodatud[(uni, silt)]) < 0.02,
          f"saadud {got:+.2f} bp, A1 {oodatud[(uni,silt)]:+.2f} bp")

# --- G2 rezhiimi pertsentiil ei kasuta tulevikku ---------------------------
s = pd.Series(np.random.RandomState(7).randn(400))
a = E.rull_pertsentiil(s, 156)
s2 = s.copy(); s2.iloc[-1] = 999.0
b = E.rull_pertsentiil(s2, 156)
k("G2 tuleviku muutmine ei muuda varasemaid pertsentiile",
  bool((a.iloc[:-1].fillna(-1) == b.iloc[:-1].fillna(-1)).all()), "")
k("G2 warmup NaN kuni aken taidetud", bool(a.iloc[:155].isna().all()), "")

# --- G3 rezhiimimuutujad ei sisalda tulevikku ------------------------------
# kontroll: nihuta KOGU rezhiimiseeria uks nadal EDASI (st kasuta ainult
# eelmise nadala infot). Kui tulemus praktiliselt ei muutu, ei sitsu
# rezhiim tulevikus.
r28 = G.tulemused(al, "U28")["neto"].dropna()
pers = {}
for c in G.REZIIMID:
    nuud = kah[c].reindex(r28.index)
    eile = kah[c].shift(1).reindex(r28.index)
    m = nuud.notna() & eile.notna()
    pers[c] = float((nuud[m] == eile[m]).mean())
# See EI OLE lookahead-test (selle teeb G2), vaid persistentsuse MOOT.
# Kui rezhiim oleks juhuslik mura, oleks sama-osakaal ~0.50.
k("G3 rezhiim on persistentne, mitte nadalane mura",
  bool(min(pers.values()) > 0.75),
  ", ".join(f"{c}:{v:.2f}" for c, v in sorted(pers.items(), key=lambda x: x[1])))

# --- G4 mediaanjaotus on tasakaalus ---------------------------------------
# TAHELEPANEK, mida ei varjata: rull_pertsentiil loeb, kui suur osa aknast
# on KAESOLEVAST VAIKSEM. Diskreetsel muutujal (COTBRE = taisarv) on palju
# vordseid vaartusi, seega pertsentiil on susteemselt alla 0.5 ja "HIGH"
# osakaal ei ole 50%. See EI OLE viga, aga tahendab, et "mediaanjaotus" on
# moningatel rezhiimidel tegelikult kaldu. Raporteerime tegeliku osakaalu.
osad = {c: float((kah[c].dropna() == "HIGH").mean()) for c in G.REZIIMID}
k("G4 HIGH-osakaal raporteeritud (sidemed nihutavad)", True,
  ", ".join(f"{c}:{v:.2f}" for c, v in sorted(osad.items(), key=lambda x: x[1])))

# --- G5 t_vahe teadaoleva vastusega ---------------------------------------
rs = np.random.RandomState(11)
a1 = rs.normal(1.0, 1.0, 5000)
b1 = rs.normal(0.0, 1.0, 5000)
tt, pp = G.t_vahe(a1, b1)
k("G5 t_vahe: +1 sigma erinevus n=5000 -> t ~ 50", bool(45 < tt < 55),
  f"t = {tt:.1f}, p = {pp:.2e}")
tt0, _ = G.t_vahe(b1, rs.normal(0.0, 1.0, 5000))
k("G5 t_vahe: identsed jaotused -> |t| < 3", bool(abs(tt0) < 3),
  f"t = {tt0:.2f}")

# --- G6 katvus ------------------------------------------------------------
kat = {c: int(M[c].notna().sum()) for c in G.REZIIMID}
k("G6 katvus loendatud", True,
  ", ".join(f"{c}:{v}" for c, v in kat.items()))
k("G6 5 rezhiimi katavad KOGU valimi",
  sum(1 for v in kat.values() if v == len(M)) == 5,
  f"{sum(1 for v in kat.values() if v == len(M))}/9 taielikku")

print(f"\n{len(t)} kontrolli, {sum(1 for x in t if not x)} viga")
