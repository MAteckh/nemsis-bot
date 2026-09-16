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

RIDA = re.compile(r"^([A-Z]{6})\|(\d{4}-\d{2}-\d{2})\|(\d{1,2})\|(\d+)\|"
                  r"([0-9a-f]{64})\|([A-Za-z0-9+/=]+)$")


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
    for ln in body.split("\n"):
        g = RIDA.match(ln.strip())
        if not g:
            continue
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
    """Parsib koik failid tickideks. Tagastab {symbol: [tick, ...]}."""
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
    """Uks CSV sumboli kohta. Deterministlik jarjekord => idempotentne."""
    os.makedirs(kaust, exist_ok=True)
    teed = {}
    for sym, ts in sorted(tik.items()):
        p = os.path.join(kaust, f"{sym}_{paev}_ticks.csv")
        # DEDUPLIKEERIMINE deterministliku votme jargi (symbol, ts, bid, ask)
        nahtud, read = set(), []
        for t in ts:
            k = B.votme_rida(sym, t)
            if k in nahtud:
                continue
            nahtud.add(k)
            read.append(f"{t['ts_utc'].strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]},"
                        f"{t['bid']},{t['ask']},{t['bid_maht']:.4f},"
                        f"{t['ask_maht']:.4f}")
        with open(p, "w", encoding="utf-8") as f:
            f.write("ts_utc,bid,ask,bid_maht,ask_maht\n")
            f.write("\n".join(read) + "\n")
        teed[sym] = (p, len(ts), len(read))
    return teed


if __name__ == "__main__":
    fail, kaust = sys.argv[1], sys.argv[2]
    read = ingest(fail, kaust)
    print(f"faile: {len(read)}")
    print(f"  sha256 klapib   : {sum(1 for r in read if r['sha_ok'])}/{len(read)}")
    print(f"  suurus klapib   : {sum(1 for r in read if r['suurus_ok'])}/{len(read)}")
    kirjuta_bi5(read, os.path.join(kaust, "bi5"))
    tik = tikid(read)
    paev = read[0]["paev"]
    teed = kirjuta_csv(tik, os.path.join(kaust, "ticks"), paev)
    print(f"\n{'sumbol':<10s}{'tikke':>10s}{'unikaalseid':>13s}  fail")
    for sym, (p, n, u) in teed.items():
        print(f"{sym:<10s}{n:>10d}{u:>13d}  {p}")
