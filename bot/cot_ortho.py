"""
cot_ortho.py — kas COT-s on infot, mida hinnas EI OLE? (otsustav test)

Meetod: regresseeri iga valuuta net_pct tema enda varasemale hinnaliikumisele
(4/12/26/52 nadalat), vota JAAK ja aja jaak labi TAPSELT sama masinavarga
(156n rullpertsentiil -> ekstreemsed detsiilid -> REV). Kui jaak tootab,
siis COT kannab hinnast soltumatut infot.

Lisaks: regiimijaotus (VIX korge/madal).
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

al = R.ehita_alus()
IDX = al["sis"].index
p28, k28 = R.universum("U28", al["V"])
p7, k7 = R.universum("U7", al["V"])
H28 = E.nadala_hinnad(al["V"], p28, al["sis"]); H28.index = IDX
H7 = E.nadala_hinnad(al["V"], p7, al["sis"]); H7.index = IDX


def rea(nimi, x, laius=30):
    m = E.moodikud(x, nimi)
    if m is None:
        return f"{nimi:<{laius}s}  (liiga vahe vaatlusi)"
    return (f"{nimi:<{laius}s}{m['n']:>5d}{m['keskm_bp']:>9.2f}{m['sh']:>8.2f}"
            f"{100*m['kokku']:>9.1f}{100*m['maxdd']:>8.1f}{m['pf']:>7.2f}"
            f"{m['wr']:>7.1f}{m['t']:>7.2f}{E.p_kahepoolne(m['t']):>8.3f}")


def pais(laius=30):
    return (f"{'variant':<{laius}s}{'n':>5s}{'keskm_bp':>9s}{'sharpe':>8s}"
            f"{'kokku%':>9s}{'maxdd%':>8s}{'pf':>7s}{'wr%':>7s}{'t':>7s}{'p':>8s}")


print("=" * 106)
print("R21  ORTOGONALISEERITUD COT — net_pct jaak parast hinnamomentumi mahalahutamist")
print("=" * 106)
Nw = al["Nw"]
Vw = al["V"].reindex(al["sis"].values); Vw.index = IDX
LOG = np.log(Vw).reindex(columns=Nw.columns)

def jaak(N, X_list):
    """Rull-regressioon oleks ule voimenduse; kasutame EXPANDING OLS-i,
    et mitte kasutada tulevikku: iga rea koefitsiendid on hinnatud
    AINULT sellest reast varasemate andmetega."""
    out = pd.DataFrame(index=N.index, columns=N.columns, dtype=float)
    for c in N.columns:
        y = N[c].values
        X = np.column_stack([np.ones(len(N))] + [x[c].values for x in X_list])
        ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
        for i in range(len(N)):
            if not ok[i]:
                continue
            m = ok.copy(); m[i:] = False
            if m.sum() < 104:          # vaja vahemalt 2 aastat ajalugu
                continue
            b, *_ = np.linalg.lstsq(X[m], y[m], rcond=None)
            out.iloc[i, out.columns.get_loc(c)] = y[i] - X[i] @ b
    return out

MOMS = [LOG.diff(k) for k in (4, 12, 26, 52)]
Nres = jaak(Nw, MOMS)
print(f"jaak arvutatud: {int(Nres.notna().all(axis=1).sum())} taielikku rida "
      f"(expanding OLS, min 104 nadalat ajalugu)")
Pres = Nres.apply(E.rull_pertsentiil)
print(pais())
print(rea("U28 A_REV algne (net_pct)",
          E.portfell(E.kaalud(R.skoorid(al, "A_REV"), p28, 1), H28, k28)["neto"]))
print(rea("U28 A_REV ORTOGONAALNE jaak",
          E.portfell(E.kaalud(-E.skoor_A(Pres), p28, 1), H28, k28)["neto"]))
print(rea("U7  A_REV algne (net_pct)",
          E.portfell(E.kaalud(R.skoorid(al, "A_REV"), p7, 1), H7, k7)["neto"]))
print(rea("U7  A_REV ORTOGONAALNE jaak",
          E.portfell(E.kaalud(-E.skoor_A(Pres), p7, 1), H7, k7)["neto"]))
# kui palju net_pct-st hind uldse seletab
r2 = {}
for c in Nw.columns:
    y = Nw[c].values
    X = np.column_stack([np.ones(len(Nw))] + [x[c].values for x in MOMS])
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    b, *_ = np.linalg.lstsq(X[ok], y[ok], rcond=None)
    e = y[ok] - X[ok] @ b
    r2[c] = 1 - e.var() / y[ok].var()
print("\nR2: kui palju hinnamomentum (4/12/26/52n) seletab net_pct-st:")
print("  " + "  ".join(f"{c} {100*v:.0f}%" for c, v in r2.items()))
print(f"  keskmine {100*np.mean(list(r2.values())):.0f}% "
      f"=> {100-100*np.mean(list(r2.values())):.0f}% on hinnast SOLTUMATU")

print()
print("=" * 106)
print("R22  REZIIMID — VIX korge vs madal")
print("=" * 106)
vix = E.lae_hind("VIX")
vw = vix.reindex(al["sis"].values, method="ffill"); vw.index = IDX
mediaan = vw.median()
x28 = E.portfell(E.kaalud(R.skoorid(al, "A_REV"), p28, 1), H28, k28)["neto"].dropna()
x7 = E.portfell(E.kaalud(R.skoorid(al, "A_REV"), p7, 1), H7, k7)["neto"].dropna()
print(f"VIX mediaan {mediaan:.1f}")
print(pais())
for nimi, x in (("U28", x28), ("U7", x7)):
    v = vw.reindex(x.index)
    print(rea(f"{nimi} VIX > {mediaan:.0f} (korge)", x[v > mediaan]))
    print(rea(f"{nimi} VIX <= {mediaan:.0f} (madal)", x[v <= mediaan]))
