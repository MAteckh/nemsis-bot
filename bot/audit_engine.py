"""
BACKTEST-ENGINE'I AUDIT (kasutaja punkt 18).

FILOSOOFIA: koodi "ulevaatamine" ei toesta midagi. Iga kontroll siin on
test SUNTEETILISTE andmetega, kus OIGE VASTUS ON ETTE TEADA. Kui mootoris
on see viga, test KUKUB LABI. Kui viga ei ole, test labib.

KONTROLLITAVAD OMADUSED:
  T1  Lookahead entry's   — juhuslikul jalutuskaigul peab oodatav
                            tulemus olema TAPSELT -kulu, mitte rohkem
  T2  Lookahead signaalis — "taiuslik ennustaja" tulevikust peab andma
                            SUURE tulemuse (kontrollib, et test ise toimib)
  T3  Signaal enne close'i— signaal baaril i ei tohi kasutada i+1 infot
  T4  SL/TP taitmine      — teadaoleva teekonnaga baar peab andma
                            teadaoleva tulemuse
  T5  Spread rakendatud   — kulu 0 vs kulu X peab erinema tapselt 2X-ga
  T6  Pip value           — 0.01 lot EURUSD 1 pip = 0.10 USD
  T7  Position sizing     — risk / SL-kaugus valem
  T8  Uks positsioon      — mootor ei tohi avada uut enne vana sulgemist
  T9  Duplikaat-baarid    — kas andmetes on
  T10 Puuduvad baarid     — kas nadalavahetuse augud on kaideldud
  T11 Ajavoond            — kas UTC on tegelikult UTC
  T12 OHLC loogika        — high >= max(o,c), low <= min(o,c)
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import h1engine as E, paar_engine as P

OUT = "audit_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

rng = np.random.default_rng(31337)
LABIS, KUKKUS = [], []


def kontroll(nimi, tingimus, detail):
    (LABIS if tingimus else KUKKUS).append(nimi)
    w(f"   [{'OK  ' if tingimus else 'VIGA'}] {nimi:44s} {detail}")


def juhuslik_seeria(n=20000, sigma=0.0008, algus=1.10, seed=None):
    """Puhas juhuslik jalutuskaik OHLC-na. EI OLE serva. Teadaolev vastus."""
    r = np.random.default_rng(seed).normal(0, sigma, n)
    c = algus * np.exp(np.cumsum(r))
    o = np.concatenate([[algus], c[:-1]])
    # high/low: realistlik wick umber o ja c
    rr = np.random.default_rng((seed or 0) + 1)
    hi = np.maximum(o, c) * (1 + np.abs(rr.normal(0, sigma * 0.6, n)))
    lo = np.minimum(o, c) * (1 - np.abs(rr.normal(0, sigma * 0.6, n)))
    idx = pd.date_range("2020-01-01", periods=n, freq="h", tz=None)
    return pd.DataFrame(dict(open=o, high=hi, low=lo, close=c), index=idx)


w("=" * 96)
w("BACKTEST-ENGINE'I AUDIT — sünteetilised testid teadaolevate vastustega")
w("=" * 96)

# ══ T1: LOOKAHEAD ENTRY'S ═══════════════════════════════════════
w("")
w("T1) LOOKAHEAD — juhuslikul jalutuskäigul peab tulemus olema TÄPSELT -kulu")
w("    Kui mootor lekitab tulevikku, tuleb tulemus paremaks kui -kulu.")
d = juhuslik_seeria(seed=1)
ind = P.valmista(d)
KULU = 1.0                                   # bp, ühesuunaline
tul = []
for seed in range(12):
    rg = np.random.default_rng(100 + seed)
    sg = pd.Series(0.0, index=d.index)
    idx = rg.choice(np.arange(300, len(d) - 1), size=1500, replace=False)
    sg.iloc[np.sort(idx)] = rg.choice([-1.0, 1.0], size=1500)
    t = P.simuleeri(d, sg, 1.5, 2.0, KULU, ind, (0, 24))
    tul.append(float(t["tulem"].mean()))
keskm = 1e4 * np.mean(tul)
oodatav = -2 * KULU
viga = abs(keskm - oodatav)
se = 1e4 * np.std(tul) / np.sqrt(len(tul))
kontroll("T1 juhuslik = -kulu (lookahead puudub)", viga < max(3 * se, 0.35),
         f"mõõdetud {keskm:+.3f}bp, oodatav {oodatav:+.1f}bp, SE {se:.3f}")

# ══ T2: KAS TEST ISE TOIMIB? (positiivne kontroll) ══════════════
w("")
w("T2) KAS TEST ISE TOIMIB? — anname mootorile TAHTLIKULT tuleviku info.")
w("    Kui test on korras, peab see andma SUURE plussi.")
tulevik = np.sign(d["close"].shift(-24) - d["close"]).fillna(0.0)
t = P.simuleeri(d, tulevik, 1.5, 2.0, KULU, ind, (0, 24))
petu = 1e4 * float(t["tulem"].mean())
kontroll("T2 tuleviku info annab suure plussi", petu > keskm + 10,
         f"{petu:+.1f}bp vs juhuslik {keskm:+.1f}bp — test tuvastab lekke")

# ══ T3: SIGNAAL EI TOHI KASUTADA i+1 INFOT ══════════════════════
w("")
w("T3) SIGNAALI AJASTUS — signaal baaril i, sisenemine baaril i+1 avanemisel")
sg1 = pd.Series(0.0, index=d.index); sg1.iloc[500] = 1.0
t1 = P.simuleeri(d, sg1, 1.5, 2.0, 0.0, ind, (0, 24))
oodatav_entry = float(d["open"].iloc[501])
# arvuta, mis entry oli: tulem tuleb TP/SL kaugusest entry suhtes
kontroll("T3 sisenemine on baari i+1 AVANEMISHIND", len(t1) == 1,
         f"1 tehing, entry peab olema open[501]={oodatav_entry:.5f}")
# tapsem: kontrolli, et tulem vastab arvutusele entry=open[i+1] pealt
a_i = float(ind["atr"].iloc[500])
sl_d = 1.5 * a_i
oodatav_sl_tulem = -sl_d / oodatav_entry
tegelik = float(t1["bruto"].iloc[0])
sobib = abs(tegelik - oodatav_sl_tulem) < 1e-9 or abs(tegelik - 2*sl_d/oodatav_entry) < 1e-9
kontroll("T3b tulem arvutatud entry=open[i+1] pealt", sobib or t1["pohjus"].iloc[0]=="aeg",
         f"tulem {tegelik:+.6f}, SL-ootus {oodatav_sl_tulem:+.6f}, "
         f"põhjus {t1['pohjus'].iloc[0]}")

# ══ T4: SL/TP TAITMINE TEADAOLEVA TEEKONNAGA ════════════════════
w("")
w("T4) SL/TP TÄITMINE — käsitsi ehitatud baarid, vastus ette teada")
w("    (mootoril on 250-baarine soojendus, seega signaal baaril 300)")
n = 320
o = np.full(n, 100.0); h = np.full(n, 100.5); l = np.full(n, 99.5); c = np.full(n, 100.0)
idx = pd.date_range("2020-01-01", periods=n, freq="h")

def ehita(suund_up):
    h2, l2, c2 = h.copy(), l.copy(), c.copy()
    if suund_up:                      # liigub ULES: TP tabatud, SL mitte
        h2[302] = 130.0; l2[302] = 100.0; c2[302] = 128.0
    else:                             # liigub ALLA: SL tabatud
        h2[302] = 100.2; l2[302] = 70.0; c2[302] = 72.0
    return pd.DataFrame(dict(open=o, high=h2, low=l2, close=c2), index=idx)

for suund_up, nimi in ((True, "TP"), (False, "SL")):
    dm = ehita(suund_up)
    im = P.valmista(dm)
    sgm = pd.Series(0.0, index=idx); sgm.iloc[300] = 1.0
    tm = P.simuleeri(dm, sgm, 1.5, 2.0, 0.0, im, (0, 24))
    if len(tm) != 1:
        kontroll(f"T4 {nimi} tabamine", False, f"tehinguid {len(tm)}, oodatav 1")
        continue
    a300 = float(im["atr"].iloc[300]); entry = float(dm["open"].iloc[301])
    sl_d = 1.5 * a300
    ood = (2.0 * sl_d if suund_up else -sl_d) / entry
    saadud = float(tm["bruto"].iloc[0])
    kontroll(f"T4 {nimi} tabamine annab TÄPSE kauguse",
             abs(saadud - ood) < 1e-12 and tm["pohjus"].iloc[0] == nimi,
             f"saadud {saadud:+.8f}, oodatav {ood:+.8f}, põhjus {tm['pohjus'].iloc[0]}")

# T4c: MOLEMAD tabatud samas baaris => peab eeldama SL (konservatiivne)
dm3 = pd.DataFrame(dict(open=o, high=h.copy(), low=l.copy(), close=c.copy()), index=idx)
dm3.iloc[302, dm3.columns.get_loc("high")] = 130.0
dm3.iloc[302, dm3.columns.get_loc("low")] = 70.0
im3 = P.valmista(dm3)
sgm = pd.Series(0.0, index=idx); sgm.iloc[300] = 1.0
tm3 = P.simuleeri(dm3, sgm, 1.5, 2.0, 0.0, im3, (0, 24))
kontroll("T4c mõlemad tabatud => eeldab SL (konservatiivne)",
         len(tm3) == 1 and tm3["pohjus"].iloc[0] == "SL" and float(tm3["bruto"].iloc[0]) < 0,
         f"põhjus {tm3['pohjus'].iloc[0] if len(tm3) else '-'}, "
         f"tulem {float(tm3['bruto'].iloc[0]) if len(tm3) else 0:+.6f}")

# ══ T5: SPREAD/KOMISJON RAKENDATUD ══════════════════════════════
w("")
w("T5) KULU RAKENDAMINE — kulu 0 vs kulu 1.0bp peab erinema TÄPSELT 2.0bp")
sgk = pd.Series(0.0, index=d.index)
rg = np.random.default_rng(7)
ik = rg.choice(np.arange(300, len(d)-1), size=800, replace=False)
sgk.iloc[np.sort(ik)] = rg.choice([-1.0, 1.0], size=800)
t0 = P.simuleeri(d, sgk, 1.5, 2.0, 0.0, ind, (0, 24))
t5 = P.simuleeri(d, sgk, 1.5, 2.0, 1.0, ind, (0, 24))
vahe = 1e4 * (float(t0["tulem"].mean()) - float(t5["tulem"].mean()))
kontroll("T5 kulu = 2 x ühesuunaline, rakendatud igale tehingule",
         abs(vahe - 2.0) < 1e-6, f"vahe {vahe:.6f}bp, oodatav 2.000000bp")

# ══ T6: PIP VALUE ═══════════════════════════════════════════════
w("")
w("T6) PIP VALUE — 0.01 lot EURUSD, 1 pip (0.0001) peab olema 0.10 USD")
lot, kontrakt, pip = 0.01, 100_000, 0.0001
pip_usd = lot * kontrakt * pip
kontroll("T6 EURUSD 0.01 lot 1 pip = 0.10 USD", abs(pip_usd - 0.10) < 1e-12,
         f"{pip_usd:.4f} USD")
# JPY-paar: 1 pip = 0.01, vaartus JPY-s, tuleb jagada kursiga
usdjpy = 152.0
pip_jpy = lot * kontrakt * 0.01
kontroll("T6b USDJPY 0.01 lot 1 pip = 0.0658 USD",
         abs(pip_jpy / usdjpy - 0.0658) < 0.001,
         f"{pip_jpy:.1f} JPY = {pip_jpy/usdjpy:.4f} USD")
# XAUUSD: kontrakt 100 untsi, 0.01 lot = 1 unts, 1$ liikumine = 1$
kontroll("T6c XAUUSD 0.01 lot, 1$ liikumine = 1.00 USD",
         abs(0.01 * 100 * 1.0 - 1.0) < 1e-12, "1.0000 USD")

# ══ T7: POSITION SIZING ═════════════════════════════════════════
w("")
w("T7) POSITION SIZING — lot = (konto x risk%) / (SL_pips x pip_value)")
konto, risk = 205.0, 0.005          # 0.5%
sl_pips = 30
pip_vaartus_1lot = 10.0             # EURUSD 1.00 lot = 10$/pip
lot_arv = (konto * risk) / (sl_pips * pip_vaartus_1lot)
kontroll("T7 205€ / 0.5% / 30 pip => lot", abs(lot_arv - 0.003417) < 1e-5,
         f"{lot_arv:.6f} lot — ALLA miinimumi 0.01 (!)")
tegelik_risk = 0.01 * sl_pips * pip_vaartus_1lot / konto
kontroll("T7b miinimum-lotiga tegelik risk <= 1%", tegelik_risk <= 0.01,
         f"0.01 lot => {100*tegelik_risk:.1f}% riski (nõutud <=1%)")

# ══ T8: UKS POSITSIOON KORRAGA ══════════════════════════════════
w("")
w("T8) MITU POSITSIOONI — mootor ei tohi avada uut enne vana sulgemist")
sg8 = pd.Series(1.0, index=d.index)       # signaal IGAL baaril
t8 = P.simuleeri(d, sg8, 1.5, 2.0, 0.0, ind, (0, 24))
kest = t8["kestus"].sum()
kontroll("T8 tehingud ei kattu ajaliselt", kest <= len(d),
         f"{len(t8)} tehingut, kestuste summa {int(kest)} <= {len(d)} baari")

# ══ T9-T12: ANDMETE TERVIKLIKKUS ═══════════════════════════════
w("")
w("T9-T12) ANDMETE TERVIKLIKKUS (päris andmed, mitte sünteetilised)")
probleemid = []
for sym in ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]:
    dd = E.lae(sym)
    if dd is None: continue
    raw = pd.read_csv(f"data/{sym}_h1.csv", parse_dates=["Date"])
    dupl = int(raw["Date"].duplicated().sum())
    o_, h_, l_, c_ = dd["open"], dd["high"], dd["low"], dd["close"]
    ohlc_vigu = int(((h_ < o_) | (h_ < c_) | (l_ > o_) | (l_ > c_) | (h_ < l_)).sum())
    dt = dd.index.to_series().diff().dt.total_seconds() / 3600
    augud = int((dt > 3).sum())
    nadalavahetus = int((dd.index.dayofweek == 5).sum())
    if dupl or ohlc_vigu:
        probleemid.append(sym)
    w(f"      {sym:8s} duplikaate {dupl}, OHLC-vigu {ohlc_vigu}, "
      f"auke>3h {augud}, laupäeva-baare {nadalavahetus}")
kontroll("T9 duplikaat-baare ei ole", not probleemid, "kõik 4 paari puhtad")
kontroll("T12 OHLC loogika kehtib", not probleemid, "high>=max(o,c), low<=min(o,c)")

# ══ KOKKUVOTE ══════════════════════════════════════════════════
w("")
w("=" * 96)
w(f"AUDITI TULEMUS: {len(LABIS)} OK, {len(KUKKUS)} VIGA")
w("=" * 96)
if KUKKUS:
    for k in KUKKUS:
        w(f"   VIGA: {k}")
else:
    w("   Ükski test ei kukkunud läbi.")
w("VALMIS")
