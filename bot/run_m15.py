"""
PDF-I ORIGINAALNE UULESEHITUS: 1H TREND + 15m SISENEMINE.

Senine test kasutas ainult H1-baare ja see oli PUUDUS, mille ma ise
valja tolin. Nuud on olemas 15-minutilised baarid ja saab teha tapselt
seda, mida dokument ette naeb.

LOOKAHEAD — koige olulisem koht selles failis:
H1-baar ajatempliga 09:00 katab vahemiku 09:00-10:00 ja SULGUB kell
10:00. Seega tema vaartus on teada alles kella 10:00 M15-baarist
alates. Kui ta lihtsalt reindeksida ffill-iga, lekib TULEVIK: kell
09:15 teaks bot juba, kuidas 09:00-10:00 tund lopeb.
=> nihutame H1-indeksi 1 tund EDASI enne uhendamist.

PIIRANG, mida tuleb valja oelda: Yahoo annab 15m ainult 60 paeva.
See on VAGA vahe. 58 paeva peal ei saa strateegiat valideerida —
saab ainult vaadata, kas H1-tulemus kordub. Seda ma siin teengi.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P, paar_config as C
from run_paarid import variandid

rng = np.random.default_rng(1709)
OUT = "m15_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()


def lae_m15(sym):
    p = os.path.join(E.DATA, f"{sym}_m15.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()[["open", "high", "low", "close"]]


def h1_m15_peale(h1_seeria, m15_index):
    """
    H1-indikaator M15-baaridele, ILMA tulevikku lekitamata.
    H1-baar ajatempliga T sulgub T+1h, seega kehtib alates T+1h.
    """
    s = h1_seeria.copy()
    s.index = s.index + pd.Timedelta(hours=1)
    return s.reindex(m15_index, method="ffill")


def sig_m15(d15, ind15, h1_ind, cfg, adx_min):
    """
    PDF: trend + ADX 1H pealt, tagasitomme + RSI 15m pealt.
    """
    c = d15["close"]
    f, m, s_ = cfg["ema"]
    # TREND 1H pealt
    tous, lang, adx1 = h1_ind
    tugev = adx1 > adx_min
    # SISENEMINE 15m pealt
    ef15 = c.ewm(span=f).mean()
    tagasi_up = (c > ef15) & (c.shift(1) <= ef15.shift(1))
    tagasi_dn = (c < ef15) & (c.shift(1) >= ef15.shift(1))
    rl, rh = cfg["rsi_long"]; sl_, sh_ = cfg["rsi_short"]
    r = ind15["rsi"]
    lng = tous & tugev & tagasi_up & r.between(rl, rh)
    srt = lang & tugev & tagasi_dn & r.between(sl_, sh_)
    return (lng.astype(float) - srt.astype(float)).fillna(0.0)


TP_PAARID = [s for s, c in C.PAARID.items() if c["rezim"] == "trend_pullback"]

w("=" * 100)
w("PDF-i ORIGINAAL: 1H TREND + 15m SISENEMINE  (60 päeva andmeid)")
w("=" * 100)
w("   NB: 60 päeva on valideerimiseks liiga vähe. See test näitab, kas")
w("   H1-tulemus KORDUB peenemal ajaskaalal — mitte et strateegia töötab.")
w("")
w(f"   {'paar':8s} {'teh':>5s} {'teh/päev':>9s} {'võit%':>7s} {'BRUTO bp':>9s} "
  f"{'retail':>8s} {'ECN':>8s} {'PÖÖRATUD':>9s}")
w("   " + "-" * 70)

read = []
for sym in TP_PAARID:
    cfg = C.PAARID[sym]
    d15 = lae_m15(sym)
    dh1 = E.lae(sym)
    if d15 is None or dh1 is None:
        w(f"   {sym:8s} — andmeid puudu"); continue
    # H1 trend-osa
    ch = dh1["close"]
    f_, m_, s_ = cfg["ema"]
    ef, em = ch.ewm(span=f_).mean(), ch.ewm(span=m_).mean()
    es = ch.ewm(span=s_).mean() if s_ else em
    tous_h1 = (ef > em) & (em > es) if s_ else (ef > em)
    lang_h1 = (ef < em) & (em < es) if s_ else (ef < em)
    adx_h1 = P.adx(dh1, 14)
    h1_ind = (h1_m15_peale(tous_h1, d15.index).fillna(False).astype(bool),
              h1_m15_peale(lang_h1, d15.index).fillna(False).astype(bool),
              h1_m15_peale(adx_h1, d15.index))
    ind15 = P.valmista(d15)
    kr, ke = E.KULU_RETAIL.get(sym, 1.5), E.KULU_ECN.get(sym, .5)
    sess = C.SESS[cfg["sess"]]
    paevi = (d15.index[-1] - d15.index[0]).days

    for v in variandid(sym, cfg):
        sg = sig_m15(d15, ind15, h1_ind, cfg, v["adx"])
        if int((sg != 0).sum()) < 30:
            continue
        # max_baare 120 M15-baari = 30h, sarnane H1 testi 120 tunniga? ei —
        # hoiame sama KELLAAJA: 120h = 480 M15-baari
        t = P.simuleeri(d15, sg, v["sl"], v["tp"], kr, ind15, sess, max_baare=480)
        if t is None or len(t) < 25:
            continue
        tp_ = P.simuleeri(d15, -sg, v["sl"], v["tp"], kr, ind15, sess, max_baare=480)
        b = t["bruto"].values
        read.append(dict(sym=sym, adx=v["adx"], sl=v["sl"], tp=v["tp"], n=len(t),
                         paevad=paevi, wr=100*float((t["tulem"]>0).mean()),
                         bruto=float(b.mean()), retail=float(t["tulem"].mean()),
                         ecn=float((b - 2*ke/1e4).mean()),
                         poord=float(tp_["tulem"].mean()) if tp_ is not None and len(tp_)>25 else np.nan))

df = pd.DataFrame(read)
df.to_csv("data/m15.csv", index=False)
for sym in TP_PAARID:
    g = df[df["sym"] == sym]
    if not len(g):
        w(f"   {sym:8s} — liiga vähe tehinguid"); continue
    r = g.iloc[len(g)//2]
    w(f"   {r['sym']:8s} {r['n']:5d} {r['n']/r['paevad']:9.2f} {r['wr']:6.1f}% "
      f"{1e4*r['bruto']:+9.1f} {1e4*r['retail']:+8.1f} {1e4*r['ecn']:+8.1f} "
      f"{1e4*r['poord']:+9.1f}")

w("")
w(f"   variante {len(df)}")
w(f"   BRUTO plussis  {int((df['bruto']>0).sum())}/{len(df)} "
  f"({100*(df['bruto']>0).mean():.0f}%)   keskmine {1e4*df['bruto'].mean():+.1f}bp")
w(f"   retail plussis {int((df['retail']>0).sum())}/{len(df)} "
  f"({100*(df['retail']>0).mean():.0f}%)   keskmine {1e4*df['retail'].mean():+.1f}bp")
w(f"   ECN plussis    {int((df['ecn']>0).sum())}/{len(df)} "
  f"({100*(df['ecn']>0).mean():.0f}%)   keskmine {1e4*df['ecn'].mean():+.1f}bp")
w(f"   PÖÖRATUD plussis {int((df['poord']>0).sum())}/{len(df)} "
  f"({100*(df['poord']>0).mean():.0f}%)   keskmine {1e4*df['poord'].mean():+.1f}bp")

# ── VÕRDLUS H1-ga ───────────────────────────────────────────────
w("")
w("=" * 100)
w("KAS 15m SISENEMINE PARANDAB H1 TULEMUST?")
w("=" * 100)
h1df = pd.read_csv("data/paarid.csv")
h1tp = h1df[h1df["rezim"] == "trend_pullback"]
w(f"   {'':14s} {'H1 sisenemine':>15s} {'15m sisenemine':>16s}")
w("   " + "-" * 48)
w(f"   {'BRUTO keskm':14s} {1e4*h1tp['ootus'].mean()+2.6:>14.1f} "
  f"{1e4*df['bruto'].mean():>15.1f}")
w(f"   {'retail keskm':14s} {1e4*h1tp['ootus'].mean():>14.1f} "
  f"{1e4*df['retail'].mean():>15.1f}")
w(f"   {'plussis %':14s} {100*(h1tp['ootus']>0).mean():>13.0f}% "
  f"{100*(df['retail']>0).mean():>14.0f}%")
w(f"   {'tehinguid':14s} {h1tp['n'].median():>14.0f} {df['n'].median():>15.0f}")

# ── AUS BASELINE M15-l ──────────────────────────────────────────
w("")
w("=" * 100)
w("AUS BASELINE — juhuslik sisenemine läbib sama valiku")
w("=" * 100)
w(f"   {'paar':8s} {'strat ECN':>10s} {'juhu ECN parim':>15s} {'vahe':>8s}")
w("   " + "-" * 46)
vahed = []
for sym in TP_PAARID:
    g = df[df["sym"] == sym]
    if not len(g): continue
    r = g.loc[g["ecn"].idxmax()]
    d15 = lae_m15(sym); ind15 = P.valmista(d15)
    ke = E.KULU_ECN.get(sym, .5); sess = C.SESS[C.PAARID[sym]["sess"]]
    n = len(d15); juh = []
    for _ in range(len(g)):
        m = max(int(r["n"]), 30)
        idx = rng.choice(np.arange(300, n-1), size=m, replace=False)
        s2 = pd.Series(0.0, index=d15.index)
        s2.iloc[np.sort(idx)] = rng.choice([-1.0, 1.0], size=m)
        t2 = P.simuleeri(d15, s2, r["sl"], r["tp"], ke, ind15, sess, max_baare=480)
        if t2 is not None and len(t2) >= 25:
            juh.append(float((t2["bruto"] - 2*ke/1e4).mean()))
    if not juh: continue
    jm = max(juh); vahed.append(r["ecn"] - jm)
    w(f"   {sym:8s} {1e4*r['ecn']:+9.1f} {1e4*jm:+14.1f} {1e4*(r['ecn']-jm):+7.1f}")
w("")
if vahed:
    w(f"   Juhuslikust parem: {sum(1 for v in vahed if v>0)}/{len(vahed)}   "
      f"keskmine vahe {1e4*np.mean(vahed):+.1f}bp")
w("VALMIS")
