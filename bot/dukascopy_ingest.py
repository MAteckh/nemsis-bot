"""
dukascopy_ingest.py — Supabase MCP tulemusefaili -> .bi5 failid -> tick-CSV.

UURIMISKOOD. Ei puuduta live-faile.

ARHITEKTUUR JA MIKS TA SELLINE ON
---------------------------------
Liivakastil EI OLE valisuhendust: egress-proxy keelab CONNECT koigile
hostidele organisatsiooni poliitikaga (mooedetud: curl -> 000,
"connect_rejected"). Seetottu ei saa siit Dukascopyt ega Supabase'i
otse pollida.

Tootav tee, mis on selles projektis kasutusel:

    Dukascopy .bi5  (binaar)
        |  Supabase Edge Function 'dukascopy-bi5' (Deno, base64 + sha256)
        v
    Postgres  extensions.http -> decode(b64) -> dukascopy_files.raw (bytea)
        |  MCP execute_sql:  select encode(raw,'base64')
        v
    tool-result fail  ->  SEE SKRIPT  ->  .bi5 failid + tick-CSV

MIKS BASE64: pgsql-http tagastab keha TEKSTINA. .bi5 on LZMA-voog, mille
2. bait on 0x00, seega tekstivali katkeb 1 baidi peal (mooedetud:
octet_length 11684, aga content::bytea 1 bait). Base64 on tekstikindel ja
labib tervena — sha256 kontrollitakse otsast otsani.

Kasutus:
    python3 dukascopy_ingest.py <tool-result-fail> <valjundkaust>
"""
import base64
import hashlib
import json
import os
import re
import sys

import dukascopy_bi5 as B

# NB: MITTE ankurdatud reaalguse/-lopuga.
#
# Varem oli siin ^...$ ja read otsiti rea kaupa. MCP tulemusefailis on
# esimene andmerida liidetud JSON-i eesliitega ([{"csv":") ja viimane
# jareliitega ("}]), sest saatetekst sisaldab ise <untrusted-data-...>
# tagi, mille tottu JSON-i eraldamine ebaonnestub ja langetakse tooreks
# tekstiks. Tulemus: IGA ekspordi esimene JA viimane fail kadusid vaikselt
# (mooedetud: 86 rida andmebaasis -> 83 sisse loetud). Base64-tahestikus
# ei ole '|', seega labiv finditer on uheselt maaratud ja veakindel.
RIDA = re.compile(r"([A-Z]{6})\|(\d{4}-\d{2}-\d{2})\|(\d{1,2})\|(\d+)\|"
                  r"([0-9a-f]{64})\|([A-Za-z0-9+/=]+)")


def loe_tulemus(path_in):
    """Koorib MCP JSON-i ja untrusted-ploki, tagastab toore CSV-teksti."""
    raw = open(path_in, encoding="utf-8", errors="replace").read()
    try:
        raw = json.loads(raw)["result"]
    except Exception:
        pass
    m = re.search(r"<untrusted-data-[0-9a-f-]+>(.*?)</untrusted-data-[0-9a-f-]+>",
                  raw, re.S)
    body = m.group(1).strip() if m else raw
    try:
        body = json.loads(body)[0]["csv"]
    except Exception:
        pass
    return body.replace("\\n", "\n")


def ingest(path_in, kaust):
    body = loe_tulemus(path_in)
    os.makedirs(kaust, exist_ok=True)
    read = []
    for g in RIDA.finditer(body):
        sym, paev, tund, suurus, sha, b64 = g.groups()
        blob = base64.b64decode(b64)
        # SHA256 kontroll otsast otsani: Edge Function arvutas selle
        # ALLIKA baitidest, enne base64. Kui see klapib, on kogu tee terve.
        sha_tegelik = hashlib.sha256(blob).hexdigest()
        read.append(dict(symbol=sym, paev=paev, tund=int(tund),
                         baite_oodatud=int(suurus), baite_saadud=len(blob),
                         sha_oodatud=sha, sha_tegelik=sha_tegelik,
                         sha_ok=(sha == sha_tegelik),
                         suurus_ok=(int(suurus) == len(blob)),
                         blob=blob))
    if not read:
        raise SystemExit("dukascopy_ingest: ei leidnud uhtegi kehtivat rida")
    return read


