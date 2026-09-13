"""
sb_d25.py — koorib pikad paevased (_d25) seeriad Supabase tulemusefailist.

Sama muster kui sb_multi.py, aga sufiksiga _d25 (Yahoo 25-aastane ajalugu,
COT A1 pikendustesti jaoks). Ei muuda uhtegi olemasolevat andmefaili.

Kasutus: python3 sb_d25.py <tool-result-fail>
"""
import os
import re
import sys

MARK = re.compile(r"###([A-Z0-9]+_d25)")
RIDA = re.compile(r"\d{4}-\d{2}-\d{2}(?:,-?\d+\.?\d*){4}")


def main(path_in):
    raw = open(path_in, encoding="utf-8", errors="replace").read().replace("\\n", "\n")
    tykid = MARK.split(raw)
    if len(tykid) < 3:
        raise SystemExit("sb_d25: MARKE EI LEITUD")
    for i in range(1, len(tykid), 2):
        sym, body = tykid[i], tykid[i + 1]
        read, nahtud = [], set()
        for tk in RIDA.findall(body):
            if tk[:10] not in nahtud:
                nahtud.add(tk[:10])
                read.append(tk)
        if not read:
            print(f"{sym}: ridu ei leitud")
            continue
        read.sort()
        out = os.path.join("data", f"{sym}.csv")
        with open(out, "w", encoding="utf-8") as f:
            f.write("Date,Open,High,Low,Close\n")
            f.write("\n".join(read) + "\n")
        print(f"{out}: {len(read)} rida  ({read[0][:10]} .. {read[-1][:10]})")


if __name__ == "__main__":
    main(sys.argv[1])
