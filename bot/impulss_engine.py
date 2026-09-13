"""
impulss_engine.py — IMPULSI JATKUVUSE / POORDUMISE TEST.

EELREGISTREERITUD REEGLID (kasutaja punktid 4-7). Neid EI muudeta
parast tulemuste nagemist.

IMPULSI VARIANDID:
  A: kuunla ulatus >= 1.5 x ATR(14) JA sulgemine kuunla ulemises 25%
     (tous) voi alumises 25% (langus)
  B: sama, aga ulatus >= 2.0 x ATR(14)
  C: kaks jarjestikust kuunalt samas suunas, koguliikumine >= 1.5 x ATR,
     viimane kuunal sulgeb liikumise suunas

KINNITUSED:
  JATK:     impulss murrab viimase 6 baari tipu/pohja
  TAGASI:   jargmine LOPETATUD kuunal EI poora impulssi taielikult

HOIDMISAJAD: 1, 2, 4 baari
ATR-STOPP:   puudub, 0.75 x ATR, 1.0 x ATR
SUUND:       JATKUVUS voi POORDUMINE

LOOKAHEAD-KAITSE (kasutaja punkt 3), iga koht eraldi:
  1. ATR(14) on .shift(1) — arvutatud baari i-1 seisuga, EI sisalda
     jooksva baari ulatust. Vastasel juhul oleks kunnis osaliselt
     iseennast maaratlev (suur baar tostab oma ATR-i).
  2. 6-baari tipp/pohi on .rolling(6).max().shift(1) — baarid i-6..i-1,
     jooksev baar EI ole sees.
  3. Sisenemine on ALATI baari i+1 AVANEMISHIND.
  4. Valjumine on baari i+1+k SULGEMISHIND voi stopi tase teel.
  5. Jarjestus portfelli jaoks kasutab ainult impulsi tugevust
     (ulatus/ATR), mis on teada baari i sulgemisel.
  6. Mitte uhtegi normaliseerimist tuleviku andmete peal.
"""
import numpy as np, pandas as pd
import h1engine as E


def atr_shift(d, n=14):
    """ATR baari i-1 seisuga. shift(1) on LOOKAHEAD-KAITSE."""
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0/n, adjust=False).mean().shift(1)


def impulss(d, variant):
    """Tagastab +1 (tousuimpulss) / -1 (langusimpulss) / 0, ja tugevuse."""
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    a = atr_shift(d)
    ulatus = h - l
    asend = (c - l) / ulatus.replace(0, np.nan)      # 0=pohjas, 1=tipus
    if variant in ("A", "B"):
        lavi = 1.5 if variant == "A" else 2.0
        suur = ulatus >= lavi * a
        up = suur & (asend >= 0.75)
        dn = suur & (asend <= 0.25)
        tugevus = (ulatus / a).where(up | dn, 0.0)
    elif variant == "C":
        # kaks jarjestikust kuunalt samas suunas
        d1 = c - o
        sama = (np.sign(d1) == np.sign(d1.shift(1))) & (d1 != 0)
        koos = (c - o.shift(1)).abs()
        suur = sama & (koos >= 1.5 * a)
        up = suur & (d1 > 0)
        dn = suur & (d1 < 0)
        tugevus = (koos / a).where(up | dn, 0.0)
    else:
        raise ValueError(variant)
    sg = up.astype(float) - dn.astype(float)
    return sg.fillna(0.0), tugevus.fillna(0.0)


def kinnitus(d, sg, tuup):
    """JATK: murrab 6 baari tipu/pohja. TAGASI: jargmine ei poora."""
    h, l, c, o = d["high"], d["low"], d["close"], d["open"]
    if tuup == "JATK":
        hi6 = h.rolling(6).max().shift(1)        # baarid i-6..i-1
        lo6 = l.rolling(6).min().shift(1)
        ok = ((sg > 0) & (h >= hi6)) | ((sg < 0) & (l <= lo6))
        return sg.where(ok, 0.0), 0              # sisenemine baaril i+1
    if tuup == "TAGASI":
        # jargmine LOPETATUD kuunal (i+1) ei poora impulssi taielikult
        # => otsus tehakse i+1 sulgemisel, sisenemine i+2 avanemisel
        imp_lo, imp_hi = l, h
        j_c = c.shift(-1)
        ei_poora = ((sg > 0) & (j_c > imp_lo)) | ((sg < 0) & (j_c < imp_hi))
        return sg.where(ei_poora.fillna(False), 0.0), 1
    raise ValueError(tuup)


def simuleeri(d, sg, hoia, stop_atr=None, suund=+1, nihe=0):
    """
    TEEKONNA-TEADLIK. Sisenemine baaril i+1+nihe AVANEMISEL.
    Valjumine: stopp teel, muidu hoia baari parast SULGEMISEL.
    suund=+1 jatkuvus, -1 poordumine.
    Tagastab DataFrame: aeg, sym, suund, bruto, tugevus.
    """
    o, h, l, c = (d["open"].values, d["high"].values,
                  d["low"].values, d["close"].values)
    a = atr_shift(d).values
    s = sg.values
    n = len(d)
    out = []
    for i in np.flatnonzero(s != 0):
        e_idx = i + 1 + nihe
        x_idx = e_idx + hoia
        if x_idx >= n or not (np.isfinite(a[i]) and a[i] > 0):
            continue
        dirn = int(np.sign(s[i])) * suund
        entry = o[e_idx]
        r = None
        if stop_atr:
            sl = entry - dirn * stop_atr * a[i]
            for j in range(e_idx, x_idx + 1):
                hit = (l[j] <= sl) if dirn == 1 else (h[j] >= sl)
                if hit:
                    r = -stop_atr * a[i] / entry
                    break
        if r is None:
            r = dirn * (c[x_idx] - entry) / entry
        out.append((d.index[i], dirn, r))
    if not out:
        return None
    return pd.DataFrame(out, columns=["aeg", "dir", "bruto"])
