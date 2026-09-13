"""
cot_engine.py — CFTC COT (Commitments of Traders) positsioneerimise mootor.

EESMARK (NEMSIS jargmine uurimiskategooria): kas avalik CFTC COT
positsioneerimine sisaldab FX-tootluste kohta infot, mida OHLC-hinnas EI OLE?
Koik senised ~11 650 NEMSIS-testi kasutasid AINULT hinda. COT on esimene
tegelikult uus infoallikas.

TAHTIS — SEE ON UURIMISKOOD. Ta EI PUUDUTA live-faile
(main_v4.py, config.py, mt5_connector.py, strategy_meanrev.py, backtest.py).

-----------------------------------------------------------------------------
ANDMED
-----------------------------------------------------------------------------
Allikas : CFTC Public Reporting Environment, Socrata dataset 6dca-aqww
          "Commitments of Traders - Legacy Futures Only"
          https://publicreporting.cftc.gov/resource/6dca-aqww.json
Tee     : liivakastil pole otseuhendust cftc.gov-iga (agent-proxy 403).
          Kasutaja Supabase'i `http` laiendus teeb paringu, tulemus laeti
          tabelisse cot_legacy ja eksporditi -> bot/data/cot_legacy.csv
Kontrat : CME valuutafutuurid (mitte spot-FX!):
          EUR 099741, GBP 096742, JPY 097741, CHF 092741, CAD 090741,
          AUD 232741, NZD 112741, MXN 095741, USD-indeks 098662
Vahemik : 2004-01-06 .. 2026-09-08, nadalane (reedene aruanne teisipaeva seisuga)
Veerud  : noncomm_positions_long_all / _short_all (suured spekulandid),
          comm_positions_long_all / _short_all (hedgerid), open_interest_all

-----------------------------------------------------------------------------
AVALDAMISE AJASTUS — SEE ON KOIGE OLULISEM LOOKAHEAD-RISK
-----------------------------------------------------------------------------
CFTC COT reeglid:
  * vaatlusaeg (report date) = TEISIPAEV turu sulgemine
  * avaldamine               = sama nadala REEDE 15:30 ET
  * st info on avalik 3 paeva PARAST vaatlust

Seetottu EI TOHI teisipaeva positsiooni kasutada enne reedet 15:30 ET.

NEMSIS-i konservatiivne valik: esimene kaubeldav hind on ESMASPAEVA
sulgemine, st report_date + >= 6 kalendripaeva. See on ruhkem kui
noutav (reede 15:30 ET oleks juba lubatud, FX on lahti kuni 17:00 ET),
aga valistab koik pupliseerimisviivituse- ja ajavoondikusimused.
Pyhade tottu on 21/1393 aruannet nihkes (esmaspaev voi kolmapaev) —
sellepargi kasutame "esimene kauplemispaev alates report_date + 6d",
mitte fikseeritud nadalapaeva.

Tundlikkus: reede sulgemise sisenemist raporteeritakse eraldi (kiirem,
aga agressiivsem eeldus).

-----------------------------------------------------------------------------
EELREGISTREERITUD HUPOTEESID (fikseeritud ENNE jooksutamist)
-----------------------------------------------------------------------------
A  EXTREME   : net_pct rullpertsentiil 156 nadalat; >=0.90 = korgeim detsiil,
               <=0.10 = madalaim detsiil. Lavid on FIKSEERITUD, mitte
               optimeeritud.
B  CHANGE    : nadal-nadala muutus net_pct-s, ristloikeline jarjestus;
               top-2 valuutat +1, bottom-2 valuutat -1.
C  EXTREME+PX: A signaal, mis jaab alles AINULT siis, kui 12-nadalane
               hinnamomentum on samas suunas. Uks eelregistreeritud
               hinnakomponent, mitte indikaatorigrid.
D  SUUND     : iga signaal joostakse MOLEMAS suunas:
               CONT (jarg positsioneerimisele) ja REV (vastu).
               Kumb on oige, EI OLE ette eeldatud.

Hoideperioodid : 1, 2, 4 nadalat (ainult need)
Kokku variante : 6 signaali x 3 hoidu x 2 universumit = 36
"""
import math
import os

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# --- eelregistreeritud konstandid ------------------------------------------
PERTS_AKEN = 156        # nadalat (3 aastat) rullpertsentiili jaoks
LAVI_YLA = 0.90
LAVI_ALA = 0.10
MOM_NADALAD = 12        # C-variandi hinnakinnitus
VIIVE_PAEVI = 6         # report_date -> esimene kaubeldav paev
HOIUD = (1, 2, 4)

