"""
KAS 200 EUR SAAB AASTAGA ASENDADA TOOTASU? — lopplik arvutus.

Kasutaja soov: aasta parast peaks bot tooma nii palju, et ei peaks
enam tool kaima. Ta on varem oelnud: puhtalt kulud mitu tuhat kuus,
6 last.

See skript ei otsi strateegiat. Ta arvutab, MIDA SEE NOUAB ja mis on
parim voimalik tulemus koige parema strateegiaga, mis mul on
(JP225 |z|>1.0, 3% stopp, 2. pool: Sharpe +1.87, +20%/a 1x juures).
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(1)
OUT = "quit_job_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()


def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open", "High", "Low", "Close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()


jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index)
jp, spx = jp.reindex(ix), spx.reindex(ix)
o, h, l, c = jp["Open"], jp["High"], jp["Low"], jp["Close"]
rr = spx["Close"] / spx["Close"].shift(1) - 1
z = (rr / rr.rolling(60).std()).shift(1)
wsig = (np.sign(z) * (z.abs() > 1.0)).reindex(o.index).fillna(0.0)
S = 0.03
ls, ss = (l / o - 1) <= -S, (h / o - 1) >= S
ret = np.where(wsig > 0, np.where(ls, -S, c / o - 1),
      np.where(wsig < 0, np.where(ss, -S, 1 - c / o), 0.0))
ret = pd.Series(ret, index=o.index).where(lambda s: s.abs() < 0.25, 0.0)
net = (ret - (wsig != 0).astype(float) * 6 / 1e4).fillna(0.0)
mid = len(net) // 2
TR = net.iloc[mid:][wsig.iloc[mid:] != 0].values
K = 76                                    # tehingut aastas

w("=" * 78)
w("1) MIS ON 'EI PEA TÖÖL KÄIMA' EURODES?")
w("=" * 78)
w(f"   {'vajalik/kuus':>13s} {'aastas':>10s} {'konto 1x':>13s} {'konto 5x':>13s}")
w("   " + "-" * 54)
for m in (2000, 3000, 4000, 5000):
    a = m * 12
    w(f"   {m:12,d}€ {a:9,d}€ {a/0.20:12,.0f}€ {a/1.00:12,.0f}€")

w("")
w("=" * 78)
w("2) MIDA SEE 200 EUROLT ÜHE AASTAGA NÕUAB?")
w("=" * 78)
for siht, lbl in ((36000, "3000€/kuus (5x võimendusega)"),
                  (180000, "3000€/kuus (ilma võimenduseta)")):
    w(f"   {lbl:34s} 200€ -> {siht:,}€ = {siht/200:.0f}x "
      f"= {100*(siht/200-1):,.0f}%/aastas")

w("")
w("=" * 78)
w("3) PARIM VÕIMALIK TULEMUS (Monte Carlo, 40 000 katset, 1 aasta)")
w("=" * 78)
w(f"   {'võimendus':>10s} {'aastatootlus':>13s} {'mediaan lõpp':>14s} "
  f"{'P(jõuab 36k)':>14s} {'P(laostub)':>12s}")
w("   " + "-" * 68)


def sim(lev, siht=36000, n=40000):
    idx = rng.integers(0, len(TR), size=(n, K))
    x = np.maximum(TR[idx] * lev, -1.0)
    eq = 200 * np.cumprod(1 + x, axis=1)
    hm, bm = eq >= siht, eq <= 20
    hit, bust = hm.any(axis=1), bm.any(axis=1)
    fh = np.where(hit, hm.argmax(axis=1), K + 1)
    fb = np.where(bust, bm.argmax(axis=1), K + 1)
    won, lost = float((fh < fb).mean()), float((fb < fh).mean())
    lopp = np.where(bust & (fb < fh), 0.0, eq[:, -1])
    return won, lost, float(np.median(lopp))


for lev in (1, 5, 10, 20, 30, 40, 50, 80, 100):
    won, lost, med = sim(lev)
    w(f"   {lev:9d}x {100*TR.mean()*K*lev:12.0f}% {med:13,.0f}€ "
      f"{100*won:13.2f}% {100*lost:11.1f}%")

w("")
w("=" * 78)
w("4) PARIM VÕIMENDUS — maksimeeri P(jõuab)")
w("=" * 78)
best, bl, bruin = 0.0, None, 0.0
for lev in range(5, 201, 5):
    won, lost, _ = sim(lev, n=20000)
    if won > best:
        best, bl, bruin = won, lev, lost
w(f"   parim {bl}x juures: P(jõuab 36 000€ aastaga) = {100*best:.2f}%")
w(f"   samal ajal P(laostub) = {100*bruin:.1f}%")
w(f"   => {1/max(best,1e-9):.1f} katset ühe õnnestumise kohta,"
  f" oodatav kulu {200/max(best,1e-9):,.0f}€")

w("")
w("=" * 78)
w("5) AGA KAS 36 000 EUROT ANNABKI 3000 EUR/KUUS SISSETULEKUT?")
w("=" * 78)
w("   run_withdraw.py juba vastas sellele: 12 000€ kontolt 5x võimendusega")
w("   1000€/kuus välja võttes elab konto 10 aastat üle ainult 32.3% juhtudest")
w("   ja lõpeb mediaanis 1 008€ peal. 40x võimendusega on see oluliselt hullem.")
w("   'Jõuda 36 000€-ni' ja 'omada 3000€/kuus sissetulekut' EI OLE sama asi.")
w("VALMIS")
