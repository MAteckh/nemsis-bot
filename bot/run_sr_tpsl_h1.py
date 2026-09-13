"""
S/R STRATEEGIA PARIS TP/SL-IGA, TUNNIANDMETEL.

MIKS UUS TEST: eelmine (run_support_resist.py) ei testinud kasutaja
strateegiat. Ta testis ainult, kas signaal ennustab jargmise paeva
suunda — ilma TP ja SL-ita. Kasutaja idee on aga "vota sealt ainult
vaike kasum", mis TAHENDAB TP-d.

MIKS TUNNIANDMED: paevabaaridel EI TOHI testida paevasiseseid TP/SL
tasemeid. Seda opiti valuliselt: breakout-straddle andis paevabaaridel
Sharpe +4.76 ja tunniandmetel -1.48, sest paevabaar ei utle, KUMB
tase tabati esimesena.

MIDA PRO 20 AASTA KOGEMUSEGA TEEKS TEISITI:
  1. TREND FILTER — ara kauple S/R-i trendi vastu. Osta tugilt AINULT
     tousutrendis, muu vastupanult AINULT langustrendis.
  2. R:R SUHE — testi mitut, mitte uht. Vaike TP nouab KORGET
     voiduprotsenti; suur TP lubab madalat.
  3. VOLATIILSUSE SKAALA — TP/SL ATR-i uhikutes, mitte fikseeritud
     dollarites. Tase, mis on rahulikul turul kaugel, on kiirel lahedal.
  4. KINNITUS — mitte iga puude tasemel ei ole tagasilukkamine.
     Noua, et kuunal ka SULGEKS tasemest tagasi.

Testime koik neli koos ja uksikult, et naha, mis paranduse annab.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

OUT = "sr_tpsl_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

H1 = {"XAUUSD": "XAUUSD_h1.csv", "SPX": "SPX_h1.csv",
      "NAS100": "NAS100_h1.csv", "WTI": "WTI_h1.csv"}
COST_BP = {"XAUUSD": 0.4, "SPX": 0.4, "NAS100": 0.3, "WTI": 1.5}


def load(f):
    p = os.path.join(R.DATA, f)
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()[["open", "high", "low", "close"]]


def atr(d, n=14):
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def simuleeri(d, sym, N=50, tp_atr=0.5, sl_atr=1.0, trend_filter=True,
              kinnitus=True, max_baare=24):
    """
    Kaib tunnibaarid labi. Signaal: S/R test + tagasipoordumine.
    Valjub TP-l, SL-il voi max_baare parast. TEEKONNA-TEADLIK.
    """
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    a = atr(d)
    vast = h.rolling(N).max().shift(1)
    tugi = l.rolling(N).min().shift(1)
    ema = c.ewm(span=200).mean()
    rt = 2 * COST_BP[sym] / 1e4

    ov, ot, oc, oa = vast.values, tugi.values, c.values, a.values
    oh, ol, oo, oe = h.values, l.values, o.values, ema.values
    n = len(d)
    tehingud = []
    i = 210
    while i < n - 1:
        if not (np.isfinite(oa[i]) and oa[i] > 0 and np.isfinite(ov[i])):
            i += 1
            continue
        suund = 0
        # tagasilukkamine vastupanult => luhike
        if oh[i] >= ov[i] and (oc[i] < ov[i] if kinnitus else True):
            suund = -1
        # pordumine toelt => pikk
        elif ol[i] <= ot[i] and (oc[i] > ot[i] if kinnitus else True):
            suund = 1
        if suund == 0:
            i += 1
            continue
        if trend_filter:
            if suund == 1 and oc[i] < oe[i]:
                i += 1
                continue
            if suund == -1 and oc[i] > oe[i]:
                i += 1
                continue
        entry = oo[i + 1]
        tp = entry + suund * tp_atr * oa[i]
        sl = entry - suund * sl_atr * oa[i]
        tulem = None
        for j in range(i + 1, min(i + 1 + max_baare, n)):
            hi, lo = oh[j], ol[j]
            tp_hit = (hi >= tp) if suund == 1 else (lo <= tp)
            sl_hit = (lo <= sl) if suund == 1 else (hi >= sl)
            if tp_hit and sl_hit:
                tulem = -sl_atr * oa[i] / entry      # konservatiivne: SL
                break
            if tp_hit:
                tulem = tp_atr * oa[i] / entry
                break
            if sl_hit:
                tulem = -sl_atr * oa[i] / entry
                break
        if tulem is None:
            j = min(i + max_baare, n - 1)
            tulem = suund * (oc[j] - entry) / entry
        tehingud.append(tulem - rt)
        i = j + 1
    return np.array(tehingud)


def stat(t):
    if len(t) < 30:
        return None
    eq = np.cumprod(1 + t)
    return dict(n=len(t), keskm=t.mean(), wr=100 * (t > 0).mean(),
                sh=t.mean() / t.std() * math.sqrt(252) if t.std() > 0 else 0,
                kokku=eq[-1] - 1)


w("=" * 100)
w("S/R STRATEEGIA PÄRIS TP/SL-IGA, TUNNIBAARID (teekonna-teadlik)")
w("=" * 100)
for sym, f in H1.items():
    d = load(f)
    if d is None or len(d) < 2000:
        continue
    w("")
    w(f"--- {sym}  ({d.index[0].date()} .. {d.index[-1].date()}, {len(d)} H1 baari) ---")
    w(f"  {'TP/SL (ATR)':>12s} {'trend':>6s} {'kinnit':>7s} {'teh':>5s} "
      f"{'võit%':>7s} {'keskm bp':>10s} {'kokku':>9s}")
    w("  " + "-" * 66)
    for tp_a, sl_a in ((0.25, 0.5), (0.5, 0.5), (0.5, 1.0), (1.0, 1.0), (1.5, 1.0), (2.0, 1.0)):
        for tf in (True, False):
            t = simuleeri(d, sym, tp_atr=tp_a, sl_atr=sl_a, trend_filter=tf)
            s = stat(t)
            if s is None:
                continue
            mark = "  <<<" if s["keskm"] > 0 else ""
            w(f"  {tp_a:5.2f}/{sl_a:<6.2f} {'JAH' if tf else 'ei':>6s} "
              f"{'JAH':>7s} {s['n']:5d} {s['wr']:6.1f}% {1e4*s['keskm']:+9.2f} "
              f"{100*s['kokku']:+8.1f}%{mark}")
w("VALMIS")
