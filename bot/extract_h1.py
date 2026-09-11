import json, re, sys, collections
def go(src, outdir="data"):
    raw = open(src, encoding="utf-8", errors="replace").read()
    try: payload = json.loads(raw)["result"]
    except Exception: payload = raw
    m = re.search(r"<untrusted-data-[0-9a-f-]+>(.*?)</untrusted-data-[0-9a-f-]+>", payload, re.S)
    body = (m.group(1) if m else payload).replace("\\n", "\n")
    try: body = json.loads(body.strip())[0]["csv"]
    except Exception: pass
    body = body.replace("\\n", "\n")
    pat = re.compile(r"^([A-Z0-9]+)_h1,(\d{4}-\d{2}-\d{2} \d{2}:\d{2}),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)$")
    b = collections.defaultdict(list)
    for ln in body.split("\n"):
        mm = pat.match(ln.strip())
        if mm: b[mm.group(1)].append(",".join(mm.groups()[1:]))
    for sym, rows in sorted(b.items()):
        p = f"{outdir}/{sym}_h1.csv"
        open(p, "w").write("Date,Open,High,Low,Close\n" + "\n".join(rows) + "\n")
        print(f"{sym:8s} {len(rows):6d} baari  {rows[0][:16]} .. {rows[-1][:16]}")
if __name__ == "__main__": go(sys.argv[1])
