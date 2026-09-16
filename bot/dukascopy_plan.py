"""
dukascopy_plan.py — EELREGISTREERITUD paeva- ja tunnivalik tick-allalaadimiseks.

SEE EI OLE STRATEEGIATEST. Siin ei arvutata uhtegi tootlust.

VALIKUREEGEL (fikseeritud ENNE allalaadimist, ei soltu tulemustest):

  1. Kandidaatpaevad = paevad, millel on vahemalt uks TIER 1 kalendrisundmus,
     mille |z| >= 1 JA mille valuuta on kaardistatav 7 major-paari peale
     (cal_imm.KAART).
  2. Paevad votetakse POORD-KRONOLOOGILISES jarjekorras koige varskemast.
     Ei mingit valikut "kus tulemus ilusam".
  3. PEATUMINE: niipea kui kumulatiivne TIER 1 |z|>=1 sundmuste arv >= SIHT,
     paevade nimekiri loppeb.
  4. Tunnid: iga valitud paeva kohta voetakse KOIGI selle paeva TIER 1
     sundmuste (ka |z| < 1 — need on kontrollgrupp) tundide umbrus
     {h-1, h, h+1}, loigatud vahemikku [0, 23], liidetud uheks komplektiks.
     Kontrollgrupp voetakse kaasa SIIN, mitte hiljem, et hilisem test ei
     saaks kontrollgruppi tagantjarele valida.
  5. Sumbolid: koik 7 majorit, iga paeva kohta samad. Ei valita sumbolit
     sundmuse jargi.
"""
import datetime as dt
import json
import os
import sys

import pandas as pd

import cal_engine as C
import cal_imm as I

SIHT = 30                       # peatumislavi: TIER 1 |z|>=1 sundmusi
UMBRUS_H = 1                    # +-1 tund ymber release'i
SUMBOLID = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF",
            "AUDUSD", "USDCAD", "NZDUSD"]
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def kalender():
    d = C.z_ullatus(C.lae_kalender(("T1", "T2")))
    d = d[d["z"].notna()].copy()
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    d["paar"] = d["cur"].map(lambda c: I.KAART[c][0] if c in I.KAART else None)
    return d[d["paar"].notna()].copy()


def plaan(siht=SIHT):
    d = kalender()
    t1 = d[d["tier"] == "T1"].copy()
    t1["paev"] = t1["ts"].dt.date

    kand = t1[t1["z"].abs() >= 1]
    paevad_kahanevalt = sorted(kand["paev"].unique(), reverse=True)

    valitud, kumul = [], 0
    for p in paevad_kahanevalt:
        n = int((kand["paev"] == p).sum())
        valitud.append((p, n))
        kumul += n
        if kumul >= siht:
            break

    read = []
    for p, n in valitud:
        sel = t1[t1["paev"] == p]
        tunnid = set()
        for h in sel["ts"].dt.hour.tolist():
            for o in range(-UMBRUS_H, UMBRUS_H + 1):
                v = h + o
                if 0 <= v <= 23:
                    tunnid.add(v)
        read.append(dict(paev=str(p), n_z1=n, n_t1_koik=len(sel),
                         tunnid=sorted(tunnid)))
    read.sort(key=lambda r: r["paev"])
    return read, kumul


if __name__ == "__main__":
    read, kumul = plaan()
    print("=" * 96)
    print("EELREGISTREERITUD ALLALAADIMISPLAAN — Dukascopy tick")
    print("=" * 96)
    print(f"  siht: >= {SIHT} TIER 1 |z|>=1 sundmust")
    print(f"  paevi: {len(read)}   kaetud T1 |z|>=1 sundmusi: {kumul}")
    print(f"  sumboleid: {len(SUMBOLID)}  ({', '.join(SUMBOLID)})")
    print()
    print(f"{'paev':<13s}{'|z|>=1':>7s}{'T1 koik':>9s}{'tunde':>7s}  tunnid UTC")
    tunde_kokku = 0
    for r in read:
        tunde_kokku += len(r["tunnid"])
        print(f"{r['paev']:<13s}{r['n_z1']:>7d}{r['n_t1_koik']:>9d}"
              f"{len(r['tunnid']):>7d}  "
              f"{','.join(str(t) for t in r['tunnid'])}")
    print()
    print(f"  sumbol-tunde kokku: {tunde_kokku * len(SUMBOLID)} "
          f"({tunde_kokku} tundi x {len(SUMBOLID)} sumbolit)")
    print(f"  vordluseks tais 24h: {len(read) * 24 * len(SUMBOLID)}")

    out = os.path.join(JUUR, "SUB60_TICK_PLAAN.csv")
    with open(out, "w", encoding="utf-8") as f:
        f.write("paev,n_t1_z1,n_t1_koik,tunnid\n")
        for r in read:
            f.write(f"{r['paev']},{r['n_z1']},{r['n_t1_koik']},"
                    f"\"{' '.join(str(t) for t in r['tunnid'])}\"\n")
    print(f"  kirjutatud: {out}")

    sql = os.path.join(JUUR, "SUB60_TICK_PLAAN.json")
    json.dump(dict(siht=SIHT, umbrus_h=UMBRUS_H, sumbolid=SUMBOLID,
                   kumul=kumul, paevad=read),
              open(sql, "w", encoding="utf-8"), indent=1)
    print(f"  kirjutatud: {sql}")
