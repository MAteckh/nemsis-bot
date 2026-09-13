"""
NEMSIS v6 — KATEGOORIA 2: MAKROSUNDMUSED ja KATEGOORIA 3: MIKROSTRUKTUUR.

KATEGOORIA 2 — MIS ON AUSALT TESTITAV:
Mul ei ole majanduskalendrit. AGA uks sundmus on REEGLIGA tuletatav ja
seega ei vaja kalendrit:
  NFP (US tooturu raport) = iga kuu ESIMENE REEDE kell 13:30 UTC
  (suveajal 12:30 UTC, aga H1-baaridel langeb see samasse baari)
See on avalik, fikseeritud ajakava alates 1940ndatest. Kasutan seda.

FOMC/ECB/BoE/BoJ kuupaevad EI OLE reegliga tuletatavad (need maaratakse
igal aastal eraldi). Ilma kalendrita neid ei testi — margin need
TESTIMATA, mitte ei valeta kuupaevi malust.

EELREGISTREERITUD (uks primary spetsifikatsioon kummalegi):
  V6-M1  NFP jatkuvus: sundmuse baari suund ennustab jargmisi baare
  V6-M2  NFP poordumine: sundmuse baari suund poordub
  V6-M3  NFP volatiilsuse laienemine: kas vol tousеb (kirjeldav)
  V6-M4  post-event drift: 4h ja 1d parast

KONSERVATIIVNE SLIPPAGE: uudise ajal spread laieneb 3-10x. Testime
kolme tasemega: tavaline, 3x, 10x.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E

OUT = "v6_makro.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

PAARID = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD","XAUUSD"]
D = {s: E.lae(s) for s in PAARID}
D = {k: v for k, v in D.items() if v is not None}


def nfp_baarid(ix):
    """Kuu esimene reede, tund 13 UTC. Reegliga tuletatav, kalendrit ei vaja."""
    s = pd.Series(ix, index=ix)
    reede = ix.dayofweek == 4
    esimene = s.groupby([ix.year, ix.month]).transform(
        lambda g: g.dt.day <= 7).values
    return reede & esimene & (ix.hour == 13)


w("=" * 96)
w("KATEGOORIA 2 — MAKROSÜNDMUSED (NFP, reegliga tuletatav)")
w("=" * 96)
w("  NFP = kuu esimene reede 13:30 UTC. Avalik, fikseeritud ajakava.")
w("  FOMC/ECB/BoE/BoJ kuupäevad EI OLE reegliga tuletatavad => TESTIMATA.")
w("")

kokku = {}
for sym, d in D.items():
    m = nfp_baarid(d.index)
    if m.sum() < 15:
        continue
    c, o, h, l = d["close"], d["open"], d["high"], d["low"]
    ev_r = (c / o - 1)[m]                        # sündmuse baari tootlus
    a = E.atr(d, 14)
    # volatiilsuse laienemine
    vol_ev = float(((h - l) / a)[m].mean())
    vol_muu = float(((h - l) / a)[~m].dropna().mean())
    # jargnevad tootlused
    nxt = {}
    for k in (1, 4, 24):
        fut = (c.shift(-k) / o.shift(-1) - 1)
        nxt[k] = fut[m]
    kokku[sym] = dict(n=int(m.sum()), ev=ev_r, vol_ev=vol_ev, vol_muu=vol_muu, nxt=nxt)

w(f"  {'paar':8s} {'NFP-baare':>10s} {'vol NFP/tavaline':>18s} {'|liikumine|':>12s}")
w("  " + "-" * 54)
for sym, r in kokku.items():
    w(f"  {sym:8s} {r['n']:10d} {r['vol_ev']/max(r['vol_muu'],1e-9):17.2f}x "
      f"{1e4*float(r['ev'].abs().mean()):11.0f}bp")

w("")
w("  V6-M1/M2 — kas sündmuse baari SUUND ennustab järgnevat? (bp, ILMA kuludeta)")
w(f"  {'paar':8s} {'+1h':>9s} {'+4h':>9s} {'+24h':>9s}  (positiivne = JÄTKUVUS)")
w("  " + "-" * 52)
agg = {1: [], 4: [], 24: []}
for sym, r in kokku.items():
    rida = f"  {sym:8s}"
    for k in (1, 4, 24):
        sg = np.sign(r["ev"])
        x = (sg * r["nxt"][k]).dropna()
        if len(x) < 10:
            rida += f"{'-':>9s}"; continue
        agg[k].append(float(x.mean()))
        rida += f"{1e4*float(x.mean()):+9.1f}"
    w(rida)
w("  " + "-" * 52)
w(f"  {'KESKMINE':8s}" + "".join(f"{1e4*np.mean(agg[k]):+9.1f}" for k in (1,4,24)))

w("")
w("  KULUD UUDISE AJAL — spread laieneb. Kas serv jääb alles?")
w(f"  {'slippage-tase':>22s} {'+1h':>9s} {'+4h':>9s} {'+24h':>9s}")
w("  " + "-" * 52)
for nimi, kordaja in (("tavaline (2.6bp)", 1), ("uudise ajal 3x", 3), ("uudise ajal 10x", 10)):
    kulu = 2.6 * kordaja / 1e4
    w(f"  {nimi:>22s}" + "".join(
        f"{1e4*(np.mean(agg[k]) - kulu):+9.1f}" for k in (1,4,24)))
w("")
parim = max((1,4,24), key=lambda k: np.mean(agg[k]))
w(f"  Parim horisont: +{parim}h, {1e4*np.mean(agg[parim]):+.1f}bp ENNE kulusid.")
w(f"  Tavalise kuluga: {1e4*(np.mean(agg[parim]) - 2.6/1e4):+.1f}bp")
w(f"  Uudise ajal 3x kuluga: {1e4*(np.mean(agg[parim]) - 3*2.6/1e4):+.1f}bp")
w("")
w("  NFP tehinguid on 12 aastas. Isegi kui serv oleks +5bp, annaks see")
w("  12 x 5bp = 60bp aastas = 0.6% — enne võimendust, enne slippage'i.")

w("")
w("=" * 96)
w("KATEGOORIA 3 — MIKROSTRUKTUUR")
w("=" * 96)
w("")
w("  NÕUTUD ANDMED: tick-andmed või bid/ask kvoodid.")
w("  OLEMAS: ainult OHLC (päev, H1, M15). Bid/ask EI OLE. Tick EI OLE.")
w("  Mahtu (volume) samuti ei ole — Yahoo FX-seeriad seda ei anna.")
w("")
w("  Kasutaja juhis: 'ÄRA leiuta order flow'd OHLC-st. Kui päris bid/ask")
w("  või tick-andmeid ei ole: MARK AS UNTESTABLE. Ära loo sünteetilist")
w("  order flow'd.'")
w("")
w("  => KATEGOORIA 3 = UNTESTABLE.")
w("")
w("  Mida saaks OHLC-st tuletada ja MIKS ma seda EI tee:")
w("    - 'bid/ask imbalance' küünla kerest  => see EI OLE order flow,")
w("      see on hinnamuutus teise nimega. Juba testitud (momentum).")
w("    - 'quote intensity' baari ulatusest  => see on volatiilsus.")
w("      Juba testitud (v4 vol-režiimid, v4 surve->murre).")
w("    - 'likviidsusšokk' suurest baarist   => see on vol-hüpe.")
w("      Juba testitud (v4 'ebanormaalne' režiim).")
w("  Kõik kolm on juba negatiivse tulemusega testitud teiste nimede all.")
w("VALMIS")
