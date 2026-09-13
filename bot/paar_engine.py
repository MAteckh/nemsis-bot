"""
paar_engine.py — UKS mootor, mis joosutab koiki paaripohiseid
konfiguratsioone (PDF punkt 8: "ara ehita 15 koodibaasi").

LOOKAHEAD-KAITSE (PDF punkt 9: "signaalid, mis soltuvad tulevikust voi
candle'i sulgumata andmetest"):
  - iga indikaator arvutatakse baari i SULGEMISE seisuga
  - otsus tehakse baaril i, sisenetakse baaril i+1 AVANEMISEL
  - vahemikutasemed (murre_lb) on .shift(1) — jooksev baar valja
  - ATR ja ADX kasutavad ainult moodunud baare
"""
import numpy as np, pandas as pd


# ══ INDIKAATORID (Wilder'i silumine, nagu MT5-s) ═════════════════
def _wilder(x, n):
    return x.ewm(alpha=1.0 / n, adjust=False).mean()


def atr(d, n=14):
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return _wilder(tr, n)


def adx(d, n=14):
    h, l, pc = d["high"], d["low"], d["close"].shift(1)
    up = h.diff()
    dn = -l.diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr_ = _wilder(tr, n)
    pdi = 100 * _wilder(pd.Series(plus, index=d.index), n) / atr_
    mdi = 100 * _wilder(pd.Series(minus, index=d.index), n) / atr_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return _wilder(dx.fillna(0.0), n)


def rsi(d, n=14):
    delta = d["close"].diff()
    up = _wilder(delta.clip(lower=0), n)
    dn = _wilder((-delta).clip(lower=0), n)
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50.0)


def bb(d, n=20, k=2.0):
    m = d["close"].rolling(n).mean()
    s = d["close"].rolling(n).std()
    return m - k * s, m, m + k * s


# ══ SIGNAALID ════════════════════════════════════════════════════
def sig_trend_pullback(d, cfg, adx_min, ind):
    """EMA joondus + ADX + tagasitomme + RSI riba."""
    c = d["close"]
    f, m, s = cfg["ema"]
    ef, em = c.ewm(span=f).mean(), c.ewm(span=m).mean()
    es = c.ewm(span=s).mean() if s else em
    tous = (ef > em) & (em > es) if s else (ef > em)
    lang = (ef < em) & (em < es) if s else (ef < em)
    tugev = ind["adx"] > adx_min
    # tagasitomme: hind kais EMA-fast'ist labi ja tuli tagasi
    tagasi_up = (c > ef) & (c.shift(1) <= ef.shift(1))
    tagasi_dn = (c < ef) & (c.shift(1) >= ef.shift(1))
    rl, rh = cfg["rsi_long"]
    sl_, sh_ = cfg["rsi_short"]
    r = ind["rsi"]
    lng = tous & tugev & tagasi_up & r.between(rl, rh)
    srt = lang & tugev & tagasi_dn & r.between(sl_, sh_)
    return (lng.astype(float) - srt.astype(float)).fillna(0.0)


def sig_breakout(d, cfg, adx_min, ind, retest=True):
    """N-baari vahemiku murre + EMA suund (+ valikuline retest/ATR-filter)."""
    c, h, l = d["close"], d["high"], d["low"]
    lb = cfg.get("murre_lb", 20)
    hi = h.rolling(lb).max().shift(1)
    lo = l.rolling(lb).min().shift(1)
    f, m, _ = cfg["ema"]
    ef, em = c.ewm(span=f).mean(), c.ewm(span=m).mean()
    up_ok, dn_ok = ef > em, ef < em
    tugev = ind["adx"] > adx_min if adx_min else pd.Series(True, index=d.index)
    murre_up = (c > hi) & up_ok & tugev
    murre_dn = (c < lo) & dn_ok & tugev
    if cfg.get("atr_ule_mediaani"):
        a = ind["atr"]
        lai = a > a.rolling(240).median()
        murre_up, murre_dn = murre_up & lai, murre_dn & lai
    if retest:
        # murre eelmisel baaril, jooksev baar tuli tasemele tagasi JA
        # sulgeb taas murde suunas => "retest rather than first spike"
        murre_up = (murre_up.shift(1).fillna(False) & (l <= hi) & (c > hi))
        murre_dn = (murre_dn.shift(1).fillna(False) & (h >= lo) & (c < lo))
    return (murre_up.astype(float) - murre_dn.astype(float)).fillna(0.0)


