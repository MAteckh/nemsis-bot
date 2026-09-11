"""sb_split.py — koorib MCP tulemusefailist mitme sümboli baarid eraldi CSV-deks.

Sisendrida kuju: SYMBOL,YYYY-MM-DD,open,high,low,close
"""
import json, re, sys, os, collections

def split(path_in, out_dir):
    raw = open(path_in, encoding="utf-8", errors="replace").read()
    try:
        payload = json.loads(raw)["result"]
    except Exception:
        payload = raw
    m = re.search(r"<untrusted-data-[0-9a-f-]+>(.*?)</untrusted-data-[0-9a-f-]+>", payload, re.S)
    body = m.group(1) if m else payload
    try:
        body = json.loads(body.strip())[0]["csv"]
    except Exception:
        pass
    body = body.replace("\\n", "\n")
    buckets = collections.defaultdict(list)
    pat = re.compile(r"^([A-Z0-9]+)_d,(\d{4}-\d{2}-\d{2}),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)$")
    for ln in body.split("\n"):
        mm = pat.match(ln.strip())
        if mm:
            buckets[mm.group(1)].append(",".join(mm.groups()[1:]))
    os.makedirs(out_dir, exist_ok=True)
    for sym, rows in sorted(buckets.items()):
        p = os.path.join(out_dir, f"{sym}_d.csv")
        with open(p, "w", encoding="utf-8") as f:
            f.write("Date,Open,High,Low,Close\n")
            f.write("\n".join(rows) + "\n")
        print(f"{sym:8s} {len(rows):5d} rida  {rows[0][:10]} .. {rows[-1][:10]}")
    return buckets

if __name__ == "__main__":
    split(sys.argv[1], sys.argv[2])
