"""
h1engine.py — jagatud mootor paevasiseste (H1) strateegiate testimiseks.

Miks eraldi moodul: iga strateegiaskript vajab samu asju — andmete
laadimist, kulusid, sessiooniaegu, walk-forwardi, null-jaotust. Kui iga
skript teeb neid ise, tekivad erinevused ja tulemused ei ole vorreldavad.

PEAMISED REEGLID, mis siin on sisse kirjutatud (opitud vigadest):
  1. Signaal arvutatakse baari i SULGEMISEL, sisenetakse baari i+1
     AVANEMISEL. Kunagi ei kasutata jooksva baari high/low'd otsuseks.
  2. Kulu on EDASI-TAGASI (2 x uhesuunaline), rakendatud iga tehingu peal.
  3. Walk-forward: valik AINULT 1. aknast. 2. akent ei tohi valikul
     kuidagi kasutada.
  4. Null-jaotus: juhuslikustatakse SIGNAALI SUUND, kulud rakendatakse
     uuesti. Mitte abs() valmis tootluse peal — see muudab kulu kasumiks.
"""
import os, math
import numpy as np, pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Uhesuunaline kulu baaspunktides. Kaks taset, et naha, kui palju
# tulemus broogeri hinnakirjast soltub.
KULU_RETAIL = {           # tavaline retail-CFD konto (konservatiivne)
    "EURUSD": 1.0, "GBPUSD": 1.2, "USDJPY": 1.0, "AUDUSD": 1.2,
    "USDCAD": 1.3, "USDCHF": 1.3, "NZDUSD": 1.8, "EURJPY": 1.5,
    "GBPJPY": 1.8, "AUDJPY": 1.8, "EURAUD": 1.8, "EURGBP": 1.5,
    "XAUUSD": 1.5, "XAGUSD": 4.0,
    "WTI": 3.0, "SPX": 1.5, "NAS100": 1.5, "GER40": 2.0,
    "JP225": 3.0, "UK100": 2.5, "BTCUSD": 8.0,
}
KULU_ECN = {k: v * 0.35 for k, v in KULU_RETAIL.items()}   # ECN raw + komisjon

FX = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
      "EURJPY", "GBPJPY", "AUDJPY", "EURAUD", "EURGBP"]
MUUD = ["XAUUSD", "XAGUSD", "WTI", "SPX", "NAS100", "GER40", "JP225",
        "UK100", "BTCUSD"]
KOIK = FX + MUUD


def lae(sym):
    """H1 baarid. Tagastab None, kui faili pole voi on liiga luhike."""
    p = os.path.join(DATA, f"{sym}_h1.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna()[["open", "high", "low", "close"]]
    # eemalda lamedad baarid (high==low) — need on andmeaugud, mitte turg
    d = d[(d["high"] > d["low"]) | (d["high"] == d["low"])]
    return d if len(d) >= 3000 else None


def lae_koik(symbols=None):
    symbols = symbols or KOIK
    out = {}
    for s in symbols:
        d = lae(s)
        if d is not None:
            out[s] = d
    return out


def atr(d, n=14):
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def sharpe(x, baare_aastas=6000):
    """H1-baaride Sharpe aastapohiseks. FX kaupleb ~6000 tundi aastas."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 50 or x.std() == 0:
        return 0.0
    return float(x.mean() / x.std() * math.sqrt(baare_aastas))


def teh_sharpe(t, teh_aastas):
    """Tehingupohine Sharpe, skaleeritud tehingute sagedusega."""
    t = np.asarray(t, dtype=float)
    t = t[np.isfinite(t)]
    if len(t) < 30 or t.std() == 0:
        return 0.0
    return float(t.mean() / t.std() * math.sqrt(teh_aastas))


def tulevik(d, k):
    """Tootlus: sisene baari i+1 avanemisel, valju baari i+k sulgemisel."""
    return (d["close"].shift(-k) / d["open"].shift(-1) - 1)


def hinda(sg, y, kulu_bp, teh_aastas=None):
    """
    Signaali (+1/0/-1) hinnang fikseeritud horisondiga.
    Tagastab dict voi None, kui tehinguid liiga vahe.
    """
    sg = pd.Series(sg).fillna(0.0)
    ix = sg.index.intersection(y.index)
    s, yy = sg.reindex(ix), y.reindex(ix)
    mask = (s != 0) & yy.notna()
    n = int(mask.sum())
    if n < 100:
        return None
    rt = 2 * kulu_bp / 1e4
    t = (s[mask] * yy[mask] - rt).values
    if teh_aastas is None:
        aastaid = max((ix[-1] - ix[0]).days / 365.25, 0.5)
        teh_aastas = n / aastaid
    m = len(t) // 2
    return dict(n=n, keskm=float(t.mean()), bruto=float((s[mask]*yy[mask]).mean()),
                wr=100 * float((t > 0).mean()), sh=teh_sharpe(t, teh_aastas),
                p1=float(t[:m].mean()), p2=float(t[m:].mean()),
                tstat=float(t.mean() / t.std() * math.sqrt(n)) if t.std() > 0 else 0.0,
                teh_aastas=teh_aastas, t=t)


def simuleeri_tpsl(d, sg, kulu_bp, tp, sl, max_baare=24):
    """
    TEEKONNA-TEADLIK simulatsioon. tp/sl on ATR-i kordajad.
    Sisenemine baari i+1 avanemisel, valjumine TP/SL/aja peal.
    Kui moLEMAD tabatud samas baaris, eeldame SL (konservatiivne).
    """
    a = atr(d).values
    o, h, l, c = (d["open"].values, d["high"].values,
                  d["low"].values, d["close"].values)
    s = np.asarray(pd.Series(sg).reindex(d.index).fillna(0.0).values)
    rt = 2 * kulu_bp / 1e4
    n = len(d)
    teh, ajad = [], []
    i = 20
    while i < n - 1:
        if s[i] == 0 or not (np.isfinite(a[i]) and a[i] > 0):
            i += 1
            continue
        suund = int(np.sign(s[i]))
        entry = o[i + 1]
        tp_h = entry + suund * tp * a[i]
        sl_h = entry - suund * sl * a[i]
        r, j = None, i + 1
        for j in range(i + 1, min(i + 1 + max_baare, n)):
            th = (h[j] >= tp_h) if suund == 1 else (l[j] <= tp_h)
            sh_ = (l[j] <= sl_h) if suund == 1 else (h[j] >= sl_h)
            if th and sh_:
                r = -sl * a[i] / entry; break
            if th:
                r = tp * a[i] / entry; break
            if sh_:
                r = -sl * a[i] / entry; break
        if r is None:
            j = min(i + max_baare, n - 1)
            r = suund * (c[j] - entry) / entry
        teh.append(r - rt)
        ajad.append(d.index[i])
        i = j + 1
    return np.array(teh), pd.DatetimeIndex(ajad)


def null_jaotus(ehita_sg, d, y, kulu_bp, rng, katseid=20, lavi=0.0):
    """
    Mitu korda labiks JUHUSLIK suund sama soela? ehita_sg() peab
    tagastama signaaliseeria; siin vahetatakse ainult MARK.
    """
    sg = ehita_sg(d)
    baas = hinda(sg, y, kulu_bp)
    if baas is None:
        return None, None
    nz = (sg != 0)
    ok = 0
    for _ in range(katseid):
        v = pd.Series(0.0, index=sg.index)
        v[nz] = rng.choice([-1.0, 1.0], size=int(nz.sum()))
        r = hinda(v, y, kulu_bp)
        if r and r["keskm"] > lavi:
            ok += 1
    return baas, ok / katseid
