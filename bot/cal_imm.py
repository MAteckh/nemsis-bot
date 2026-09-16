"""
cal_imm.py — ECONOMIC CALENDAR IMMEDIATE RELEASE EXECUTION TEST (mootor).

KUSIMUS, MIS ON UUS. B1 testis PAEVAST efekti. B2 testis VIIVITATUD efekti
(T+8h -> T+32h) ja leidis, et kogu mootedetav efekt on loigus 0h -> 1h
(+9.55 bp, t = 11.51), mida H1-baaridega EI SAA kaubelda. Siin testime,
kas selle hupe ESIMENE OSA on TEGELIKULT TAIDETAV.

VANA (B1/B2)                          UUS (see test)
  paevane / viivitatud efekt            vahetu valjalaske taitmine
  ristloikeliselt tsentreeritud         UHE PAARI toores log-tootlus
  valuutatootlus
  sisenemine tunde hiljem               sisenemine esimesel voimalikul hinnal
  H1 voi paevabaarid                    M5 / M15 (korgeim olemasolev)

Neid EI SEGATA. B1/B2 definitsioone EI MUUDETA.

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py, gold_logic.py,
strategies.py).

-----------------------------------------------------------------------------
ANDMEAUDIT — MIS REPOS ON JA MIS MITTE (mooedetud, mitte eeldatud)
-----------------------------------------------------------------------------
  TICK        EI OLE
  BID/ASK     EI OLE          => taitmishind on SIMULEERITUD, mitte paris
  M1          EI OLE          => D1 (+1 min) on DATA INSUFFICIENT
  M5          2026-08-05 .. 2026-09-16   42 paeva, 7 majorit
              (laetud Yahoo'st Supabase kaudu; Yahoo annab 5m baare
               ainult ~60 paeva tagasi — seda EI SAA pikendada)
  M15         2026-06-22 .. 2026-09-11   81 paeva
  H1          2023-11-27 .. 2026-09-11   2.79 aastat

  Seetottu on see test KOLMEASTMELINE ja iga aste on eraldi margitud:
    RADA A  M5   korgeim resolutsioon, LUHIM valim  (n = 15 T1 |z|>=1)
    RADA B  M15  keskmine resolutsioon               (n = 39)
    RADA C  H1   pikim valim, AGA ei suuda lahendada alla 60 min
                 (n = 408) — sama andmestik mis B2

  RADA A ja B ei kanna jareldavat statistikat. Nad on KIRJELDAVAD.
  RADA C kannab statistikat, aga EI SAA vastata kusimusele "kas hupet
  saab taita", sest tema vaikseim samm on tund.

-----------------------------------------------------------------------------
EELREGISTREERITUD ENNE ESIMEST JOOKSU
-----------------------------------------------------------------------------
ullatus     z = (actual - forecast) / rull-std(20 VARASEMAT sama
            (valuuta, indikaator) prognoosiviga, min 10), shift(1) enne
            rolling'ut. cal_engine.z_ullatus KUTSUTAKSE OTSE.
suund       sign(z) * eelregistreeritud majanduslik mark (cal_engine.TIER1)
lavi        PRIMARY |z| >= 1;  tundlikkus 1.5 ja 2.0 (EI OPTIMEERITA)
sisenemine  D0 = esimene baar, mille SULGEMINE on >= valjalaske hetk
            lisaks D5 D15 D30 D60 (minutites parast valjalaset)
            D1 (+1 min) = DATA INSUFFICIENT, M1-andmeid ei ole
hoid        PRIMARY 30 min;  tundlikkus 5 / 15 / 60 / 120 min
kulu        paaripohine uhesuunaline bp x 2 (edasi-tagasi)
libisemine  SUNDMUSE lisalibisemine, rakendub UKS KORD sisenemisel:
            0 / 1 / 2 / 3 / 5 / 10 bp
tootlus     UHE PAARI toores log-tootlus (MITTE ristloikeliselt
            tsentreeritud — see on taitmistest uhel instrumendil)
seeme       20260916
"""
import math
import os

import numpy as np
import pandas as pd

