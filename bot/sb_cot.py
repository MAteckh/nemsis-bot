"""
sb_cot.py — teisendab Supabase MCP execute_sql tulemusefaili CFTC COT CSV-ks.

Taust: liivakastil pole otseuhendust cftc.gov-iga (agent-proxy 403). Andmed
tulevad kasutaja Supabase'i `http` laienduse kaudu: Postgres kusib Socrata
API-t (publicreporting.cftc.gov), tulemus salvestatakse tabelisse cot_legacy
ja eksporditakse uhe suure string_agg CSV-plokina. See skript koorib
JSON-umbrise maha.

Kasutus:
    python sb_cot.py <tool-result-fail> <valjund.csv>
"""
import json
import re
import sys

VEERUD = "cur,date,nc_long,nc_short,comm_long,comm_short,oi"
RIDA = re.compile(r"^(?:USDX|[A-Z]{3}),\d{4}-\d{2}-\d{2}(?:,-?\d+){5}$")


def extract(path_in, path_out):
    raw = open(path_in, encoding="utf-8").read()
    try:
        payload = json.loads(raw)["result"]
    except Exception:
        payload = raw
    m = re.search(r"<untrusted-data-[0-9a-f-]+>(.*?)</untrusted-data-[0-9a-f-]+>",
                  payload, re.S)
    body = m.group(1) if m else payload
    try:
        body = json.loads(body.strip())[0]["csv"]
    except Exception:
        pass
    body = body.replace("\\n", "\n")
    read = [ln.strip() for ln in body.split("\n")]
    read = [ln for ln in read if RIDA.match(ln)]
    if not read:
        raise SystemExit("sb_cot: ei leidnud uhtegi kehtivat rida")
    with open(path_out, "w", encoding="utf-8") as f:
        f.write(VEERUD + "\n")
        f.write("\n".join(read) + "\n")
    vald = sorted({ln.split(",")[0] for ln in read})
    kp = sorted({ln.split(",")[1] for ln in read})
    print(f"{path_out}: {len(read)} rida, {len(vald)} valuutat "
          f"({','.join(vald)}), {kp[0]} .. {kp[-1]}")
    return len(read)


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
