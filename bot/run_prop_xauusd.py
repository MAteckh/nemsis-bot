"""
KAS PRAEGUNE STRATEEGIA LABIKS PROP-FIRMA HINDAMISE?

Praegu configis: XAUUSD donchian(50), paevabaarid, 45 EUR kahjumilagi,
max 1 positsioon.

TYYPILISED PROP-FIRMA REEGLID (FTMO-stiilis kaheastmeline):
  1. samm: +10% kasumit, max -5% PAEVAS, max -10% KOKKU
  2. samm: +5% kasumit, samad limiidid
  rahastatud: hoiad 80-90% kasumist

KRIITILINE ERINEVUS, mida testida:
Boti enda circuit breaker on -10% paevas / -15% nadalas. Prop-firma
lubab -5% paevas / -10% kokku. Ehk BOTI LIMIIDID ON LAIEMAD KUI
PROP-FIRMA OMAD — bot rikuks reegli enne, kui tema enda kaitse
kaivituks. Seda tuleb konfiguratsioonis muuta.

Teine kusimus: $25 000 kontol kaob miinimum-loti probleem. Kui palju
lotte saaks siis kaubelda ja mis on tulemus?
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import strategies as S
import research as R

rng = np.random.default_rng(2026)
OUT = "prop_xauusd_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, "data", "XAUUSD_d.csv"),
                parse_dates=["Date"]).set_index("Date").sort_index()
d = d[~d.index.duplicated(keep="last")]
d.columns = [c.strip().lower() for c in d.columns]
for c in ("open", "high", "low", "close"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna()[["open", "high", "low", "close"]]

PV = 100.0
ACC = 25000.0          # $25k prop-konto
RISK_PCT = 0.01        # 1% riski tehingu kohta (prop-sobiv)


def sig_risk(cap_frac):
    """Donchian 50, SL piiratud nii, et kahjum = cap_frac kontost."""
    def fn(win, cfg):
        b = S.sig_donchian(win, cfg)
        if b is None:
            return None
        dr, sl, tp = b
        return dr, sl, tp
    return fn


# Simuleeri tehingud ja saa R-multiplikaatorid (kahjum = -1R, kasum = xR)
r = S.simulate(d, S.sig_donchian, cfg={"lookback": 50},
               account_balance=200.0, pip_value=PV)
tr = [t for t in r["trades"] if t.closed_at]

# iga tehingu tulemus SL-i kordsetes (R)
R_mult = []
for t in tr:
    sl_dist = abs(t.entry - t.sl) if getattr(t, "sl", None) else None
    if not sl_dist or sl_dist <= 0:
        continue
    R_mult.append(t.pnl / (sl_dist * PV * t.lot))
R_mult = np.array([x for x in R_mult if np.isfinite(x)])

w("=" * 88)
w("1) STRATEEGIA R-MULTIPLIKAATORITES (sõltumatu konto suurusest)")
w("=" * 88)
w(f"   tehinguid          {len(R_mult)}")
w(f"   keskmine           {R_mult.mean():+.3f} R")
w(f"   võiduprotsent      {100*(R_mult > 0).mean():.1f}%")
w(f"   keskmine võit      {R_mult[R_mult > 0].mean():+.2f} R")
w(f"   keskmine kaotus    {R_mult[R_mult <= 0].mean():+.2f} R")
w(f"   parim              {R_mult.max():+.2f} R")
w(f"   halvim             {R_mult.min():+.2f} R")
s = np.sign(R_mult)
pikim = cur = 0
for v in s:
    cur = cur + 1 if v <= 0 else 0
    pikim = max(pikim, cur)
w(f"   pikim kaotusseeria {pikim} tehingut")
w(f"   tehinguid aastas   ~{len(R_mult)/6.7:.1f}")

w("")
w("=" * 88)
w("2) PROP-FIRMA 1. SAMM: +10% eesmärk, -5% päevas, -10% kokku")
w("=" * 88)
w("   Monte Carlo 20 000 katset, bootstrap R-multiplikaatoritest.")
w("")
w(f"   {'risk/tehing':>12s} {'LÄBIB':>9s} {'lõhub':>9s} {'aeg otsa':>10s} {'mediaan päevi':>14s}")
w("   " + "-" * 58)

AASTAS = len(R_mult) / 6.7          # tehinguid aastas


def sim(risk_pct, paevi=180, n=20000):
    k = max(int(AASTAS * paevi / 365), 3)
    idx = rng.integers(0, len(R_mult), size=(n, k))
    x = R_mult[idx] * risk_pct
    eq = np.cumprod(1 + x, axis=1)
    hit = eq >= 1.10
    # -10% kokku (staatiline algsaldolt)
    bust_total = eq <= 0.90
    # -5% paevas: uks tehing paevas, seega uks samm
    bust_day = x <= -0.05
    bust = bust_total | bust_day
    h, b = hit.any(1), bust.any(1)
    fh = np.where(h, hit.argmax(1), k + 1)
    fb = np.where(b, bust.argmax(1), k + 1)
    won = float((fh < fb).mean())
    lost = float((fb < fh).mean())
    days = fh[fh <= k] * 365 / AASTAS
    return won, lost, (float(np.median(days)) if len(days) else 0.0)


for rp in (0.005, 0.01, 0.015, 0.02, 0.03):
    won, lost, med = sim(rp)
    w(f"   {100*rp:11.1f}% {100*won:8.1f}% {100*lost:8.1f}% "
      f"{100*(1-won-lost):9.1f}% {med:14.0f}")

w("")
w("=" * 88)
w("3) MITU LOTTI SAAKS $25 000 KONTOL? (miinimum-loti probleem kaob)")
w("=" * 88)
atr = float(pd.concat([d["high"] - d["low"],
                       (d["high"] - d["close"].shift()).abs(),
                       (d["low"] - d["close"].shift()).abs()],
                      axis=1).max(axis=1).tail(14).mean())
w(f"   ATR(14) = {atr:.2f},  SL = 2 x ATR = {2*atr:.2f}")
w(f"   {'risk/tehing':>12s} {'$ riski':>10s} {'lot':>8s} {'vs 205€ konto':>16s}")
w("   " + "-" * 50)
for rp in (0.005, 0.01, 0.015, 0.02):
    risk_usd = ACC * rp
    lot = risk_usd / (2 * atr * PV)
    w(f"   {100*rp:11.1f}% {risk_usd:9.0f}$ {lot:8.2f} "
      f"{'0.01 (miinimum)':>16s}")
w("")
w(f"   205€ kontol oli sama SL = {2*atr*PV*0.01:.2f}€ = "
  f"{100*2*atr*PV*0.01/205:.0f}% kontost.")
w(f"   $25 000 kontol on üks miinimum-lot = "
  f"{100*2*atr*PV*0.01/ACC:.2f}% kontost.")

w("")
w("=" * 88)
w("4) ⚠️ BOTI LIMIIDID vs PROP-FIRMA LIMIIDID")
w("=" * 88)
w("   boti circuit breaker : -10% PÄEVAS,  -15% NÄDALAS")
w("   prop-firma tüüpiline :  -5% päevas,  -10% KOKKU")
w("")
w("   => BOTI LIMIIDID ON LAIEMAD. Bot rikuks prop-firma reegli ENNE,")
w("      kui tema enda kaitse käivituks. Konto suletaks.")
w("      Enne prop-kontol käivitamist TULEB need muuta:")
w("        circuit breaker päevalimiit  -10% -> -4%")
w("        nädalane / kogulimiit        -15% -> -8%")
w("      (jäta varu, sest limiit on tavaliselt EQUITY järgi ja")
w("       hõljuv kahjum loeb ka)")
w("VALMIS")
