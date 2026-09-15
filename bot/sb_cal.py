"""
sb_cal.py — teisendab Supabase MCP tulemusefaili majanduskalendri CSV-ks.

Allikas: TradingView economic calendar API
(https://economic-calendar.tradingview.com/events), laetud Supabase `http`
laienduse kaudu tabelisse econ_cal. Liivakastil ei ole otseuhendust
(agent-proxy annab koigile valistele hostidele 000/403).

Valjad: valuuta, UTC release timestamp, indikaator, actual, forecast,
previous, importance.

Kasutus: python3 sb_cal.py <tool-result-fail> <valjund.csv>
"""
import json
import re
import sys

VEERUD = "cur,ts,indicator,actual,forecast,previous,importance"
RIDA = re.compile(
    r"^[A-Z]{3},\d{4}-\d{2}-\d{2}T\d{2}:\d{2},[^,]+,-?[\d.eE+]+,-?[\d.eE+]+,[^,]*,[^,]*$")


def extract(path_in, path_out):
    raw = open(path_in, encoding="utf-8", errors="replace").read()
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
        raise SystemExit("sb_cal: ei leidnud uhtegi kehtivat rida")
    with open(path_out, "w", encoding="utf-8") as f:
        f.write(VEERUD + "\n")
        f.write("\n".join(read) + "\n")
    val = sorted({ln.split(",")[0] for ln in read})
    kp = sorted({ln.split(",")[1][:10] for ln in read})
    ind = {ln.split(",")[2] for ln in read}
    print(f"{path_out}: {len(read)} sundmust, {len(val)} valuutat "
          f"({','.join(val)}), {len(ind)} indikaatorit, {kp[0]} .. {kp[-1]}")
    return len(read)


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
