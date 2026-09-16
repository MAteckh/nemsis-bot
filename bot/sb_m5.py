"""
sb_m5.py — teisendab Supabase MCP tulemusefaili M5-baarideks (uks CSV paari kohta).

Allikas: Yahoo Finance 5-minutilised baarid, laetud Supabase `http` laienduse
kaudu tabelisse market_bars (load_yahoo_bars). Liivakastil ei ole otseuhendust.

Yahoo annab 5m baare AINULT ~60 paeva tagasi. Seda EI SAA pikendada.

Kasutus: python3 sb_m5.py <tool-result-fail> <valjundkaust>
"""
import json
import os
import re
import sys

RIDA = re.compile(r"^([A-Z]{6})_m5,"
                  r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}),"
                  r"([\d.eE+-]+),([\d.eE+-]+),([\d.eE+-]+),([\d.eE+-]+)$")


def extract(path_in, kaust):
    raw = open(path_in, encoding="utf-8", errors="replace").read()
    # Vastus on JSON, mille sees on untrusted-plokk, mille sees on JSON-massiiv,
    # mille "csv" valjas on reavahetused omakorda escape'itud. Dekodeerime
    # samm-sammult, mitte string-asendustega.
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
        g = RIDA.match(ln.strip())
        if g:
            read.setdefault(g.group(1), []).append(
                ",".join(g.groups()[1:]))
    if not read:
        raise SystemExit("sb_m5: ei leidnud uhtegi kehtivat rida")
    os.makedirs(kaust, exist_ok=True)
    for sym, read_ in sorted(read.items()):
        read_ = sorted(set(read_))
        p = os.path.join(kaust, f"{sym}_m5.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("Date,open,high,low,close\n")
            f.write("\n".join(read_) + "\n")
        print(f"  {p}: {len(read_)} baari  "
              f"{read_[0][:16]} .. {read_[-1][:16]}")
    return read


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
