"""
LIVE-STRATEEGIA TULEMUSE KOVA KONTROLL.

Tulemus: +1983 EUR (kuludega), voiduprotsent 49.2%, PF 2.53, 65 tehingut.
TP/SL suhe on ~2.3:1, mille juures juhusliku jalutuskaigu voiduprotsent
peaks olema ~30%. Saime 49%. See on KAS paris serv VOI viga.

KONTROLLID:
  1. PIKAD vs LUHIKESED — kas kogu kasum tuleb kulla tousust?
  2. OSTA-JA-HOIA vordlus samal perioodil
  3. JUHUSLIK sisenemine sama TP/SL-iga (kas TP/SL ise teeb tulemuse?)
  4. AASTATE kaupa — kas stabiilne voi uks hea aasta?
  5. WALK-FORWARD lookbacki valikul
  6. KONTO ELLUJAAMINE — kas 205 EUR peab vastu?
  7. LOOKBACK-TUNDLIKKUS — kas 50 on tipp voi platoo?
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import gold_logic, kulumudel as K
from run_live_kuludega import lae, simuleeri, DD, PV, MIN_LOT

OUT = "live_kontroll.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

rng = np.random.default_rng(1809)
teh = simuleeri(False, None)
hind_k = float(DD["close"].median())
kulud = [K.tehingu_kulu(t, hind_k) for t in teh]
neto = np.array([(t.pnl or 0) - k for t, k in zip(teh, kulud)])

w("=" * 96)
w("1) PIKAD vs LÜHIKESED — kas kasum tuleb ainult kulla tõusust?")
w("=" * 96)
for suund in ("buy", "sell"):
    m = np.array([t.direction == suund for t in teh])
    if m.sum() == 0: continue
    x = neto[m]
    w(f"   {suund:5s}: {int(m.sum()):3d} tehingut, NETO {x.sum():+9.2f}€, "
      f"võit% {100*(x>0).mean():5.1f}, keskm {x.mean():+7.2f}€")
w("")
w("2) OSTA-JA-HOIA sama perioodi peal")
w("=" * 96)
d0 = DD[DD.index >= teh[0].opened_at]
bh_pct = float(d0["close"].iloc[-1] / d0["close"].iloc[0] - 1)
# 0.01 lot = 1 unts; osta-ja-hoia 1 untsiga
bh_eur = (float(d0["close"].iloc[-1]) - float(d0["close"].iloc[0])) * MIN_LOT * PV
w(f"   kuld tõusis {100*bh_pct:+.1f}%")
w(f"   osta-ja-hoia 1 untsiga (=0.01 lot): {bh_eur:+.2f}€")
w(f"   strateegia NETO:                    {neto.sum():+.2f}€")
w(f"   VAHE:                               {neto.sum()-bh_eur:+.2f}€")

w("")
w("3) JUHUSLIK sisenemine sama TP/SL-iga — kas TP/SL ise teeb tulemuse?")
w("=" * 96)
def juhuslik_sim(seed, n_teh):
    rg = np.random.default_rng(seed)
    d = DD
    out, lahti = [], None
    paevad = rg.choice(np.arange(70, len(d)-1), size=min(n_teh*3, len(d)-100), replace=False)
    lubatud = set(paevad.tolist())
    for i in range(70, len(d)-1):
        if lahti is not None:
            hi, lo = float(d["high"].iloc[i]), float(d["low"].iloc[i])
            tp_h = (hi >= lahti["tp"]) if lahti["dir"]=="buy" else (lo <= lahti["tp"])
            sl_h = (lo <= lahti["sl"]) if lahti["dir"]=="buy" else (hi >= lahti["sl"])
            v = "sl" if (tp_h and sl_h) else ("tp" if tp_h else ("sl" if sl_h else None))
            if v:
                tase = lahti["tp"] if v=="tp" else lahti["sl"]
                p = ((tase-lahti["e"]) if lahti["dir"]=="buy" else (lahti["e"]-tase))*MIN_LOT*PV
                out.append(p); lahti=None
        if lahti is not None or i not in lubatud: continue
        w_ = d.iloc[max(0,i-260):i+1]
        atr = gold_logic.calc_atr(w_)
        if not (np.isfinite(atr) and atr>0): continue
        sl_d = min(1.5*atr, 45.0/(MIN_LOT*PV)); tp_d = 3.0*atr
        dirn = rg.choice(["buy","sell"]); e = float(d["open"].iloc[i+1])
        lahti = dict(dir=dirn, e=e, tp=e+(tp_d if dirn=="buy" else -tp_d),
                     sl=e-(sl_d if dirn=="buy" else -sl_d))
    return np.array(out)

jt = [juhuslik_sim(s, len(teh)) for s in range(30)]
jsum = np.array([x.sum() - 0.6*len(x) for x in jt if len(x) > 10])   # ~0.6€ kulu/teh
jwr = np.array([100*(x>0).mean() for x in jt if len(x) > 10])
w(f"   strateegia:     NETO {neto.sum():+9.2f}€,  võit% {100*(neto>0).mean():.1f}")
w(f"   juhuslik (30x): NETO {jsum.mean():+9.2f}€ (mediaan {np.median(jsum):+.2f}, "
  f"parim {jsum.max():+.2f}), võit% {jwr.mean():.1f}")
w(f"   p(juhuslik >= strateegia) = {float((jsum >= neto.sum()).mean()):.3f}")

w("")
w("4) AASTATE KAUPA — stabiilne või üks hea aasta?")
w("=" * 96)
ser = pd.Series(neto, index=[t.closed_at for t in teh])
w(f"   {'aasta':>6s} {'tehinguid':>10s} {'NETO':>10s} {'võit%':>7s}")
w("   " + "-" * 38)
pos_a = 0
for a, g in ser.groupby(ser.index.year):
    pos_a += (g.sum() > 0)
    w(f"   {a:6d} {len(g):10d} {g.sum():+9.2f}€ {100*(g>0).mean():6.1f}%")
w(f"   => plussis {pos_a}/{ser.index.year.nunique()} aastat")

w("")
w("5) LOOKBACK-TUNDLIKKUS — kas 50 on üksik tipp või platoo?")
w("=" * 96)
import run_live_kuludega as R
w(f"   {'lookback':>9s} {'tehinguid':>10s} {'NETO':>10s} {'PF':>6s}")
w("   " + "-" * 40)
tul = {}
for lb in (20, 30, 40, 50, 60, 80, 100):
    R.LB = lb
    tt = R.simuleeri(False, None)
    if len(tt) < 10: 
        w(f"   {lb:9d} {len(tt):10d}   liiga vähe"); continue
    kk = [K.tehingu_kulu(t, hind_k) for t in tt]
    nn = np.array([(t.pnl or 0) - k for t, k in zip(tt, kk)])
    v, kl = nn[nn>0], nn[nn<=0]
    pf = v.sum()/abs(kl.sum()) if len(kl) and kl.sum()!=0 else 99
    tul[lb] = nn.sum()
    w(f"   {lb:9d} {len(tt):10d} {nn.sum():+9.2f}€ {pf:6.2f}")
R.LB = 50
plussis = sum(1 for v in tul.values() if v > 0)
w(f"   => plussis {plussis}/{len(tul)} lookbacki — "
  f"{'PLATOO (hea märk)' if plussis >= len(tul)-1 else 'ÜKSIK TIPP (halb märk)'}")

w("")
w("6) KAS 205€ KONTO PEAB VASTU?")
w("=" * 96)
bal = 205.0; miinimum = bal; pohjas = None
for t, k in zip(teh, kulud):
    bal += (t.pnl or 0) - k
    if bal < miinimum: miinimum, pohjas = bal, t.closed_at
w(f"   madalaim saldo: {miinimum:.2f}€ ({pohjas.date() if pohjas is not None else '-'})")
w(f"   lõppsaldo:      {bal:.2f}€")
kaotusjada = maxjada = 0
for x in neto:
    kaotusjada = kaotusjada + 1 if x < 0 else 0
    maxjada = max(maxjada, kaotusjada)
w(f"   pikim kaotusjada: {maxjada} tehingut")
w(f"   halvim üksiktehing: {neto.min():+.2f}€")
w(f"   {maxjada} järjestikust halvimat = {maxjada*neto.min():+.2f}€ "
  f"=> 205€ kontost jääks {205 + maxjada*neto.min():.2f}€")
if miinimum < 50:
    w("   HOIATUS: konto langes alla 50€ — 0.01 lot poleks enam mõistlik")
w("VALMIS")
