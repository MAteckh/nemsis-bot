"""
sb_daily.py — koorib mitme sumboliga PAEVA-andmete tulemusefaili laiali.
sb_multi.py ootab ###SUMBOL_h1 voi _m15; siin on _d.
"""
import re, sys, os

MARK = re.compile(r"###([A-Z0-9]+)_d")
RIDA = re.compile(r"(\d{4}-\d{2}-\d{2}(?:,-?[\d.]+){4})")


def main(path_in):
    raw = open(path_in, encoding="utf-8", errors="replace").read().replace("\\n", "\n")
    tykid = MARK.split(raw)
    if len(tykid) < 3:
        print("MARKE EI LEITUD"); return
    for i in range(1, len(tykid), 2):
        sym, body = tykid[i], tykid[i + 1]
        rows, nahtud = [], set()
        for tk in RIDA.findall(body):
            if tk[:10] not in nahtud:
                nahtud.add(tk[:10]); rows.append(tk)
        if not rows:
            print(f"{sym}: ridu ei leitud"); continue
        rows.sort()
        out = os.path.join("data", f"{sym}_d.csv")
        with open(out, "w", encoding="utf-8") as f:
            f.write("Date,Open,High,Low,Close\n"); f.write("\n".join(rows) + "\n")
        print(f"{out}: {len(rows)} rida  ({rows[0][:10]} .. {rows[-1][:10]})")


if __name__ == "__main__":
    main(sys.argv[1])
