"""
sb_min.py — teisendab Supabase MCP tulemusefaili minutibaarideks.

Allikas: Yahoo Finance, laetud Supabase `http` laienduse kaudu tabelisse
market_bars (load_yahoo_range, period1/period2 aknad).

MOOEDETUD PIIRANG: Yahoo annab 1-minutilisi baare ainult ~28 paeva tagasi
(7-paevaste akende kaupa; 28 ja 35 paeva tagasi tagastavad 0 rida).
Seda EI SAA pikendada ilma tasulise allikata.

Kasutus: python3 sb_min.py <tool-result-fail> <valjundkaust> <sufiks>
   nait: python3 sb_min.py tulemus.txt data/ m1
"""
import json
import os
import re
import sys


def extract(path_in, kaust, sufiks):
    rida = re.compile(r"^([A-Z]{6})_" + re.escape(sufiks) + r","
                      r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}),"
                      r"([\d.eE+-]+),([\d.eE+-]+),([\d.eE+-]+),([\d.eE+-]+)$")
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
        body = body.replace("\\n", "\n")
    read = {}
    for ln in body.split("\n"):
        g = rida.match(ln.strip())
        if g:
            read.setdefault(g.group(1), []).append(",".join(g.groups()[1:]))
    if not read:
        raise SystemExit(f"sb_min: ei leidnud uhtegi kehtivat {sufiks} rida")
    os.makedirs(kaust, exist_ok=True)
    for sym, r in sorted(read.items()):
        r = sorted(set(r))
        p = os.path.join(kaust, f"{sym}_{sufiks}.csv")
        vana = 0
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                olemas = [x.strip() for x in f.readlines()[1:] if x.strip()]
            vana = len(olemas)
            r = sorted(set(r) | set(olemas))
        with open(p, "w", encoding="utf-8") as f:
            f.write("Date,open,high,low,close\n")
            f.write("\n".join(r) + "\n")
        print(f"  {p}: {len(r)} baari (+{len(r)-vana} uut)  "
              f"{r[0][:16]} .. {r[-1][:16]}")
    return read


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2], sys.argv[3])