def kirjuta_bi5(read, kaust):
    for r in read:
        d = os.path.join(kaust, r["symbol"], r["paev"])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{r['tund']:02d}h_ticks.bi5"), "wb") as f:
            f.write(r["blob"])


def tikid(read):
    """Parsib failid tickideks. Tagastab {symbol: [tick, ...]}.

    NB: kutsuja peab andma ETTE AINULT UHE PAEVA read. Mitme paeva
    korraga andmine liidaks eri paevad uheks sumboli-jadaks.
    """
    import datetime as dt
    out = {}
    for r in read:
        y, m, d = (int(x) for x in r["paev"].split("-"))
        t = B.parsi(r["blob"], r["symbol"], dt.date(y, m, d), r["tund"])
        out.setdefault(r["symbol"], []).extend(t)
    for s in out:
        out[s].sort(key=lambda t: t["ts_utc"])
    return out


def kirjuta_csv(tik, kaust, paev):
    """Uks CSV sumboli kohta. Deterministlik jarjekord => idempotentne.

    LIIDAB olemasoleva failiga. Varem kirjutati "w"-ga ule: kui sama
    paeva ingestiti osade kaupa (nt ainult uuesti alla laetud tunnid),
    kustutas teine jooks esimese tunnid vaikselt ara. Nuud loetakse vana
    fail sisse ja read liidetakse; dedup-voti (ts, bid, ask) hoiab
    tulemuse uheseks ning sortimine teeb selle jarjekorrast soltumatuks.
    """
    os.makedirs(kaust, exist_ok=True)
    teed = {}
    for sym, ts in sorted(tik.items()):
        p = os.path.join(kaust, f"{sym}_{paev}_ticks.csv")

        read = {}
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                next(f, None)
                for ln in f:
                    ln = ln.rstrip("\n")
                    if not ln:
                        continue
                    osad = ln.split(",")
                    read[(osad[0], osad[1], osad[2])] = ln
        vanu = len(read)

        for t in ts:
            aeg = t["ts_utc"].strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
            k = (aeg, str(t["bid"]), str(t["ask"]))
            if k in read:
                continue
            read[k] = (f"{aeg},{t['bid']},{t['ask']},"
                       f"{t['bid_maht']:.4f},{t['ask_maht']:.4f}")

        read = [read[k] for k in sorted(read)]
        with open(p, "w", encoding="utf-8") as f:
            f.write("ts_utc,bid,ask,bid_maht,ask_maht\n")
            f.write("\n".join(read) + "\n")
        teed[sym] = (p, len(ts) + vanu, len(read))
    return teed


if __name__ == "__main__":
    fail, kaust = sys.argv[1], sys.argv[2]
    read = ingest(fail, kaust)
    print(f"faile: {len(read)}")
    print(f"  sha256 klapib   : {sum(1 for r in read if r['sha_ok'])}/{len(read)}")
    print(f"  suurus klapib   : {sum(1 for r in read if r['suurus_ok'])}/{len(read)}")
    kirjuta_bi5(read, os.path.join(kaust, "bi5"))

    # PAEVADE KAUPA. Varem oli siin paev = read[0]["paev"] ja koik read
    # laksid uhte kutsesse -> kaks paeva liideti uheks CSV-ks, mis kandis
    # esimese rea kuupaeva. Vaikne andmerike; parandatud.
    paevad = {}
    for r in read:
        paevad.setdefault(r["paev"], []).append(r)

    print(f"\n{'paev':<13s}{'sumbol':<10s}{'tikke':>10s}"
          f"{'unikaalseid':>13s}  fail")
    for paev in sorted(paevad):
        teed = kirjuta_csv(tikid(paevad[paev]),
                           os.path.join(kaust, "ticks"), paev)
        for sym, (p, n, u) in teed.items():
            print(f"{paev:<13s}{sym:<10s}{n:>10d}{u:>13d}  {p}")
