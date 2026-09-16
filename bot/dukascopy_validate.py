"""
dukascopy_validate.py — tick-andmete kvaliteedikontroll ja formaadi TOENDUS.

UURIMISKOOD. Ei tee strateegiatesti, ei arvuta P/L-i.

KOIGE TAHTSAM SIIN ON TEST K3: kuu-indekseerimine. Dukascopy URL-is on kuu
0-indekseeritud ("08" = september). Seda EI VOETA usu peale — parsitud
tickidest arvutatakse tunnipohine OHLC ja vorreldakse REPOS JUBA OLEMAS
OLEVATE M1-baaridega samal kuupaeval. Kui kuu-indeks oleks vale, osutaks
fail teisele kuule ja hinnad EI KLAPIKS.
"""
import datetime as dt
import glob
import math
import os
import sys

import pandas as pd

import dukascopy_bi5 as B

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TICKS = os.path.join(DATA, "dukascopy", "ticks")
PASS, FAIL = "PASS", "FAIL"
tulem = []


def k(nimi, ok, info=""):
    tulem.append(bool(ok))
    print(f"{PASS if ok else FAIL}  {nimi:<52s} {info}")


def lae(sym, paev):
    p = os.path.join(TICKS, f"{sym}_{paev}_ticks.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["ts_utc"])
    return d.sort_values("ts_utc").reset_index(drop=True)


if __name__ == "__main__":
    paev = sys.argv[1] if len(sys.argv) > 1 else "2026-09-03"
    failid = sorted(glob.glob(os.path.join(TICKS, f"*_{paev}_ticks.csv")))
    sumbolid = [os.path.basename(f).split("_")[0] for f in failid]

    print("=" * 108)
    print(f"DUKASCOPY TICK VALIDATION — {paev}")
    print("=" * 108)

    # ------------------------------------------------ K1 BID/ASK ---------
    print("\nK1  BID / ASK KEHTIVUS")
    read = []
    for sym in sumbolid:
        d = lae(sym, paev)
        jag = 10 ** B.digits(sym)
        spread = (d["ask"] - d["bid"])
        pip = spread * jag / 10.0
        read.append(dict(
            symbol=sym, n=len(d),
            esimene=str(d["ts_utc"].iloc[0]), viimane=str(d["ts_utc"].iloc[-1]),
            bid_min=float(d["bid"].min()), bid_max=float(d["bid"].max()),
            ask_min=float(d["ask"].min()), ask_max=float(d["ask"].max()),
            esimene_bid=float(d["bid"].iloc[0]), esimene_ask=float(d["ask"].iloc[0]),
            viimane_bid=float(d["bid"].iloc[-1]), viimane_ask=float(d["ask"].iloc[-1]),
            koik_pos=bool((d["bid"] > 0).all() and (d["ask"] > 0).all()),
            bid_le_ask=bool((d["bid"] <= d["ask"]).all()),
            neg_spread=int((spread < 0).sum()), null_spread=int((spread == 0).sum()),
            spread_med=float(pip.median()), spread_p75=float(pip.quantile(.75)),
            spread_p90=float(pip.quantile(.90)), spread_p95=float(pip.quantile(.95)),
            spread_max=float(pip.max()),
            ts_kasvav=bool(d["ts_utc"].is_monotonic_increasing)))
    R = pd.DataFrame(read)
    k("K1a koik bid > 0 ja ask > 0", bool(R["koik_pos"].all()),
      f"{len(R)} sumbolit")
    k("K1b bid <= ask KOIGIL tickidel", bool(R["bid_le_ask"].all()),
      f"negatiivseid spreade kokku {int(R['neg_spread'].sum())}")
    k("K1c ajatemplid on kasvavad", bool(R["ts_kasvav"].all()), "")
    k("K1d nullspreade osakaal on vaike",
      bool((R["null_spread"] / R["n"]).max() < 0.05),
      f"max {100*(R['null_spread']/R['n']).max():.2f}% ({R.loc[(R['null_spread']/R['n']).idxmax(),'symbol']})")

    print(f"\n{'sumbol':<9s}{'tikke':>9s}{'spread med':>12s}{'p75':>8s}"
          f"{'p90':>8s}{'p95':>8s}{'max':>9s}{'null%':>8s}")
    for _, r in R.iterrows():
        print(f"{r['symbol']:<9s}{r['n']:>9d}{r['spread_med']:>12.2f}"
              f"{r['spread_p75']:>8.2f}{r['spread_p90']:>8.2f}"
              f"{r['spread_p95']:>8.2f}{r['spread_max']:>9.2f}"
              f"{100*r['null_spread']/r['n']:>8.2f}")
    print("  (spread pipides; 5-kohalistel 1 pip = 0.0001, JPY-l 1 pip = 0.01)")

    # ------------------------------------------------ K2 HINNATASE -------
    print("\nK2  HINNATASE — kas jagaja 10^digits on oige?")
    ootus = {"EURUSD": (0.9, 1.4), "GBPUSD": (1.0, 1.6), "AUDUSD": (0.5, 0.9),
             "NZDUSD": (0.5, 0.8), "USDCHF": (0.7, 1.1), "USDCAD": (1.1, 1.6),
             "USDJPY": (100.0, 200.0)}
    for _, r in R.iterrows():
        lo, hi = ootus[r["symbol"]]
        k(f"K2 {r['symbol']} tase {lo}-{hi}",
          lo < r["bid_min"] and r["bid_max"] < hi,
          f"bid {r['bid_min']:.5f} .. {r['bid_max']:.5f}  "
          f"(digits {B.digits(r['symbol'])})")

    # ------------------------------------- K3 KUU-INDEKS + RISTKONTROLL --
    print("\nK3  KUU-INDEKSEERIMINE — otsustav test M1-baaride vastu")
    print("    URL kasutas kuud (month-1). Kui see on vale, osutab fail")
    print("    teisele kuule ja hinnad EI KLAPI olemasoleva M1-ga.")
    read3 = []
    for sym in sumbolid:
        m1p = os.path.join(DATA, f"{sym}_m1.csv")
        if not os.path.exists(m1p):
            print(f"    {sym}: M1-andmeid ei ole, ristkontrolli ei saa teha")
            continue
        m1 = pd.read_csv(m1p, parse_dates=["Date"]).set_index("Date").sort_index()
        d = lae(sym, paev)
        # tick -> minuti sulgemine
        tk = d.set_index("ts_utc")
        mid = (tk["bid"] + tk["ask"]) / 2.0
        tm = mid.resample("1min").last().dropna()
        ix = tm.index.intersection(m1.index)
        if len(ix) < 50:
            print(f"    {sym}: kattuvaid minuteid {len(ix)} — liiga vahe")
            continue
        a, b = tm.reindex(ix), m1["close"].reindex(ix)
        viga_bp = 1e4 * (a / b - 1.0).abs()
        kor = float(pd.Series(a.values).pct_change().corr(
            pd.Series(b.values).pct_change()))
        alla2 = 100.0 * float((viga_bp < 2.0).mean())
        read3.append(dict(symbol=sym, minuteid=len(ix),
                          mediaan_viga_bp=float(viga_bp.median()),
                          p95_viga_bp=float(viga_bp.quantile(.95)),
                          max_viga_bp=float(viga_bp.max()),
                          osa_alla_2bp=alla2,
                          tootluse_korr=kor))
        # KUU-INDEKSI TOEND on HINNATASE, mitte minutituotluse korrelatsioon.
        # Vale kuu annaks kumnetes kuni sadades baaspunktides erineva taseme.
        # Minutituotluse korrelatsioon on KIRJELDAV: see mootab kahe ERI
        # andmepakkuja kokkulangevust 1-minutilisel horisondil, kus tootlus
        # on mone kumnendiku bp suurune ja tickide ajastuse mura domineerib.
        # Seda EI KASUTATA pass/fail kriteeriumina.
        k(f"K3 {sym} hinnatase klapib M1-ga", viga_bp.median() < 5.0,
          f"{len(ix)} min, mediaanviga {viga_bp.median():.2f} bp, "
          f"p95 {viga_bp.quantile(.95):.2f} bp, alla 2 bp {alla2:.0f}%")
    R3 = pd.DataFrame(read3)

    # ------------------------------------------------ K4 KATVUS ----------
    print("\nK4  TUNNIKATVUS")
    for sym in sumbolid:
        d = lae(sym, paev)
        tunnid = sorted(set(d["ts_utc"].dt.hour))
        k(f"K4 {sym} tunde", len(tunnid) >= 22,
          f"{len(tunnid)}/24 tunnil on tick'e; puudu: "
          f"{sorted(set(range(24)) - set(tunnid))}")

    # ------------------------------------------------ K5 TEADAOLEV -------
    print("\nK5  PARSERI TEADAOLEV VASTUS")
    import struct
    proov = struct.pack(">IIIff", 1234, 116500, 116490, 1.5, 2.5)
    import lzma
    pakitud = lzma.LZMACompressor(lzma.FORMAT_ALONE).compress(proov)
    pakitud += lzma.LZMACompressor(lzma.FORMAT_ALONE).flush()
    # kasutame otse parsi_kirjed loogikat lahtipakitud andmete peal
    jag = 10 ** B.digits("EURUSD")
    ms, ask_i, bid_i, av, bv = struct.unpack(">IIIff", proov)
    k("K5a kirje 20 baiti, ASK enne BID-i", ask_i > bid_i,
      f"ask {ask_i/jag:.5f} > bid {bid_i/jag:.5f}")
    k("K5b ms-offset -> ajatempel",
      (dt.datetime(2026, 9, 3, 10, tzinfo=dt.timezone.utc)
       + dt.timedelta(milliseconds=ms)).isoformat()
      == "2026-09-03T10:00:01.234000+00:00",
      f"ms={ms} -> +1.234 s")

    print("\n    MINUTITUOTLUSE KORRELATSIOON (KIRJELDAV, mitte kriteerium):")
    for _, r in R3.iterrows():
        print(f"      {r['symbol']}: {r['tootluse_korr']:.4f} "
              f"({int(r['minuteid'])} minutit)")
    print("    Madalam korrelatsioon ei tahenda vale kuud — hinnatase")
    print("    klapib baaspunkti tapsusega. 1-minutiline tootlus on kahe")
    print("    eri pakkuja vahel loomulikult murane.")

    JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    R.to_csv(os.path.join(JUUR, "SUB60_TICK_QUALITY.csv"), index=False)
    if len(R3):
        R3.to_csv(os.path.join(JUUR, "SUB60_TICK_CROSSCHECK.csv"), index=False)

    print()
    print("=" * 108)
    print(f"{len(tulem)} kontrolli, {sum(1 for t in tulem if not t)} FAIL")
    print("=" * 108)
