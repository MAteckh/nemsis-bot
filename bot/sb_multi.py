"""
sb_multi.py — koorib MITME sumboliga Supabase tulemusefaili laiali.

Paring vormistab iga sumboli ette rea ###SUMBOL. See skript loikab faili
nende markide kohalt ja kirjutab iga sumboli oma CSV-ks data/ kausta.

Kasutus: python3 sb_multi.py <tool-result-fail>
"""
import re, sys, os
from sb_h1 import RIDA

def main(path_in):
    raw = open(path_in, encoding="utf-8", errors="replace").read().replace("\\n", "\n")
    tykid = re.split(r"###([A-Z0-9]+_h1)", raw)
    if len(tykid) < 3:
        print("MARKE EI LEITUD")
        return
    for i in range(1, len(tykid), 2):
        sym, body = tykid[i], tykid[i + 1]
        rows, nahtud = [], set()
        for tk in RIDA.findall(body):
            if tk[:16] not in nahtud:
                nahtud.add(tk[:16]); rows.append(tk)
        if not rows:
            print(f"{sym}: ridu ei leitud"); continue
        rows.sort()
        out = os.path.join("data", f"{sym.replace('_h1','')}_h1.csv")
        with open(out, "w", encoding="utf-8") as f:
            f.write("Date,Open,High,Low,Close\n"); f.write("\n".join(rows) + "\n")
        print(f"{out}: {len(rows)} rida  ({rows[0][:16]} .. {rows[-1][:16]})")

if __name__ == "__main__":
    main(sys.argv[1])
