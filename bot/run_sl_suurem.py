"""
S/R STRATEEGIA: SUUREM STOP LOSS (kasutaja palve "Sl pane suurem").

EELMINE TULEMUS (run_sr_tpsl_h1.py): 41/46 varianti miinuses. Ainus
perekond, kus uldse positiivseid oli, oli TP 2.0 / SL 1.0 ATR — ehk
SUUR TP, mitte vaike. Vaike TP (0.25 ATR) oli KOIGE HALVEM, hoolimata
sellest et voiduprotsent oli 62-66%.

MIDA SUUREM SL TEEB (huopotees enne testi):
  Suurem SL vahendab stopiga valjumisi => voiduprotsent TOUSEB.
  Aga iga kaotus on nuud SUUREM. Kui signaalil serva ei ole, jaab
  oodatav vaartus samaks voi laheb halvemaks, sest kulud jaavad ja
  asummeetria kasvab. Suurem SL AITAB ainult siis, kui olemasolevad
  stopid olid "mura-stopid" — hind pooras peale stoppi ikkagi oiges
  suunas. Seda saab kontrollida: vaata, kas MAX_BAARE-ni hoidmine
  ilma SL-ita (SL = vaga suur) annab plussi.

TESTIME:
  1) TAIELIK TP x SL MAATRIKS, SL kuni 6 ATR (eelmine oli max 1.0)
  2) SL = lopmatus (ainult TP voi aeg) — kas stopp uldse teeb kahju?
  3) parim variant: puhas walk-forward (1. pool vs 2. pool)
  4) null-jaotus: sama maatriks juhusliku suunaga
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(1309)
OUT = "sl_suurem_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

H1 = {"XAUUSD": "XAUUSD_h1.csv", "SPX": "SPX_h1.csv",
      "NAS100": "NAS100_h1.csv", "WTI": "WTI_h1.csv"}
COST_BP = {"XAUUSD": 0.4, "SPX": 0.4, "NAS100": 0.3, "WTI": 1.5}


def load(f):
    p = os.path.join(R.DATA, f)
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()[["open", "high", "low", "close"]]


def atr(d, n=14):
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def simuleeri(d, sym, N=50, tp_atr=0.5, sl_atr=1.0, trend_filter=False,
              kinnitus=True, max_baare=48, juhuslik=False, rng_=None):
    """
    Teekonna-teadlik H1 simulatsioon. Tagastab (tootlused, valjumispohjused).
    valjumispohjus: 0 = TP, 1 = SL, 2 = aeg.
    juhuslik=True => signaali SUUND juhuslikustatakse (null-test).
    """
    o, h, l, c = d["open"], d["high"], d["low"], d["close"]
    a = atr(d)
    vast = h.rolling(N).max().shift(1)
    tugi = l.rolling(N).min().shift(1)
    ema = c.ewm(span=200).mean()
    rt = 2 * COST_BP[sym] / 1e4

    ov, ot, oc, oa = vast.values, tugi.values, c.values, a.values
    oh, ol, oo, oe = h.values, l.values, o.values, ema.values
    n = len(d)
    teh, pohjus = [], []
    i = 210
    while i < n - 1:
        if not (np.isfinite(oa[i]) and oa[i] > 0 and np.isfinite(ov[i])):
            i += 1
            continue
        suund = 0
        if oh[i] >= ov[i] and (oc[i] < ov[i] if kinnitus else True):
            suund = -1
        elif ol[i] <= ot[i] and (oc[i] > ot[i] if kinnitus else True):
            suund = 1
        if suund == 0:
            i += 1
            continue
        if trend_filter:
            if suund == 1 and oc[i] < oe[i]:
                i += 1
                continue
            if suund == -1 and oc[i] > oe[i]:
                i += 1
                continue
        if juhuslik:
            suund = int(rng_.choice([-1, 1]))
        entry = oo[i + 1]
        tp = entry + suund * tp_atr * oa[i]
        sl = entry - suund * sl_atr * oa[i]
        tulem, ph = None, 2
        for j in range(i + 1, min(i + 1 + max_baare, n)):
            hi, lo = oh[j], ol[j]
            tp_hit = (hi >= tp) if suund == 1 else (lo <= tp)
            sl_hit = (lo <= sl) if suund == 1 else (hi >= sl)
            if tp_hit and sl_hit:
                tulem, ph = -sl_atr * oa[i] / entry, 1   # konservatiivne
                break
            if tp_hit:
                tulem, ph = tp_atr * oa[i] / entry, 0
                break
            if sl_hit:
                tulem, ph = -sl_atr * oa[i] / entry, 1
                break
        if tulem is None:
            j = min(i + max_baare, n - 1)
            tulem, ph = suund * (oc[j] - entry) / entry, 2
        teh.append(tulem - rt)
        pohjus.append(ph)
        i = j + 1
    return np.array(teh), np.array(pohjus)


def stat(t):
    if len(t) < 30:
        return None
    eq = np.cumprod(1 + t)
    return dict(n=len(t), keskm=t.mean(), wr=100 * (t > 0).mean(),
                sh=t.mean() / t.std() * math.sqrt(252) if t.std() > 0 else 0,
                kokku=eq[-1] - 1)


DATA = {}
for sym, f in H1.items():
    d = load(f)
    if d is not None and len(d) >= 2000:
        DATA[sym] = d

TP_LIST = (0.25, 0.5, 1.0, 1.5, 2.0, 3.0)
SL_LIST = (1.0, 1.5, 2.0, 3.0, 4.0, 6.0)

w("=" * 104)
w("S/R STRATEEGIA SUUREMA STOP LOSSIGA — TP x SL maatriks, H1, teekonna-teadlik")
w("=" * 104)
w("arv lahtris = keskmine tootlus tehingu kohta, BAASPUNKTIDES (kulud maha arvatud)")
w("max hoidmisaeg 48 tundi, trendifilter VALJAS (annab rohkem tehinguid)")

koik = {}
for sym, d in DATA.items():
    w("")
    w(f"--- {sym}  ({d.index[0].date()} .. {d.index[-1].date()}, {len(d)} H1 baari) ---")
    hdr = "  " + "TP / SL".rjust(9) + "".join(f"{s:>11.1f}" for s in SL_LIST)
    w(hdr)
    w("  " + "-" * (9 + 11 * len(SL_LIST)))
    for tp_a in TP_LIST:
        rida = f"  {tp_a:>9.2f}"
        for sl_a in SL_LIST:
            t, ph = simuleeri(d, sym, tp_atr=tp_a, sl_atr=sl_a)
            s = stat(t)
            koik[(sym, tp_a, sl_a)] = (t, ph, s)
            rida += "       n/a" if s is None else f"{1e4*s['keskm']:>+11.2f}"
        w(rida)

# ── kokkuvote: kas suurem SL aitab? ──────────────────────────────
w("")
w("=" * 104)
w("1) KAS SUUREM SL AITAB? (keskmine ule koigi instrumentide ja TP-de)")
w("=" * 104)
w(f"  {'SL (ATR)':>9s} {'keskm bp':>11s} {'plussis':>10s} {'võit%':>8s} "
  f"{'TP-ga':>7s} {'SL-iga':>8s} {'ajaga':>7s}")
w("  " + "-" * 64)
for sl_a in SL_LIST:
    vs = [koik[(s, tp, sl_a)] for s in DATA for tp in TP_LIST
          if koik[(s, tp, sl_a)][2] is not None]
    if not vs:
        continue
    keskm = np.mean([v[2]["keskm"] for v in vs])
    plus = sum(1 for v in vs if v[2]["keskm"] > 0)
    wr = np.mean([v[2]["wr"] for v in vs])
    ph = np.concatenate([v[1] for v in vs])
    w(f"  {sl_a:>9.1f} {1e4*keskm:>+11.2f} {plus:>6d}/{len(vs):<3d} {wr:>7.1f}% "
      f"{100*(ph==0).mean():>6.1f}% {100*(ph==1).mean():>7.1f}% {100*(ph==2).mean():>6.1f}%")

w("")
w(f"  {'TP (ATR)':>9s} {'keskm bp':>11s} {'plussis':>10s}")
w("  " + "-" * 32)
for tp_a in TP_LIST:
    vs = [koik[(s, tp_a, sl)] for s in DATA for sl in SL_LIST
          if koik[(s, tp_a, sl)][2] is not None]
    keskm = np.mean([v[2]["keskm"] for v in vs])
    plus = sum(1 for v in vs if v[2]["keskm"] > 0)
    w(f"  {tp_a:>9.2f} {1e4*keskm:>+11.2f} {plus:>6d}/{len(vs):<3d}")

# ── 2) SL = lopmatus ─────────────────────────────────────────────
w("")
w("=" * 104)
w("2) STOPP HOOPIS ARA (SL = 50 ATR ~ lõpmatus): kas stopp ise teeb kahju?")
w("=" * 104)
w(f"  {'instr':8s} {'TP':>6s} {'teh':>6s} {'võit%':>7s} {'keskm bp':>10s} {'kokku':>9s}")
w("  " + "-" * 50)
for sym, d in DATA.items():
    for tp_a in (0.5, 1.0, 2.0):
        t, ph = simuleeri(d, sym, tp_atr=tp_a, sl_atr=50.0)
        s = stat(t)
        if s is None:
            continue
        w(f"  {sym:8s} {tp_a:>6.2f} {s['n']:>6d} {s['wr']:>6.1f}% "
          f"{1e4*s['keskm']:>+10.2f} {100*s['kokku']:>+8.1f}%")

# ── 3) parim variant: puhas walk-forward ─────────────────────────
w("")
w("=" * 104)
w("3) PARIM VARIANT — PUHAS WALK-FORWARD (vali 1. poolelt, testi 2. poolel)")
w("=" * 104)
for sym in DATA:
    read = []
    for tp_a in TP_LIST:
        for sl_a in SL_LIST:
            t, ph, s = koik[(sym, tp_a, sl_a)]
            if s is None or len(t) < 60:
                continue
            m = len(t) // 2
            read.append((tp_a, sl_a, t[:m].mean(), t[m:].mean(), s["keskm"]))
    if not read:
        continue
    parim = max(read, key=lambda r: r[2])          # valik AINULT 1. poole pealt
    w(f"  {sym:8s} parim 1. poolel: TP {parim[0]:.2f} / SL {parim[1]:.1f}  "
      f"IS {1e4*parim[2]:+7.2f}bp  ->  OOS {1e4*parim[3]:+7.2f}bp"
      f"{'  <<< OOS plussis' if parim[3] > 0 else ''}")

# ── 4) null-jaotus ───────────────────────────────────────────────
w("")
w("=" * 104)
w("4) NULL-JAOTUS — sama maatriks, aga signaali SUUND juhuslik (kulud jäävad)")
w("=" * 104)
paris = sum(1 for k, v in koik.items() if v[2] is not None and v[2]["keskm"] > 0)
kokku_n = sum(1 for v in koik.values() if v[2] is not None)
sims = []
for k in range(10):
    n_ok = 0
    for sym, d in DATA.items():
        for tp_a in TP_LIST:
            for sl_a in SL_LIST:
                t, ph = simuleeri(d, sym, tp_atr=tp_a, sl_atr=sl_a,
                                  juhuslik=True, rng_=rng)
                s = stat(t)
                if s is not None and s["keskm"] > 0:
                    n_ok += 1
    sims.append(n_ok)
sims = np.array(sims)
p = float((sims >= paris).mean())
w(f"  PÄRIS signaal : {paris} plussis {kokku_n}-st")
w(f"  JUHUSLIK suund (10 katset): keskmine {sims.mean():.1f}, "
  f"min {sims.min()}, max {sims.max()}")
w(f"  p = {p:.3f}  =>  "
  f"{'serv on päris' if p < 0.05 else 'EI OLE JUHUSLIKUST PAREM'}")
w("VALMIS")
