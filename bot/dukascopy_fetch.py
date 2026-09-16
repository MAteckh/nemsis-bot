"""
dukascopy_fetch.py — CLI allalaadija Dukascopy .bi5 tick-failidele.

UURIMISKOOD. Ei puuduta live-faile.

TAHTIS — KUS SEE TOOTAB JA KUS MITTE
------------------------------------
See skript teeb OTSESE HTTPS-paringu datafeed.dukascopy.com'ile.

  TOOTAB   kasutaja VPS-il, kodumasinal, GitHub Actionsis — igal pool,
           kus valjaminev HTTPS on lubatud.
  EI TOOTA selle uurimistoo liivakastis. Mooedetud, mitte eeldatud:
           egress-proxy keelab CONNECT-i KOIGILE valishostidele
           organisatsiooni poliitikaga.
             curl -> HTTP 000, "CONNECT tunnel failed, response 403"
             agent-proxy teade: "connect_rejected (the egress proxy denied
             the CONNECT (organization policy))"
           Sama kehtis ka query1.finance.yahoo.com kohta, seega tegu ei
           ole Dukascopy-spetsiifilise blokiga.

  Liivakastis kasutatakse selle asemel Supabase Edge Functionit
  'dukascopy-bi5' + SQL-funktsioone fetch_bi5 / fetch_bi5_day /
  fetch_bi5_range, ja andmed tuuakse siia dukascopy_ingest.py-ga.
  Vt KOKKUVOTE_DUKASCOPY_TICK_PIPELINE.md.

KASUTUS
    python3 dukascopy_fetch.py --symbol EURUSD --date 2026-09-03
    python3 dukascopy_fetch.py \\
        --symbols EURUSD,GBPUSD,USDJPY,USDCHF,AUDUSD,USDCAD,NZDUSD \\
        --start 2026-09-01 --end 2026-09-07 --out data/dukascopy/bi5

OMADUSED (nouded 13 ja 11)
    - olemasolevate failide tuvastus: juba alla laetud tunde ei lae uuesti
    - retry eksponentsiaalse backoffiga (429/5xx/vorguviga)
    - rate limit: --sleep sekundit iga faili jarel, --conc samaaegsust
    - failinud failid loendisse, resume jargmisel jooksul
    - iga faili kohta salvestatakse sha256 ja suurus (audit)
"""
import argparse
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request

import dukascopy_bi5 as B

RETRIES = 4
BASE_DELAY = 0.4


def tee(kaust, symbol, paev, tund):
    return os.path.join(kaust, symbol, f"{paev:%Y}", f"{paev:%m}",
                        f"{paev:%d}", f"{tund:02d}h_ticks.bi5")


def lae_uks(symbol, paev, tund, kaust, sleep_s):
    p = tee(kaust, symbol, paev, tund)
    if os.path.exists(p):
        return dict(symbol=symbol, paev=str(paev), tund=tund, staatus="olemas",
                    baite=os.path.getsize(p), katseid=0)
    u = B.url(symbol, paev, tund)
    viimane = ""
    for katse in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(u, headers={
                "User-Agent": "Mozilla/5.0", "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=30) as r:
                blob = r.read()
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as f:
                f.write(blob)
            if sleep_s:
                time.sleep(sleep_s)
            return dict(symbol=symbol, paev=str(paev), tund=tund, staatus="ok",
                        baite=len(blob), katseid=katse,
                        sha256=hashlib.sha256(blob).hexdigest(), url=u)
        except urllib.error.HTTPError as e:
            viimane = f"HTTP {e.code}"
            if e.code == 404:                       # tunnil pole tick'e
                return dict(symbol=symbol, paev=str(paev), tund=tund,
                            staatus="tuhi404", baite=0, katseid=katse, url=u)
            if e.code != 429 and e.code < 500:
                return dict(symbol=symbol, paev=str(paev), tund=tund,
                            staatus=f"viga {e.code}", baite=0,
                            katseid=katse, url=u)
        except Exception as e:                      # vorguviga, timeout
            viimane = str(e)
        if katse < RETRIES:
            time.sleep(BASE_DELAY * (2 ** (katse - 1)) + random.random() * 0.2)
    return dict(symbol=symbol, paev=str(paev), tund=tund,
                staatus=f"ebaonnestus: {viimane}", baite=0,
                katseid=RETRIES, url=u)


def main():
    ap = argparse.ArgumentParser(description="Dukascopy .bi5 allalaadija")
    ap.add_argument("--symbol")
    ap.add_argument("--symbols")
    ap.add_argument("--date")
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--out", default="data/dukascopy/bi5")
    ap.add_argument("--conc", type=int, default=4,
                    help="samaaegseid paringuid (vaikimisi 4; allikas "
                         "annab 503, kui neid on liiga palju)")
    ap.add_argument("--sleep", type=float, default=0.15,
                    help="paus sekundites iga oonnestunud faili jarel")
    a = ap.parse_args()

    sums = ([s.strip().upper() for s in a.symbols.split(",")] if a.symbols
            else [a.symbol.upper()] if a.symbol else None)
    if not sums:
        ap.error("vaja --symbol voi --symbols")
    for s in sums:
        B.digits(s)                                  # tundmatu sumbol -> viga

    if a.date:
        paevad = [dt.date.fromisoformat(a.date)]
    elif a.start and a.end:
        p0, p1 = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
        paevad = [p0 + dt.timedelta(days=i) for i in range((p1 - p0).days + 1)]
    else:
        ap.error("vaja --date voi --start ja --end")

    too = [(s, p, h) for s in sums for p in paevad for h in range(24)]
    print(f"faile kokku {len(too)}  sumboleid {len(sums)}  "
          f"paevi {len(paevad)}  samaaegsus {a.conc}")

    read = []
    with cf.ThreadPoolExecutor(max_workers=a.conc) as ex:
        futs = {ex.submit(lae_uks, s, p, h, a.out, a.sleep): (s, p, h)
                for s, p, h in too}
        for i, f in enumerate(cf.as_completed(futs), 1):
            r = f.result()
            read.append(r)
            if i % 25 == 0 or i == len(too):
                ok = sum(1 for x in read if x["staatus"] in ("ok", "olemas"))
                print(f"  {i}/{len(too)}  korras {ok}  "
                      f"baite {sum(x['baite'] for x in read):,}")

    vead = [r for r in read if r["staatus"].startswith(("viga", "ebaonnestus"))]
    log = os.path.join(a.out, "_manifest.jsonl")
    os.makedirs(a.out, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        for r in sorted(read, key=lambda x: (x["symbol"], x["paev"], x["tund"])):
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\nok {sum(1 for r in read if r['staatus']=='ok')}  "
          f"olemas {sum(1 for r in read if r['staatus']=='olemas')}  "
          f"tuhi404 {sum(1 for r in read if r['staatus']=='tuhi404')}  "
          f"vigu {len(vead)}")
    print(f"manifest: {log}")
    if vead:
        print("EBAONNESTUNUD (jargmine jooks proovib uuesti):")
        for r in vead[:10]:
            print(f"  {r['symbol']} {r['paev']} {r['tund']:02d}h  {r['staatus']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
