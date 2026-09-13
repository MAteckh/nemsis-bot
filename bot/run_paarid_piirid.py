"""
KONTROLLIN OMA ENDA EELDUST.

Tulemus utles: bruto-ootus (ENNE kulusid) on -1.8bp. See on kummaline
— juhusliku jalutuskaigu peal peaks bruto olema ~0. Kaks voimalikku
pohjust:
  (a) signaalid on PARISELT vastupidised (breakout-sisenemised
      kaotavad, sest H1-tunnis on lyhiajaline poordumine)
  (b) MINU reegel tekitab selle: kui TP ja SL on samas baaris moLEMAD
      tabatud, eeldan SL-i. TP on 2-3x kaugemal kui SL, seega "moLEMAD
      tabatud" juhtub ainult suurte baaride peal — ja neil ma annan
      alati halvima tulemuse.

Kui (b) selgitab suure osa, siis on minu number liiga pessimistlik ja
ma pean seda utlema.

TEST: joosuta sama asi KOLME eeldusega:
  pessimistlik — moLEMAD tabatud => SL   (senine)
  optimistlik  — moLEMAD tabatud => TP
  keskmine     — moLEMAD tabatud => pool SL, pool TP
Kui ka OPTIMISTLIK on miinuses, on jareldus kindel.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P, paar_config as C
from run_paarid import variandid, signaal

OUT = "paarid_piirid.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()


def simuleeri_eeldus(d, sg, sl_atr, tp_r, kulu_bp, ind, sess, eeldus):
    """eeldus: 'sl' | 'tp' | 'pool'."""
    o, h, l, c = (d["open"].values, d["high"].values,
                  d["low"].values, d["close"].values)
    a = ind["atr"].values
    s = sg.values
    tund = d.index.hour.values
    h0, h1 = sess
    rt = kulu_bp / 1e4
    n = len(d)
    teh, molemad = [], 0
    i = 250
    while i < n - 1:
        if s[i] == 0 or not (np.isfinite(a[i]) and a[i] > 0) or not (h0 <= tund[i] < h1):
            i += 1; continue
        suund = int(np.sign(s[i]))
        entry = o[i + 1]
        sl_d = sl_atr * a[i]; tp_d = tp_r * sl_d
        tp = entry + suund * tp_d; slh = entry - suund * sl_d
        r, j = None, i + 1
        for j in range(i + 1, min(i + 1 + 120, n)):
            th = (h[j] >= tp) if suund == 1 else (l[j] <= tp)
            sh_ = (l[j] <= slh) if suund == 1 else (h[j] >= slh)
            if th and sh_:
                molemad += 1
                r = {"sl": -sl_d, "tp": tp_d,
                     "pool": 0.5 * (tp_d - sl_d)}[eeldus] / entry
                break
            if th:
                r = tp_d / entry; break
            if sh_:
                r = -sl_d / entry; break
        if r is None:
            j = min(i + 120, n - 1)
            r = suund * (c[j] - entry) / entry
        teh.append((r, r - 2 * rt))
        i = j + 1
    if len(teh) < 30:
        return None, 0
    arr = np.array(teh)
    return dict(bruto=float(arr[:, 0].mean()), neto=float(arr[:, 1].mean()),
                n=len(arr)), molemad


w("=" * 96)
w("KUI PALJU MINU KONSERVATIIVNE EELDUS TULEMUST MÕJUTAB?")
w("=" * 96)
w("   'mõlemad tabatud samas baaris' — kolm erinevat eeldust")
w("")
w(f"   {'eeldus':>14s} {'variante':>9s} {'BRUTO>0':>9s} {'keskm BRUTO':>12s} "
  f"{'NETO>0':>8s} {'keskm NETO':>11s}")
w("   " + "-" * 66)

tulem = {}
mol_kokku = tehinguid_kokku = 0
for eeldus in ("sl", "pool", "tp"):
    read = []
    for sym, cfg in C.PAARID.items():
        d = E.lae(sym)
        if d is None: continue
        ind = P.valmista(d)
        kulu = E.KULU_RETAIL.get(sym, 1.5)
        sess = C.SESS[cfg["sess"]]
        for v in variandid(sym, cfg):
            sg = signaal(d, cfg, v, ind)
            if int((sg != 0).sum()) < 40: continue
            r, mol = simuleeri_eeldus(d, sg, v["sl"], v["tp"], kulu, ind, sess, eeldus)
            if r is None: continue
            read.append(r)
            if eeldus == "sl":
                mol_kokku += mol; tehinguid_kokku += r["n"]
    g = pd.DataFrame(read)
    tulem[eeldus] = g
    nimi = {"sl": "PESSIMISTLIK", "pool": "keskmine", "tp": "OPTIMISTLIK"}[eeldus]
    w(f"   {nimi:>14s} {len(g):9d} {100*(g['bruto']>0).mean():8.1f}% "
      f"{1e4*g['bruto'].mean():+12.1f} {100*(g['neto']>0).mean():7.1f}% "
      f"{1e4*g['neto'].mean():+11.1f}")

w("")
w(f"   'mõlemad tabatud' juhtus {mol_kokku} korral {tehinguid_kokku} tehingust "
  f"= {100*mol_kokku/max(tehinguid_kokku,1):.1f}%")
w("")
if tulem["tp"]["bruto"].mean() < 0:
    w("   => Ka KÕIGE OPTIMISTLIKUMA eeldusega on bruto miinuses.")
    w("      Järeldus ei tule minu eeldusest, vaid andmetest.")
else:
    w("   => OPTIMISTLIK eeldus viib bruto plussi. Minu senine number oli")
    w("      liiga pessimistlik ja seda tuleb arvestada.")

# ── MIKS bruto miinuses? Kontrolli suunda ───────────────────────
w("")
w("=" * 96)
w("KAS SIGNAALID ON VASTUPIDISED? (pöörame suuna ümber)")
w("=" * 96)
w("   Kui signaal on süstemaatiliselt vale, peab VASTUPIDINE teenima.")
w("")
w(f"   {'režiim':18s} {'tavaline bruto':>15s} {'VASTUPIDINE bruto':>19s}")
w("   " + "-" * 56)
for rz in ("trend_pullback", "breakout_retest", "mean_reversion", "regime_switch"):
    tav, vas = [], []
    for sym, cfg in C.PAARID.items():
        if cfg["rezim"] != rz: continue
        d = E.lae(sym)
        if d is None: continue
        ind = P.valmista(d)
        kulu = E.KULU_RETAIL.get(sym, 1.5)
        sess = C.SESS[cfg["sess"]]
        for v in variandid(sym, cfg):
            sg = signaal(d, cfg, v, ind)
            if int((sg != 0).sum()) < 40: continue
            r1, _ = simuleeri_eeldus(d, sg, v["sl"], v["tp"], kulu, ind, sess, "sl")
            r2, _ = simuleeri_eeldus(d, -sg, v["sl"], v["tp"], kulu, ind, sess, "sl")
            if r1: tav.append(r1["bruto"])
            if r2: vas.append(r2["bruto"])
    if tav:
        w(f"   {rz:18s} {1e4*np.mean(tav):+14.1f} {1e4*np.mean(vas):+18.1f}")
w("")
w("   Kui MÕLEMAD on miinuses, ei ole tegu vale suunaga — tegu on")
w("   TP/SL asümmeetria ja 'mõlemad tabatud' reegli maksumusega.")
w("VALMIS")
