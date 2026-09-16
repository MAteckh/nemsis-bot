"""
dukascopy_coverage.py — KAS tickid on olemas Economic Calendar release'i umber?

SEE EI OLE STRATEEGIATEST. P/L-i EI ARVUTATA. Kontrollitakse AINULT
ANDMEKATVUST: kas release'i hetke umber 0-60 sekundi aknas on tick'e.
"""
import datetime as dt
import glob
import os

import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I
import dukascopy_bi5 as B

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TICKS = os.path.join(DATA, "dukascopy", "ticks")
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# eelregistreeritud aknad sekundites
AKNAD = [-10, -5, -1, 0, 1, 3, 5, 10, 30, 60]


def lae_tikid(paev):
    out = {}
    for f in sorted(glob.glob(os.path.join(TICKS, f"*_{paev}_ticks.csv"))):
        sym = os.path.basename(f).split("_")[0]
        d = pd.read_csv(f, parse_dates=["ts_utc"])
        d["ts_utc"] = pd.to_datetime(d["ts_utc"], utc=True)
        out[sym] = d.sort_values("ts_utc").reset_index(drop=True)
    return out


if __name__ == "__main__":
    paev = "2026-09-03"
    T = lae_tikid(paev)
    print("=" * 108)
    print(f"ECONOMIC CALENDAR <-> TICK KATVUS — {paev}")
    print("=" * 108)
    print(f"  tick-sumboleid: {len(T)}  ({', '.join(sorted(T))})")
    print("  SEE EI OLE STRATEEGIATEST. Ainult katvus.")

    d = C.z_ullatus(C.lae_kalender(("T1", "T2")))
    d = d[d["z"].notna()].copy()
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    a = pd.Timestamp(f"{paev} 00:00:00", tz="UTC")
    b = pd.Timestamp(f"{paev} 23:59:59", tz="UTC")
    x = d[(d["ts"] >= a) & (d["ts"] <= b)].copy()
    x["paar"] = x["cur"].map(lambda c: I.KAART[c][0])
    x = x[x["paar"].isin(T)].sort_values("ts")
    print(f"  kalendrisundmusi sel paeval (kaardistatavad): {len(x)}")
    print(f"    neist TIER 1: {int((x['tier']=='T1').sum())}, "
          f"|z|>=1: {int((x['z'].abs()>=1).sum())}")

    read = []
    print()
    print(f"{'aeg UTC':<20s}{'val':<5s}{'paar':<8s}{'tier':<6s}{'z':>7s}"
          f"{'eelm tick':>11s}{'jargm tick':>12s}" +
          "".join(f"{f'+{s}s':>7s}" for s in AKNAD if s > 0))
    for _, r in x.iterrows():
        P = T[r["paar"]]
        ts = P["ts_utc"].values
        t0 = np.datetime64(r["ts"].tz_convert("UTC").tz_localize(None), "ns")
        i = np.searchsorted(ts, t0)
        eelm = ((t0 - ts[i - 1]) / np.timedelta64(1, "s")) if i > 0 else np.nan
        jargm = ((ts[i] - t0) / np.timedelta64(1, "s")) if i < len(ts) else np.nan
        loend = {}
        for s in AKNAD:
            if s <= 0:
                continue
            j = np.searchsorted(ts, t0 + np.timedelta64(s, "s"))
            loend[s] = int(j - i)
        print(f"{str(r['ts'])[:19]:<20s}{r['cur']:<5s}{r['paar']:<8s}"
              f"{r['tier']:<6s}{r['z']:>7.2f}"
              f"{eelm:>10.3f}s{jargm:>11.3f}s" +
              "".join(f"{loend[s]:>7d}" for s in AKNAD if s > 0))
        read.append(dict(ts_utc=str(r["ts"]), valuuta=r["cur"], paar=r["paar"],
                         indikaator=r["indicator"], tier=r["tier"],
                         z=float(r["z"]),
                         eelmine_tick_s=float(eelm), jargmine_tick_s=float(jargm),
                         **{f"tikke_{s}s": loend[s] for s in AKNAD if s > 0}))

    R = pd.DataFrame(read)
    R.to_csv(os.path.join(JUUR, "SUB60_TICK_COVERAGE.csv"), index=False)
    print()
    print("KOKKUVOTE")
    print(f"  sundmusi kontrollitud            {len(R)}")
    print(f"  tick olemas ENNE release'i       "
          f"{int((R['eelmine_tick_s'].notna()).sum())}/{len(R)}")
    print(f"  tick olemas PARAST release'i     "
          f"{int((R['jargmine_tick_s'].notna()).sum())}/{len(R)}")
    print(f"  mediaan lahim tick ENNE          "
          f"{R['eelmine_tick_s'].median():.3f} s")
    print(f"  mediaan lahim tick PARAST        "
          f"{R['jargmine_tick_s'].median():.3f} s")
    for s in AKNAD:
        if s <= 0:
            continue
        v = R[f"tikke_{s}s"]
        print(f"  tikke 0..+{s:<3d}s   mediaan {v.median():>7.0f}   "
              f"min {v.min():>5d}   aknaid ilma tickita {int((v==0).sum())}")
    print()
    print("  JARELDUS: kui 'jargmine tick' on sekundi murdosa kaugusel ja")
    print("  0..+1 s aknas on tick'e, siis SUB-60 execution test on")
    print("  ANDMETE MOTTES teostatav. See EI utle midagi serva kohta.")
