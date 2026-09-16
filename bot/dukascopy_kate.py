"""
dukascopy_kate.py — mitme paeva kalendri<->tick KATVUS.

SEE EI OLE STRATEEGIATEST. P/L-i EI ARVUTATA, signaali ei genereerita.
Kontrollitakse AINULT, kas release'i hetke umber on paris bid/ask tick'e.

Erinevus dukascopy_coverage.py-st: see kaib labi KOIK allalaetud paevad
ja loeb kokku, mitu eelregistreeritud TIER 1 |z|>=1 sundmust on KAETUD.
Kaetuse kriteerium on fikseeritud ENNE andmete vaatamist (vt KRIT_*).
"""
import glob
import os

import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TICKS = os.path.join(DATA, "dukascopy", "ticks")
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# eelregistreeritud aknad sekundites (sama nimekiri mis pilootjooksul)
AKNAD = [-10, -5, -1, 0, 1, 3, 5, 10, 30, 60]

# KAETUSE KRITEERIUM — fikseeritud enne tulemuste vaatamist:
KRIT_EEL_S = 60.0      # viimane tick enne release'i mitte vanem kui 60 s
KRIT_JARG_S = 5.0      # esimene tick parast release'i mitte kaugemal kui 5 s
KRIT_MIN_TIKKE = 1     # aknas 0..+60 s vahemalt uks tick


def lae_tikid():
    """{(symbol, paev): DataFrame}"""
    out = {}
    for f in sorted(glob.glob(os.path.join(TICKS, "*_ticks.csv"))):
        b = os.path.basename(f)[:-len("_ticks.csv")]
        sym, paev = b.split("_")
        d = pd.read_csv(f)
        d["ts_utc"] = pd.to_datetime(d["ts_utc"], utc=True)
        out[(sym, paev)] = d.sort_values("ts_utc").reset_index(drop=True)
    return out


def sundmused():
    d = C.z_ullatus(C.lae_kalender(("T1", "T2")))
    d = d[d["z"].notna()].copy()
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d["paar"] = d["cur"].map(lambda c: I.KAART[c][0] if c in I.KAART else None)
    return d[d["paar"].notna()].copy()


def katvus(T, x):
    read = []
    for _, r in x.iterrows():
        paev = str(r["ts"].date())
        P = T.get((r["paar"], paev))
        rida = dict(ts_utc=str(r["ts"])[:19], valuuta=r["cur"], paar=r["paar"],
                    indikaator=r["indicator"], tier=r["tier"],
                    z=round(float(r["z"]), 3))
        if P is None or len(P) == 0:
            rida.update(tikke_paeval=0, eel_s=np.nan, jarg_s=np.nan,
                        kaetud=False, pohjus="tick-faili pole")
            read.append(rida)
            continue

        ts = P["ts_utc"].values
        t0 = np.datetime64(r["ts"].tz_convert("UTC").tz_localize(None), "ns")
        i = int(np.searchsorted(ts, t0))
        eel = ((t0 - ts[i - 1]) / np.timedelta64(1, "s")) if i > 0 else np.nan
        jarg = ((ts[i] - t0) / np.timedelta64(1, "s")) if i < len(ts) else np.nan
        for s in AKNAD:
            j = int(np.searchsorted(ts, t0 + np.timedelta64(s, "s")))
            rida[f"n_{s}s"] = j - i
        n60 = rida["n_60s"]
        ok = (pd.notna(eel) and eel <= KRIT_EEL_S
              and pd.notna(jarg) and jarg <= KRIT_JARG_S
              and n60 >= KRIT_MIN_TIKKE)
        pohjus = ""
        if not ok:
            if pd.isna(eel) or eel > KRIT_EEL_S:
                pohjus = "eelnev tick puudub/liiga vana"
            elif pd.isna(jarg) or jarg > KRIT_JARG_S:
                pohjus = "jargmine tick liiga kaugel"
            else:
                pohjus = "aknas 0..+60 s pole tick'e"
        rida.update(tikke_paeval=len(P),
                    eel_s=round(float(eel), 3) if pd.notna(eel) else np.nan,
                    jarg_s=round(float(jarg), 3) if pd.notna(jarg) else np.nan,
                    kaetud=bool(ok), pohjus=pohjus)
        read.append(rida)
    return pd.DataFrame(read)


if __name__ == "__main__":
    T = lae_tikid()
    paevad = sorted({p for _, p in T})
    d = sundmused()
    x = d[(d["tier"] == "T1") & (d["z"].abs() >= 1)].copy()
    x = x[x["ts"].dt.date.astype(str).isin(paevad)].sort_values("ts")

    K = katvus(T, x)
    n_ok = int(K["kaetud"].sum())

    print("=" * 112)
    print("DUKASCOPY TICK <-> ECONOMIC CALENDAR KATVUS")
    print("=" * 112)
    print("  SEE EI OLE STRATEEGIATEST. Ainult andmekatvus.")
    print(f"  tick-faile (sumbol x paev): {len(T)}   paevi: {len(paevad)}")
    print(f"  tikke kokku: {sum(len(v) for v in T.values()):,}")
    print(f"  kriteerium: eelmine tick <= {KRIT_EEL_S:.0f}s, "
          f"jargmine <= {KRIT_JARG_S:.0f}s, aknas 0..+60s >= {KRIT_MIN_TIKKE}")
    print()
    print(f"  TIER 1 |z|>=1 sundmusi neil paevadel: {len(x)}")
    print(f"  NEIST KAETUD: {n_ok}")
    print()

    v = [c for c in ("1", "3", "5", "10", "30", "60")]
    hdr = (f"{'aeg UTC':<20s}{'paar':<8s}{'z':>7s}{'eel s':>9s}{'jarg s':>9s}"
           + "".join(f"{'+'+s+'s':>7s}" for s in v) + "  kaetud")
    print(hdr)
    for _, r in K.iterrows():
        print(f"{r['ts_utc']:<20s}{r['paar']:<8s}{r['z']:>7.2f}"
              f"{r['eel_s']:>9.3f}{r['jarg_s']:>9.3f}"
              + "".join(f"{int(r['n_'+s+'s']):>7d}" for s in v)
              + ("  JAH" if r["kaetud"] else f"  EI ({r['pohjus']})"))

    out = os.path.join(JUUR, "SUB60_TICK_COVERAGE.csv")
    K.to_csv(out, index=False)
    print()
    print(f"  kirjutatud: {out}")

    R = []
    for (sym, paev), P in sorted(T.items()):
        sp = (P["ask"] - P["bid"])
        R.append(dict(symbol=sym, paev=paev, tikke=len(P),
                      algus=str(P["ts_utc"].iloc[0])[:19],
                      lopp=str(P["ts_utc"].iloc[-1])[:19],
                      spread_med=round(float(sp.median()), 6),
                      spread_min=round(float(sp.min()), 6),
                      neg_spread=int((sp < 0).sum()),
                      bid_max_0=int((P["bid"] <= 0).sum()),
                      ask_max_0=int((P["ask"] <= 0).sum())))
    D = pd.DataFrame(R)
    out2 = os.path.join(JUUR, "SUB60_TICK_DATASET.csv")
    D.to_csv(out2, index=False)
    print(f"  kirjutatud: {out2}")
    print()
    print(f"  KVALITEET: negatiivseid spread'e {int(D['neg_spread'].sum())}, "
          f"bid<=0 {int(D['bid_max_0'].sum())}, ask<=0 {int(D['ask_max_0'].sum())}")