def sig_mean_rev(d, cfg, adx_max, ind):
    """Madal ADX + BB aare + RSI aare (PDF: RSI on setup, mitte trigger)."""
    c = d["close"]
    n, k = cfg.get("bb", (20, 2.0))
    alum, kesk, ulem = bb(d, n, k)
    rahulik = ind["adx"] < adx_max
    r = ind["rsi"]
    lng = rahulik & (c < alum) & (r < cfg.get("rsi_ost", 30))
    srt = rahulik & (c > ulem) & (r > cfg.get("rsi_muuk", 70))
    return (lng.astype(float) - srt.astype(float)).fillna(0.0)


# ══ TEEKONNA-TEADLIK SIMULATSIOON ════════════════════════════════
def simuleeri(d, sg, sl_atr, tp_r, kulu_bp, ind, sess=(0, 24),
              max_baare=120):
    """
    SL = sl_atr x ATR(14). TP = tp_r x SL-kaugus (R-kordne).
    Sisenemine baaril i+1 avanemisel. Kui TP ja SL tabatud samas
    baaris, eeldame SL (konservatiivne — baar ei utle jarjekorda).
    Tagastab tehingute DataFrame'i koos MAE/MFE-ga (PDF punkt 6).
    """
    o, h, l, c = (d["open"].values, d["high"].values,
                  d["low"].values, d["close"].values)
    a = ind["atr"].values
    adx_v = ind["adx"].values
    s = sg.values
    tund = d.index.hour.values
    h0, h1 = sess
    rt = kulu_bp / 1e4                      # uhesuunaline; rakendame 2x
    n = len(d)
    teh = []
    i = 250
    while i < n - 1:
        if s[i] == 0 or not (np.isfinite(a[i]) and a[i] > 0):
            i += 1; continue
        if not (h0 <= tund[i] < h1):
            i += 1; continue
        suund = int(np.sign(s[i]))
        entry = o[i + 1]
        sl_d = sl_atr * a[i]
        tp_d = tp_r * sl_d
        tp = entry + suund * tp_d
        slh = entry - suund * sl_d
        r, pohjus, j = None, "aeg", i + 1
        mae = mfe = 0.0
        for j in range(i + 1, min(i + 1 + max_baare, n)):
            liik_hea = (h[j] - entry) if suund == 1 else (entry - l[j])
            liik_halb = (entry - l[j]) if suund == 1 else (h[j] - entry)
            mfe = max(mfe, liik_hea); mae = max(mae, liik_halb)
            th = (h[j] >= tp) if suund == 1 else (l[j] <= tp)
            sh_ = (l[j] <= slh) if suund == 1 else (h[j] >= slh)
            if th and sh_:
                r, pohjus = -sl_d / entry, "SL"; break
            if th:
                r, pohjus = tp_d / entry, "TP"; break
            if sh_:
                r, pohjus = -sl_d / entry, "SL"; break
        if r is None:
            j = min(i + max_baare, n - 1)
            r = suund * (c[j] - entry) / entry
        teh.append(dict(aeg=d.index[i + 1], suund=suund, tulem=r - 2 * rt,
                        bruto=r, pohjus=pohjus, kestus=j - i,
                        mae_r=mae / sl_d, mfe_r=mfe / sl_d,
                        adx=adx_v[i], tund=tund[i]))
        i = j + 1
    return pd.DataFrame(teh)


# ══ MOODIKUD (PDF punkt 6) ═══════════════════════════════════════
def moodikud(t, aastaid):
    if t is None or len(t) < 20:
        return None
    x = t["tulem"].values
    v, k = x[x > 0], x[x <= 0]
    eq = np.cumprod(1 + x)
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    neto = float(eq[-1] - 1)
    pf = float(v.sum() / abs(k.sum())) if len(k) and k.sum() != 0 else np.inf
    teh_a = len(x) / aastaid
    return dict(
        n=len(x), teh_kuus=len(x) / (aastaid * 12),
        neto=neto, pf=pf, ootus=float(x.mean()),
        wr=100 * float((x > 0).mean()),
        kesk_v=float(v.mean()) if len(v) else 0.0,
        kesk_k=float(k.mean()) if len(k) else 0.0,
        maxdd=dd, taastumis=neto / abs(dd) if dd < 0 else np.inf,
        sharpe=float(x.mean() / x.std() * np.sqrt(teh_a)) if x.std() > 0 else 0.0,
        tstat=float(x.mean() / x.std() * np.sqrt(len(x))) if x.std() > 0 else 0.0,
        mae_r=float(t["mae_r"].mean()), mfe_r=float(t["mfe_r"].mean()),
        kestus=float(t["kestus"].mean()))


def valmista(d):
    """Arvutab indikaatorid uks kord, et neid ei arvutataks iga variandi jaoks."""
    return dict(atr=atr(d, 14), adx=adx(d, 14), rsi=rsi(d, 14))
