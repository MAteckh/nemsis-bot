"""
KUI PALJU MAKSAB SEE, ET BACKTEST EI ARVESTA KULUSID?

Joosutab live-boti PRAEGUSE konfiguratsiooni kolm korda:
  1. ilma kuludeta            (nagu backtest.py praegu teeb)
  2. standard-konto kuludega  (spread 0.30$/unts + slippage)
  3. ECN-konto kuludega       (spread 0.12$ + komisjon 6$/lot)
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import backtest as B
import kulumudel as K
from config import GRID_CONFIG, INSTRUMENTS

OUT = "kulu_mojutus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

p = "data/XAUUSD_h1.csv"
df = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
df.columns = [c.strip().lower() for c in df.columns]
df = df[~df.index.duplicated(keep="last")].dropna()
hind = float(df["close"].median())

w("=" * 96)
w("KUI PALJU MAKSAB SEE, ET BACKTEST EI ARVESTA TEHINGUKULUSID?")
w("=" * 96)
w(f"   andmed: XAUUSD H1, {len(df)} baari, {df.index[0].date()} .. {df.index[-1].date()}")
w(f"   keskmine hind {hind:.0f}$")
w("")

res = B.simulate_gold_grid(df, grid_cfg=GRID_CONFIG,
                           instrument_cfg=INSTRUMENTS["XAUUSD"],
                           account_balance=205.0, pip_value=100.0)
teh = res["trades"]
w(f"   tehinguid: {len(teh)}")
if teh:
    lotid = [t.lot for t in teh]
    w(f"   lot: min {min(lotid):.2f}, mediaan {np.median(lotid):.2f}, max {max(lotid):.2f}")

w("")
w(f"   {'stsenaarium':>22s} {'tehinguid':>10s} {'BRUTO':>9s} {'KULUD':>9s} "
  f"{'NETO':>9s} {'kulu/teh':>9s} {'võit%':>7s} {'PF':>6s} {'maxDD':>8s}")
w("   " + "-" * 92)

# 1) ilma kuludeta
bruto = sum(t.pnl for t in teh if t.pnl is not None)
bal = 205.0; eq = [bal]
for t in teh:
    bal += (t.pnl or 0); eq.append(bal)
eq = np.array(eq)
dd0 = float((eq/np.maximum.accumulate(eq)-1).min())
x0 = np.array([t.pnl or 0 for t in teh])
v0, k0 = x0[x0>0], x0[x0<=0]
pf0 = v0.sum()/abs(k0.sum()) if len(k0) and k0.sum()!=0 else float('inf')
w(f"   {'1. KULUDETA (praegu)':>22s} {len(teh):10d} {bruto:+8.2f}€ "
  f"{0.0:8.2f}€ {bruto:+8.2f}€ {0.0:8.3f}€ {100*(x0>0).mean():6.1f}% "
  f"{pf0:6.2f} {100*dd0:+7.1f}%")

for nimi, prof in (("2. STANDARD-konto", K.VAIKE), ("3. ECN-konto", K.ECN)):
    r = K.rakenda(res, hind, prof, 205.0)
    if r is None: continue
    w(f"   {nimi:>22s} {r['n']:10d} {r['bruto']:+8.2f}€ {r['kulu']:8.2f}€ "
      f"{r['neto']:+8.2f}€ {r['kulu_teh']:8.3f}€ {r['wr']:6.1f}% "
      f"{r['pf']:6.2f} {100*r['maxdd']:+7.1f}%")

w("")
w("=" * 96)
w("KULUDE LAHTIVÕTMINE (standard-konto)")
w("=" * 96)
if teh:
    untse = sum(t.lot for t in teh) * 100
    sp = K.VAIKE["spread_usd"] * untse
    sl_ = 2 * K.VAIKE["slippage_usd"] * untse
    sl_extra = K.VAIKE["sl_slippage_usd"] * sum(
        t.lot * 100 for t in teh if t.reason and "sl" in str(t.reason).lower())
    sw = sum(K.tehingu_kulu(t, hind) for t in teh) - sp - sl_ - sl_extra
    w(f"   {'spread':>22s} {sp:8.2f}€   ({100*sp/(sp+sl_+sl_extra+sw):.0f}%)")
    w(f"   {'slippage (sisenemine+väljumine)':>22s} {sl_:8.2f}€   ({100*sl_/(sp+sl_+sl_extra+sw):.0f}%)")
    w(f"   {'SL-i lisaslippage':>22s} {sl_extra:8.2f}€   ({100*sl_extra/(sp+sl_+sl_extra+sw):.0f}%)")
    w(f"   {'swap (üle öö)':>22s} {sw:8.2f}€   ({100*sw/(sp+sl_+sl_extra+sw):.0f}%)")
    sl_teh = sum(1 for t in teh if t.reason and "sl" in str(t.reason).lower())
    w("")
    w(f"   SL-iga suletud tehinguid: {sl_teh}/{len(teh)} ({100*sl_teh/len(teh):.0f}%)")
    ule_oo = sum(1 for t in teh if t.closed_at and t.opened_at
                 and (t.closed_at - t.opened_at).days > 0)
    w(f"   üle öö hoitud: {ule_oo}/{len(teh)} ({100*ule_oo/len(teh):.0f}%)")
w("VALMIS")
