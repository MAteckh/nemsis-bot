"""
sb_h1.py — teisendab Supabase MCP tulemusefaili H1 CSV-ks.

sb_fetch.py regexp ootab ainult kuupaeva (YYYY-MM-DD). H1 baaridel on
kaasas ka kellaaeg, seega vajab oma mustrit.

Kasutus: python3 sb_h1.py <tool-result-fail> <valjund.csv>
"""
import json, re, sys

RIDA = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?:,-?[\d.]+){4})")


def extract(path_in, path_out):
    raw = open(path_in, encoding="utf-8").read()
    try:
        raw = json.loads(raw)["result"]
    except Exception:
        pass
    m = re.search(r"<untrusted-data-[0-9a-f-]+>(.*?)</untrusted-data-[0-9a-f-]+>",
                  raw, re.S)
    body = m.group(1) if m else raw
    try:
        body = json.loads(body.strip())[0]["csv"]
    except Exception:
        pass
    body = body.replace("\\n", "\n")
    rows, nahtud = [], set()
    for tk in RIDA.findall(body):
        ts = tk[:16]
        if ts not in nahtud:
            nahtud.add(ts)
            rows.append(tk)
    if not rows:
        print(f"{path_out}: RIDU EI LEITUD")
        return 0
    rows.sort()
    with open(path_out, "w", encoding="utf-8") as f:
        f.write("Date,Open,High,Low,Close\n")
        f.write("\n".join(rows) + "\n")
    print(f"{path_out}: {len(rows)} rida  ({rows[0][:16]} .. {rows[-1][:16]})")
    return len(rows)


if __name__ == "__main__":
    extract(sys.argv[1], sys.argv[2])
