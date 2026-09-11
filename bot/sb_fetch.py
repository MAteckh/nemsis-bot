"""
sb_fetch.py — teisendab Supabase MCP päringu tulemusefaili puhtaks CSV-ks.

Taust: sellel liivakastil pole otseühendust ei andmepakkujate ega Supabase'i
REST API-ga. Andmed tulevad Supabase'i `http` laienduse kaudu (Postgres teeb
päringu, mitte meie), MCP execute_sql tagastab suure CSV-ploki, mis
salvestatakse automaatselt faili. See skript koorib JSON-ümbrise maha ja
kirjutab tavalise OHLC CSV, mida backtest.py oskab lugeda.

Kasutus:
    python sb_fetch.py <tool-result-fail> <valjund.csv>
"""
import json
import re
import sys


def extract(path_in, path_out):
    raw = open(path_in, encoding="utf-8").read()
    try:
        payload = json.loads(raw)["result"]
    except Exception:
        payload = raw
    # sisu on <untrusted-data-...> piiride vahel
    m = re.search(r"<untrusted-data-[0-9a-f-]+>(.*?)</untrusted-data-[0-9a-f-]+>", payload, re.S)
    body = m.group(1) if m else payload
    # SQL tagastas [{"csv":"...."}]
    try:
        body = json.loads(body.strip())[0]["csv"]
    except Exception:
        pass
    body = body.replace("\\n", "\n").strip()
    rows = []
    for ln in body.split("\n"):
        m2 = re.match(r"^(\d{4}-\d{2}-\d{2}(?:,-?[\d.]+){4})", ln)
        if m2:
            rows.append(m2.group(1))
    with open(path_out, "w", encoding="utf-8") as f:
        f.write("Date,Open,High,Low,Close\n")
        f.write("\n".join(rows) + "\n")
    print(f"{path_out}: {len(rows)} rida  ({rows[0][:10]} .. {rows[-1][:10]})")
    return len(rows)


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
