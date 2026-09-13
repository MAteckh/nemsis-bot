"""
LIVE-STRATEEGIA AUS TEST: portfelli jalg XAUUSD donchian 50, KULUDEGA.

MIS LIVE'IS TEGELIKULT JOOKSEB (kontrollitud koodist, mitte eeldatud):
  INSTRUMENTS["XAUUSD"]["enabled"] = False  => kulla grid EI joose
  portfolio_enabled = True, 1 jalg          => ainult see joose
  signaal: strategies.sig_donchian, lookback 50, PAEVABAARIL
  SL = 1.5 x ATR(14), TP = 3.0 x ATR(14)
  SL piiratud nii, et 0.01 lotiga kahjum <= 45 EUR
  1 positsioon korraga, 1 sisenemine paevas

KAKS ASJA, MIDA SEE TEST TEEB PAREMINI KUI backtest.py:
  1. KULUD. backtest.py rida 136 tunnistab, et neid ei modelleerita.
     Live maksab taie spreadi (ost ask'ilt, sulgemine bid'ilt —
     mt5_connector.py 143-144 ja 234-235) pluss slippage'i.
  2. TEEKOND. Paevabaar ei utle, kumb tabati enne, TP voi SL. Seda
     opiti valuliselt: breakout andis paevabaaridel Sharpe +4.76 ja
     tunniandmetel -1.48. Siin lahendame teekonna H1-baaridega seal,
     kus need olemas on.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import gold_logic, kulumudel as K
from config import GRID_CONFIG

OUT = "live_kuludega.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()


def lae(f):
    d = pd.read_csv(f"data/{f}", parse_dates=["Date"]).set_index("Date").sort_index()
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d[~d.index.duplicated(keep="last")].dropna()


DD = lae("XAUUSD_d.csv")
H1 = lae("XAUUSD_h1.csv")
LB = 50
SL_ATR, TP_ATR = 1.5, 3.0
MAX_LOSS = float(GRID_CONFIG.get("portfolio_max_loss_eur", 45.0))
PV = 100.0          # XAUUSD 1.00 lot = 100 untsi
MIN_LOT = 0.01


class T:
    __slots__ = ("direction","entry","tp","sl","lot","opened_at","closed_at","pnl","reason")
    def __init__(s, **kw):
        for k, v in kw.items(): setattr(s, k, v)
        s.closed_at = s.pnl = s.reason = None


def simuleeri(teekond_h1, algus=None):
    """teekond_h1=True => lahenda TP/SL H1-baaridega; muidu konservatiivne."""
    d = DD if algus is None else DD[DD.index >= algus]
    teh, lahti = [], None
    for i in range(LB + 20, len(d)):
        w_ = d.iloc[max(0, i - 260):i + 1]
        paev = d.index[i]
        # ── kas lahtine positsioon sulgub sel paeval? ──
        if lahti is not None:
            hi, lo = float(d["high"].iloc[i]), float(d["low"].iloc[i])
            tp_hit = (hi >= lahti.tp) if lahti.direction == "buy" else (lo <= lahti.tp)
            sl_hit = (lo <= lahti.sl) if lahti.direction == "buy" else (hi >= lahti.sl)
            valjus = None
            if tp_hit and sl_hit:
                if teekond_h1:
                    # lahenda H1-baaridega: kumb tuli ENNE?
                    tk = H1[(H1.index >= paev) & (H1.index < paev + pd.Timedelta(days=1))]
                    valjus = "sl"
                    for _, b in tk.iterrows():
                        t_ = (b["high"] >= lahti.tp) if lahti.direction=="buy" else (b["low"] <= lahti.tp)
                        s_ = (b["low"] <= lahti.sl) if lahti.direction=="buy" else (b["high"] >= lahti.sl)
                        if t_ and s_: valjus = "sl"; break
                        if t_: valjus = "tp"; break
                        if s_: valjus = "sl"; break
                else:
                    valjus = "sl"
            elif tp_hit: valjus = "tp"
            elif sl_hit: valjus = "sl"
            if valjus:
                tase = lahti.tp if valjus == "tp" else lahti.sl
                pnl = ((tase - lahti.entry) if lahti.direction == "buy"
                       else (lahti.entry - tase)) * lahti.lot * PV
                lahti.closed_at, lahti.pnl, lahti.reason = paev, pnl, valjus
                teh.append(lahti); lahti = None
        if lahti is not None or paev.weekday() >= 5:
            continue
        # ── uus signaal ──
        sig = None
        prior = w_.iloc[-(LB + 1):-1]
        hind = float(w_["close"].iloc[-1])
        atr = gold_logic.calc_atr(w_)
        if not (np.isfinite(atr) and atr > 0):
            continue
        if hind > float(prior["high"].max()): sig = "buy"
        elif hind < float(prior["low"].min()): sig = "sell"
        if sig is None: continue
        sl_d, tp_d = SL_ATR * atr, TP_ATR * atr
        # KOVA KAHJUMILAGI (main_v4.py 1069-1080)
        max_dist = MAX_LOSS / (MIN_LOT * PV)
        if sl_d > max_dist: sl_d = max_dist
        if i + 1 >= len(d): break
        entry = float(d["open"].iloc[i + 1])
        lahti = T(direction=sig, entry=entry,
                  tp=entry + (tp_d if sig == "buy" else -tp_d),
                  sl=entry - (sl_d if sig == "buy" else -sl_d),
                  lot=MIN_LOT, opened_at=d.index[i + 1])
    return teh


w("=" * 100)
w("LIVE-STRATEEGIA (portfell: XAUUSD donchian 50) — KULUDEGA JA ILMA")
w("=" * 100)
hind_k = float(DD["close"].median())
for nimi, algus, tk in (("2016-2026, päevabaar (konservatiivne)", None, False),
                        ("2024-2026, H1 teekond (täpne)", H1.index[0], True)):
    teh = simuleeri(tk, algus)
    if not teh:
        w(f"   {nimi}: tehinguid ei tekkinud"); continue
    hk = float(DD[DD.index >= (algus or DD.index[0])]["close"].median())
    w("")
    w(f"   --- {nimi} ---")
    w(f"   tehinguid {len(teh)}, periood "
      f"{teh[0].opened_at.date()} .. {teh[-1].closed_at.date() if teh[-1].closed_at else '-'}")
    res = {"trades": teh}
    bruto = sum(t.pnl for t in teh if t.pnl is not None)
    w(f"   {'stsenaarium':>20s} {'BRUTO':>9s} {'KULUD':>9s} {'NETO':>9s} "
      f"{'võit%':>7s} {'PF':>6s} {'maxDD':>8s} {'lõppkonto':>10s}")
    w("   " + "-" * 84)
    x0 = np.array([t.pnl or 0 for t in teh]); v0, k0 = x0[x0>0], x0[x0<=0]
    bal = 205.0; eq = [bal]
    for t in teh: bal += t.pnl or 0; eq.append(bal)
    eq = np.array(eq); dd0 = float((eq/np.maximum.accumulate(eq)-1).min())
    w(f"   {'KULUDETA':>20s} {bruto:+8.2f}€ {0.0:8.2f}€ {bruto:+8.2f}€ "
      f"{100*(x0>0).mean():6.1f}% "
      f"{(v0.sum()/abs(k0.sum()) if len(k0) and k0.sum()!=0 else 99):6.2f} "
      f"{100*dd0:+7.1f}% {eq[-1]:9.2f}€")
    for pn, prof in (("STANDARD-konto", K.VAIKE), ("ECN-konto", K.ECN)):
        r = K.rakenda(res, hk, prof, 205.0)
        w(f"   {pn:>20s} {r['bruto']:+8.2f}€ {r['kulu']:8.2f}€ {r['neto']:+8.2f}€ "
          f"{r['wr']:6.1f}% {r['pf']:6.2f} {100*r['maxdd']:+7.1f}% {r['lopp']:9.2f}€"
          f"{'  KONTO OTSAS' if r['ruin'] else ''}")

w("")
w("=" * 100)
w("KUI PALJU MUUDAB PÄEVABAARI MITMETIMÕISTETAVUS?")
w("=" * 100)
t_kons = simuleeri(False, H1.index[0])
t_tapne = simuleeri(True, H1.index[0])
bk = sum(t.pnl for t in t_kons if t.pnl)
bt = sum(t.pnl for t in t_tapne if t.pnl)
mitu = sum(1 for a, b in zip(t_kons, t_tapne) if a.reason != b.reason)
w(f"   konservatiivne (mõlemad tabatud => SL): {bk:+.2f}€")
w(f"   täpne (H1 ütleb, kumb oli enne):        {bt:+.2f}€")
w(f"   erineva väljumisega tehinguid: {mitu}/{len(t_kons)}")
w(f"   vahe: {bt-bk:+.2f}€")
w("VALMIS")
