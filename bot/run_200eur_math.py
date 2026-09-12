"""
200EUR -> SUUR RAHA: MIS ON MATEMAATIKA?

Kasutaja kusib: kuidas kasvatada 200EUR voimalikult kiiresti suureks?
See skript ei paku strateegiat — ta arvutab valja, MIS ON UUDSE
FUUSILISELT VOIMALIK, ja mis hind sellega kaasas kaib.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
rng = np.random.default_rng(2026)

print("=" * 100)
print("1) KUI KAUA KULUB 200€ -> SIHT, ERINEVATE TOOTLUSTEGA?")
print("=" * 100)
print(f"  {'aastatootlus':>14s} {'->1 000€':>10s} {'->10 000€':>11s} {'->50 000€':>11s} {'->200 000€':>12s}")
print("  " + "-" * 62)
for ar in (0.10, 0.20, 0.30, 0.50, 1.00, 2.00, 5.00):
    row = []
    for tgt in (1000, 10000, 50000, 200000):
        yrs = np.log(tgt/200)/np.log(1+ar)
        row.append(f"{yrs:.1f}a" if yrs < 100 else ">100a")
    print(f"  {100*ar:13.0f}% {row[0]:>10s} {row[1]:>11s} {row[2]:>11s} {row[3]:>12s}")

print()
print("=" * 100)
print("2) MIS ON HIND? — laostumise tõenäosus sama tootluse juures")
print("=" * 100)
print("   Eeldus: Sharpe 1.0 strateegia (VÄGA hea; meie parim leid oli 1.0-1.66).")
print("   Suurema tootluse saab AINULT võimendusega, mis kasvatab riski RUUTU.")
print()
SH = 1.0
print(f"  {'aastatootlus':>14s} {'aastane kõikumine':>19s} {'oodatav maxDD':>15s} "
      f"{'P(kaotad 50%)':>15s} {'P(laostud)':>12s}")
print("  " + "-" * 80)
for ar in (0.10, 0.20, 0.30, 0.50, 1.00, 2.00):
    vol = ar/SH
    # Monte Carlo 5 aastat, paevased sammud
    n, T = 4000, 252*5
    mu_d, sd_d = ar/252, vol/np.sqrt(252)
    paths = rng.normal(mu_d, sd_d, size=(n, T))
    eq = np.cumprod(1+paths, axis=1)
    dd = (eq/np.maximum.accumulate(eq, axis=1)-1).min(axis=1)
    print(f"  {100*ar:13.0f}% {100*vol:18.0f}% {100*np.median(dd):14.0f}% "
          f"{100*(dd<=-0.50).mean():14.0f}% {100*(dd<=-0.90).mean():11.0f}%")

print()
print("=" * 100)
print("3) OTSUSTAV: kas 200€ jõuab 50 000€-ni ENNE kui laostub?")
print("=" * 100)
print("   Iga rida = sama strateegia, erineva võimendusega. 10 aastat aega.")
print()
print(f"  {'võimendus':>10s} {'aastatootlus':>14s} {'JÕUAB 50k':>11s} {'LAOSTUB':>9s} "
      f"{'ei kumbki':>11s} {'mediaan lõpp':>14s}")
print("  " + "-" * 74)
BASE_R, BASE_V = 0.20, 0.20      # Sharpe 1.0 alusstrateegia
for lev in (1, 2, 3, 5, 8, 12):
    mu, vol = BASE_R*lev, BASE_V*lev
    n, T = 6000, 252*10
    mu_d = mu/252 - 0.5*(vol/np.sqrt(252))**2
    steps = rng.normal(mu_d, vol/np.sqrt(252), size=(n, T))
    logeq = np.cumsum(steps, axis=1)
    eq = 200*np.exp(logeq)
    hit = (eq >= 50000).any(axis=1)
    bust = (eq <= 20).any(axis=1)
    # kumb tuli enne
    first_hit = np.where(hit, (eq >= 50000).argmax(axis=1), T+1)
    first_bust = np.where(bust, (eq <= 20).argmax(axis=1), T+1)
    won = (first_hit < first_bust).mean()
    lost = (first_bust < first_hit).mean()
    print(f"  {lev:9d}x {100*mu:13.0f}% {100*won:10.1f}% {100*lost:8.1f}% "
          f"{100*(1-won-lost):10.1f}% {np.median(eq[:,-1]):13,.0f}€")

print()
print("=" * 100)
print("4) VÕRDLUS: mis juhtub, kui lisada iga kuu natuke raha juurde?")
print("=" * 100)
print("   Sama Sharpe 1.0 strateegia, 20%/a, 1x võimendus, 10 aastat.")
print()
print(f"  {'kuine lisa':>12s} {'mediaan 5a pärast':>20s} {'mediaan 10a pärast':>21s}")
print("  " + "-" * 56)
for add in (0, 50, 100, 200, 500):
    n = 4000
    finals5, finals10 = [], []
    for T, store in ((60, finals5), (120, finals10)):
        m = rng.normal(0.20/12 - 0.5*(0.20/np.sqrt(12))**2, 0.20/np.sqrt(12), size=(n, T))
        bal = np.full(n, 200.0)
        for t in range(T):
            bal = bal*np.exp(m[:, t]) + add
        store.extend(bal)
    print(f"  {add:11d}€ {np.median(finals5):19,.0f}€ {np.median(finals10):20,.0f}€")