import cal_engine as C

DATA = C.DATA
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEME = 20260916

LAVID = [1.0, 1.5, 2.0]
VIIVITUSED = [0, 1, 5, 15, 30, 60]          # minutites; 1 = DATA INSUFFICIENT
HOIUD = [5, 15, 30, 60, 120]                # minutites
PRIMARY_VIIVITUS, PRIMARY_HOID = 0, 30
LIBISEMISED = [0.0, 1.0, 2.0, 3.0, 5.0, 10.0]   # bp, UKS KORD sisenemisel
N_BOOT = 2000

# --- INSTRUMENDIKAART, fikseeritud ENNE tulemuste nagemist ----------------
# iga valuuta koige likviidsem major; (paar, kas valuuta on BAAS)
KAART = {
    "EUR": ("EURUSD", True),  "USD": ("EURUSD", False),
    "GBP": ("GBPUSD", True),  "JPY": ("USDJPY", False),
    "CHF": ("USDCHF", False), "AUD": ("AUDUSD", True),
    "CAD": ("USDCAD", False), "NZD": ("NZDUSD", True),
}
KULU_1SUUND = {"EURUSD": 1.0, "GBPUSD": 1.2, "USDJPY": 1.0, "AUDUSD": 1.2,
               "NZDUSD": 1.8, "USDCAD": 1.3, "USDCHF": 1.3}

RAJAD = {
    "A_M5":  dict(sufiks="_m5",  baar_min=5,  nimi="RADA A  M5"),
    "B_M15": dict(sufiks="_m15", baar_min=15, nimi="RADA B  M15"),
    "C_H1":  dict(sufiks="_h1",  baar_min=60, nimi="RADA C  H1"),
}


# ---------------------------------------------------------------- ANDMED --
def lae(sym, sufiks):
    p = os.path.join(DATA, f"{sym}{sufiks}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    d = d[["open", "high", "low", "close"]].apply(pd.to_numeric,
                                                  errors="coerce").dropna()
    return d if len(d) > 200 else None


def hinnad(sufiks):
    return {s: d for s in sorted(set(p for p, _ in KAART.values()))
            for d in [lae(s, sufiks)] if d is not None}


def valim(tier="T1"):
    """z arvutatakse KOGU kalendri peal (T1+T2) nagu B1-s, siis filter."""
    d = C.z_ullatus(C.lae_kalender(("T1", "T2")))
    d = d[d["z"].notna()].copy()
    d["algne_idx"] = d.index
    if tier:
        d = d[d["tier"] == tier].copy()
    d["suund_val"] = np.sign(d["z"]) * d["mark"]      # +1 = OSTA VALUUTA
    d["paar"] = d["cur"].map(lambda c: KAART[c][0])
    d["baas"] = d["cur"].map(lambda c: KAART[c][1])
    # positsioon PAARIS: +1 osta paar, -1 muu paar
    d["suund"] = np.where(d["baas"], d["suund_val"], -d["suund_val"]).astype(int)
    d["kulu_1suund_bp"] = d["paar"].map(KULU_1SUUND)
    return d.sort_values("ts").reset_index(drop=True)


# --------------------------------------------------------------- AJASTUS --
def pos_parast(idx, baar_min, sihid):
    """
    Esimene baar, mille SULGEMINE (label + baar_min) on RANGELT PARAST sihti.

    MIKS RANGELT. Makroteated tulevad kellaaegadel :00 :15 :30 :45, mis
    langevad TAPSELT kokku M5/M15/H1 baaride sulgemistega. Kell 12:30
    valjalaske korral sulgeb baar 12:25-12:30 tapselt valjalaske hetkel ja
    on TERVIKUNA teate-EELNE. Selle sulgemishinnaga sisenemine oleks
    lookahead: kaupleksime teate-eelse hinnaga, teades juba teadet.
    Eeltulemuste audit E1 leidis selle (koigi sundmuste viivitus oli 0.0
    minutit). Range vordlus tahendab, et 12:30 teade siseneb baari
    12:30-12:35 sulgemisel, st 5 minutit hiljem. See on taidetav.

    Tagastab -1, kui sellist baari ei ole.
    """
    sulg = (np.asarray(idx.values, dtype="datetime64[ns]")
            + np.timedelta64(int(baar_min), "m"))
    s = np.asarray(sihid, dtype="datetime64[ns]")
    pos = np.searchsorted(sulg, s, side="right")
    return np.where(pos < len(sulg), pos, -1)