VALUUTAD = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]

# USD-vaartus: 1 uhik valuutat = ? USD. inv=True => seeria on USDXXX.
USD_LEG = {
    "EUR": ("EURUSD", False), "GBP": ("GBPUSD", False),
    "AUD": ("AUDUSD", False), "NZD": ("NZDUSD", False),
    "JPY": ("USDJPY", True),  "CHF": ("USDCHF", True),
    "CAD": ("USDCAD", True),
}
# 7 paari, millel on PARIS hinnaseeria kettal (primaarne universum)
U7 = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD"]

# uhesuunaline kulu bp, v5_engine.py KULU["BASE"]-ga sama tase
KULU_BASE = {"EURUSD": 1.0, "GBPUSD": 1.2, "AUDUSD": 1.2, "NZDUSD": 1.8,
             "USDJPY": 1.0, "USDCHF": 1.3, "USDCAD": 1.3}
KULU_RIST = 2.2         # ristpaaride (EURJPY jms) tuupiline uhesuunaline bp

TRAIN_LOPP = pd.Timestamp("2020-08-31")
VALID_LOPP = pd.Timestamp("2023-08-31")


# ---------------------------------------------------------------- andmed ---
def lae_hind(sym, sufiks="_d"):
    """
    Paevane sulgemishind. sufiks="_d" on 2016-2026 seeria (algne COT-toos),
    sufiks="_d25" on Yahoo 25-aastane seeria (COT A1 pikendustest).
    MOLEMAD tulevad SAMAST allikast (Yahoo `=X` paevane close, sama
    load_yahoo_bars funktsioon) — andmeallikat EI vahetata perioodide vahel.
    """
    p = os.path.join(DATA, f"{sym}{sufiks}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    return pd.to_numeric(d["close"], errors="coerce").dropna()


def puhasta_spike(s, lavi=0.05, tagasi=0.30):
    """
    Eemaldab OILMSED andmeveavad: uhe paeva hupe, mis JARGMISEL paeval
    peaaegu taielikult tagasi poordub.

    MIKS SEE ON VAJALIK: Yahoo `=X` seeria sisaldab 2008. aastal
    umberpoorduvaid valehindu, nt EURUSD 2008-12-08 sulgemine 1.49180
    (+15.96%) ja jargmisel paeval -14.33% tagasi; sama paev USDJPY
    109.24 (+16.29%) ja -16.85% tagasi. Vaartus 1.55710 kordub EURUSD-s
    mitmel paeval 2008. aastal — kinni jaanud kvoot.

    Reegel on MEHAANILINE ja SUMMEETRILINE, mitte tulemustepohine:
      lipp, kui |r_t| >= 5% JA |r_t + r_(t+1)| <= 30% * |r_t|
    Paris hupped (SNB porand 2011-09-06 +9.2%, selle kaotamine
    2015-01-16 -17.6%, Brexit 2016-06-26 -7.9%) EI poordu tagasi ja
    jaavad puutumata. Lipuga paeva sulgemine asendatakse naaberpaevade
    geomeetrilise keskmisega.

    Vaikimisi EI kasutata (raporteerime nii puhastatud kui toorest).
    """
    x = s.astype(float).copy()
    r = np.log(x).diff()
    r2 = r.shift(-1)
    lipp = (r.abs() >= lavi) & ((r + r2).abs() <= tagasi * r.abs())
    idx = np.where(lipp.fillna(False).values)[0]
    for i in idx:
        if 0 < i < len(x) - 1:
            x.iloc[i] = math.sqrt(float(x.iloc[i - 1]) * float(x.iloc[i + 1]))
    return x, int(len(idx))


def usd_vaartused(sufiks="_d", puhasta=False):
    """Series-dict: 1 uhik valuutat USD-des. USD = 1.0."""
    v = {"USD": None}
    for c, (sym, inv) in USD_LEG.items():
        s = lae_hind(sym, sufiks)
        if s is None:
            continue
        if puhasta:
            s, _ = puhasta_spike(s)
        v[c] = (1.0 / s) if inv else s
    ix = None
    for c, s in v.items():
        if s is None:
            continue
        ix = s.index if ix is None else ix.intersection(s.index)
    out = {c: (pd.Series(1.0, index=ix) if s is None else s.reindex(ix))
           for c, s in v.items()}
    return pd.DataFrame(out).dropna()


def paari_hind(V, paar):
    """Paari sulgemishind USD-vaartustest. U7 puhul = tapselt originaalseeria."""
    b, q = paar[:3], paar[3:]
    return V[b] / V[q]


def lae_cot():
    p = os.path.join(DATA, "cot_legacy.csv")
    d = pd.read_csv(p, parse_dates=["date"])
    d["net"] = d["nc_long"] - d["nc_short"]
    d["net_pct"] = d["net"] / d["oi"]
    return d


def net_pct_tabel(d, usd_allikas="implitseeritud"):
    """
    nadal x valuuta, net_pct = (nc_long - nc_short) / open_interest.

    USD-l EI OLE CME-s oma FX-futuuri koigi valuutade vastu. Koik CME
    FX-kontraktid on kvoteeritud USD vastu, seega pikk EUR-futuur ON
    luhike USD. Eelregistreeritud primaarne definitsioon:
        USD net_pct = - (7 valuuta net_pct keskmine)
    Robustsusvariant usd_allikas="USDX" kasutab USD-indeksi futuuri (098662).
    """
    t = d.pivot_table(index="date", columns="cur", values="net_pct").sort_index()
    muud = [c for c in VALUUTAD if c != "USD" and c in t.columns]
    if usd_allikas == "USDX" and "USDX" in t.columns:
        t["USD"] = t["USDX"]
    else:
        t["USD"] = -t[muud].mean(axis=1)
    return t[[c for c in VALUUTAD if c in t.columns]]


# --------------------------------------------------------------- signaal ---
def rull_pertsentiil(s, aken=PERTS_AKEN):
    """
    Pertsentiil OMA ajaloo sees, ainult MINEVIK + kaesolev vaatlus.
    Lookahead-kaitse: rank arvutatakse aknas, mis lopeb kaesoleva reaga.

    NaN-id (NZD-l 86 puuduvat nadalat enne 2016) visatakse enne akna
    moodustamist valja, muidu loeks aken NaN-vordlusi Vaaraks ja
    pertsentiil oleks alla kaldu.
    """
    puhas = s.dropna()
    p = puhas.rolling(aken, min_periods=aken).apply(
        lambda w: (w[:-1] < w[-1]).mean(), raw=True)
    return p.reindex(s.index)


def skoor_A(P):
    """+1 = ekstreemselt pikk spekulatiivne positsioon, -1 = ekstreemselt luhike."""
    return (P >= LAVI_YLA).astype(float) - (P <= LAVI_ALA).astype(float)


def skoor_B(N, top=2):
    """Nadalane muutus, ristloikeline jarjestus: top-2 = +1, bottom-2 = -1."""
    d = N.diff()
    r = d.rank(axis=1, ascending=False)
    n = d.notna().sum(axis=1)
    plus = r.le(top) & d.notna()
    minus = r.gt(n.values[:, None] - top) & d.notna()
    return plus.astype(float) - minus.astype(float)


# ---------------------------------------------------------- simulatsioon ---
def sisenemispaevad(cot_kuup, hinna_ix, viive=VIIVE_PAEVI, max_nihe=14):
    """
    report_date -> esimene kauplemispaev alates report_date + viive.

    max_nihe kaitseb selle eest, et COT-ajalugu (2004-) on pikem kui
    hinnaseeria (2016-09-): ilma selleta seotaks koik vanad aruanded
    esimese olemasoleva hinnapaevaga ja tekiks vale "signaal".
    """
    hi = pd.DatetimeIndex(hinna_ix)
    out = {}
    for rd in cot_kuup:
        t = rd + pd.Timedelta(days=viive)
        pos = hi.searchsorted(t, side="left")
        if pos < len(hi) and (hi[pos] - rd).days <= max_nihe:
            out[rd] = hi[pos]
    return pd.Series(out).sort_index()


def nadala_hinnad(V, paarid, sis):
    """Paaride sulgemishinnad AINULT sisenemispaevadel (nadalane seeria)."""
    H = pd.DataFrame({p: paari_hind(V, p) for p in paarid})
    return H.reindex(sis.values)


def kaalud(S, paarid, hoia):
    """
    Paari signaal = baasvaluuta skoor - kvootvaluuta skoor.
    Hoideperiood h: kaal = h viimase nadala signaali keskmine (kattuvad
    positsioonid), normeeritud nii et sum|w| = 1.
    """
    sg = pd.DataFrame({p: np.sign(S[p[:3]] - S[p[3:]]) for p in paarid},
                      index=S.index)
    W = sg.rolling(hoia, min_periods=1).mean()
    n = W.abs().sum(axis=1)
    return W.div(n.where(n > 0), axis=0).fillna(0.0)


def portfell(W, H, kulu_bp):
    """
    Nadalane portfellitootlus. W read = sisenemisnadalad (Esmaspaev).
    Kaal w_t teenib tootlust t -> t+1. Kulu = kulu_bp * |dw|.
    """
    R = np.log(H).diff().shift(-1)          # t -> t+1 tootlus
    R = R.reindex(W.index)
    # rida kolbab ainult siis, kui KOIGIL kaalu saanud paaridel on tootlus
    puudu = ((W != 0) & R.isna()).any(axis=1) | R.isna().all(axis=1)
    bruto = (W * R.fillna(0.0)).sum(axis=1).where(~puudu)
    dw = W.diff().abs()
    if isinstance(kulu_bp, dict):
        k = pd.Series({c: kulu_bp.get(c, KULU_RIST) for c in W.columns})
        kulu = (dw * k / 1e4).sum(axis=1)
    else:
        kulu = dw.sum(axis=1) * kulu_bp / 1e4
    neto = bruto - kulu
    return pd.DataFrame({"bruto": bruto, "kulu": kulu, "neto": neto}).dropna()


# -------------------------------------------------------------- statistika -
def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def nppf(p):
    lo, hi = -12.0, 12.0
    for _ in range(200):
        m = (lo + hi) / 2
        if ncdf(m) < p:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def deflated_sharpe(sh, sh_std, n_obs, n_katseid, skew=0.0, kurt=3.0):
    """
    Bailey & Lopez de Prado deflated Sharpe. scipy puudub => oma ncdf/nppf.

    UHIKUD (siin tehti esimesel katsel viga ja see on parandatud):
      * sh      — Sharpe VAATLUSE kohta (nadalane), mitte aastastatud
      * sh_std  — katsetatud variantide Sharpe'ide standardhalve, sama uhik
      * n_obs   — vaatluste arv

    E[max SR] = sh_std * ((1-gamma)*Z^-1[1-1/N] + gamma*Z^-1[1-1/(N*e)])
    Ilma sh_std teguriga on valem vale (annab absurdse SR* ~ 2.1 nadalas).
    """
    if n_obs < 30 or n_katseid < 2 or sh_std <= 0:
        return float("nan")
    e = 0.5772156649
    sh_max = sh_std * (nppf(1 - 1.0 / n_katseid) * (1 - e)
                       + nppf(1 - 1.0 / (n_katseid * math.e)) * e)
    sd = math.sqrt(max((1 - skew * sh + (kurt - 1) / 4.0 * sh ** 2)
                       / (n_obs - 1), 1e-12))
    return ncdf((sh - sh_max) / sd)


def moodikud(x, nimi=""):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 20:
        return None
    sd = x.std(ddof=1)
    eq = np.cumprod(1 + x)
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    v, k = x[x > 0], x[x <= 0]
    return dict(nimi=nimi, n=len(x),
                keskm_bp=float(x.mean() * 1e4),
                sh=float(x.mean() / sd * math.sqrt(52)) if sd > 0 else 0.0,
                kokku=float(eq[-1] - 1), maxdd=dd,
                pf=float(v.sum() / abs(k.sum())) if len(k) and k.sum() != 0 else float("inf"),
                wr=100.0 * float((x > 0).mean()),
                v_keskm_bp=float(v.mean() * 1e4) if len(v) else 0.0,
                k_keskm_bp=float(k.mean() * 1e4) if len(k) else 0.0,
                t=float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0)


def p_kahepoolne(t):
    return 2.0 * (1.0 - ncdf(abs(t)))


def bh(pvals, q=0.05):
    """Benjamini-Hochberg. Tagastab lavi-p ja loendi, mis labivad."""
    m = len(pvals)
    jrk = sorted(range(m), key=lambda i: pvals[i])
    lavi = 0.0
    for r, i in enumerate(jrk, 1):
        if pvals[i] <= q * r / m:
            lavi = pvals[i]
    return lavi, [i for i in range(m) if pvals[i] <= lavi and lavi > 0]


def jaota(x):
    return (x[x.index <= TRAIN_LOPP],
            x[(x.index > TRAIN_LOPP) & (x.index <= VALID_LOPP)],
            x[x.index > VALID_LOPP])