def tehingud(d, H, baar_min, viivitus_min, hoid_min, max_lunk_min=None):
    """
    Uks rida = uks sundmus.
      sisse  esimene baari SULGEMINE >= T + viivitus_min
      valja  esimene baari SULGEMINE >= (sisenemise sulgemine) + hoid_min
    max_lunk_min: kui sisenemine on hilisem kui T + viivitus + max_lunk,
      jaetakse sundmus VALJA (nadalavahetus, andmeauk). Vaikimisi 2 baari.
    """
    if max_lunk_min is None:
        max_lunk_min = 2 * baar_min
    read = []
    for paar, x in d.groupby("paar"):
        P = H.get(paar)
        if P is None:
            continue
        idx = P.index
        sulg = pd.DatetimeIndex(idx) + pd.Timedelta(minutes=baar_min)
        siht = pd.DatetimeIndex(x["ts"]) + pd.Timedelta(minutes=viivitus_min)
        pin = pos_parast(idx, baar_min, siht.values)
        for k, (_, r) in enumerate(x.iterrows()):
            i = int(pin[k])
            if i < 0:
                continue
            t_in = sulg[i]
            if (t_in - siht[k]).total_seconds() / 60.0 > max_lunk_min:
                continue                        # lunk, EI ASENDATA proksiga
            siht_out = t_in + pd.Timedelta(minutes=hoid_min)
            j = int(pos_parast(idx, baar_min,
                               np.array([siht_out.to_datetime64()]))[0])
            if j < 0 or j <= i:
                continue
            t_out = sulg[j]
            if (t_out - siht_out).total_seconds() / 60.0 > max_lunk_min:
                continue
            p_in = float(P["close"].iloc[i])
            p_out = float(P["close"].iloc[j])
            if not (np.isfinite(p_in) and np.isfinite(p_out)
                    and p_in > 0 and p_out > 0):
                continue
            read.append((r["algne_idx"], r["cur"], r["indicator"], r["ts"],
                         paar, int(r["suund"]), float(r["z"]),
                         t_in, t_out, p_in, p_out,
                         float(r["kulu_1suund_bp"]),
                         int(r["suund"]) * math.log(p_out / p_in),
                         (t_in - pd.Timestamp(r["ts"])).total_seconds() / 60.0,
                         (t_out - t_in).total_seconds() / 60.0))
    T = pd.DataFrame(read, columns=[
        "algne_idx", "cur", "indicator", "ts", "paar", "suund", "z",
        "sisse_aeg", "valja_aeg", "p_in", "p_out", "kulu_1suund_bp",
        "bruto", "viivitus_tegelik_min", "hoid_tegelik_min"])
    if len(T):
        T["kulu"] = 2.0 * T["kulu_1suund_bp"] / 1e4
        T["neto"] = T["bruto"] - T["kulu"]
    return T.sort_values("ts").reset_index(drop=True)


def liikumine(d, H, baar_min, minutid):
    """
    KIRJELDAV: |tootlus| valjalaskest kuni T + m minutit, MARGITA.
    Motmiseks, kui suur osa 60-minutilisest liikumisest toimub varem.
    Ankur = viimane sulgemine <= T (valjalaske-eelne hind).
    """
    out = {}
    for paar, x in d.groupby("paar"):
        P = H.get(paar)
        if P is None:
            continue
        idx = P.index
        sulg = np.asarray(idx.values, dtype="datetime64[ns]") + \
            np.timedelta64(int(baar_min), "m")
        ts = np.asarray(pd.DatetimeIndex(x["ts"]).values, dtype="datetime64[ns]")
        # ankur = viimane sulgemine <= T (teate-EELNE hind; siin on
        # vordsus LUBATUD, sest see on just see hind, mida tahame)
        a = np.searchsorted(sulg, ts, side="right") - 1
        for k, ii in enumerate(a):
            if ii < 0:
                continue
            p0 = float(P["close"].iloc[ii])
            rida = {}
            for m in minutid:
                j = int(pos_parast(idx, baar_min,
                                   np.array([ts[k] + np.timedelta64(m, "m")]))[0])
                rida[m] = (math.log(float(P["close"].iloc[j]) / p0)
                           if j >= 0 and p0 > 0 else np.nan)
            out[(paar, x["ts"].iloc[k], k)] = rida
    return pd.DataFrame(out).T


# ------------------------------------------------------------ STATISTIKA --
def moot(T, libisemine_bp=0.0, veerg="bruto"):
    if T is None or len(T) < 5:
        return None
    x = T[veerg].values.astype(float)
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return None
    kulu = float(np.mean(T["kulu"].values)) if "kulu" in T else 0.0
    lib = libisemine_bp / 1e4
    sd = x.std(ddof=1) if len(x) > 1 else 0.0
    v, k = x[x > 0], x[x <= 0]
    t = float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0
    return dict(n=len(x), bruto_bp=1e4 * float(x.mean()),
                med_bp=1e4 * float(np.median(x)),
                wr=100.0 * float((x > 0).mean()),
                v_bp=1e4 * float(v.mean()) if len(v) else 0.0,
                k_bp=1e4 * float(k.mean()) if len(k) else 0.0,
                pf=(float(v.sum() / abs(k.sum())) if len(k) and k.sum() != 0
                    else np.inf),
                sd_bp=1e4 * float(sd), t=t, p=C.p_kahepoolne(t),
                kulu_bp=1e4 * kulu, lib_bp=libisemine_bp,
                neto_bp=1e4 * (float(x.mean()) - kulu - lib),
                murdepunkt_bp=1e4 * float(x.mean()))


def juhuslik_baas(T, seeme=SEEME, katseid=N_BOOT):
    """
    PAARITATUD juhuslik suund: samad sundmused, sama sisenemine ja
    valjumine, AINULT suund juhuslik. Tagastab (jaotus, p).
    Jarjekorra permutatsiooni EI KASUTATA (fikseeritud protsendiriski
    korral on see matemaatiliselt sisutu).
    """
    rs = np.random.RandomState(seeme)
    alus = (T["bruto"] / T["suund"]).values.astype(float)
    alus = alus[np.isfinite(alus)]
    teg = float(np.mean(T["bruto"].values))
    jaot = np.array([float(np.mean(rs.choice([-1.0, 1.0], size=len(alus)) * alus))
                     for _ in range(katseid)])
    return jaot, float((jaot >= teg).mean())


def bootstrap_ci(x, seeme=SEEME, katseid=N_BOOT, q=(2.5, 97.5)):
    rs = np.random.RandomState(seeme)
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 5:
        return (np.nan, np.nan)
    m = np.array([x[rs.randint(0, len(x), len(x))].mean() for _ in range(katseid)])
    return (1e4 * float(np.percentile(m, q[0])),
            1e4 * float(np.percentile(m, q[1])))


PAIS = (f"{'test':<30s}{'n':>6s}{'bruto':>9s}{'med':>8s}{'kulu':>7s}"
        f"{'lib':>6s}{'neto':>8s}{'wr%':>7s}{'t':>7s}{'p':>8s}")


def rida(nimi, m, w=30):
    if m is None:
        return f"{nimi:<{w}s}   (alla 5 sundmuse voi DATA INSUFFICIENT)"
    return (f"{nimi:<{w}s}{m['n']:>6d}{m['bruto_bp']:>+9.2f}{m['med_bp']:>+8.2f}"
            f"{m['kulu_bp']:>7.2f}{m['lib_bp']:>6.1f}{m['neto_bp']:>+8.2f}"
            f"{m['wr']:>7.1f}{m['t']:>7.2f}{m['p']:>8.3f}")
