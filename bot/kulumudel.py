"""
kulumudel.py — realistlikud tehingukulud live-boti backtestile.

MIKS SEE VAJALIK ON (auditi leid):
backtest.py rida 136 utleb ausalt: "Order taitub tapselt `price` peal
(spread/slippage'i ei modelleerita eraldi — reaalsuses veidi halvem
tulemus kui siin naidatud)." Sona "veidi" on siin alahinnang, mida
tuleb MOOTA, mitte arvata.

MIS LIVE-BOTIS TEGELIKULT JUHTUB (mt5_connector.py rida 143-144, 234-235):
  ost  avaneb  tick.ask     ost  sulgub  tick.bid
  muuk avaneb  tick.bid     muuk sulgub  tick.ask
=> iga tehing maksab TAIS spreadi, uks kord.
Lisaks: deviation=20 punkti lubatud libisemine (rida 163).

Backtest avab ja sulgeb MID-hinna peal => kulu 0.

SEE MOODUL ei muuda backtest.py-d. Ta votab tagastatud tehingute
nimekirja ja rakendab kulud tagantjarele. Nii ei saa ma kogemata
uurimistooriista katki teha.

KULUALLIKAD:
  1. spread        — BlackBull XAUUSD standard ~25-35 senti
  2. komisjon      — ECN-kontol ~$6/lot edasi-tagasi; standard 0
  3. slippage      — turuorderil, eriti SL-i taitmisel
  4. swap          — ule oo hoidmine, CFD finantseerimine ~5.42%/a
"""
import numpy as np

# BlackBull XAUUSD, konservatiivsed hinnangud dollarites untsi kohta
VAIKE = dict(
    spread_usd=0.30,        # $/unts, standard-konto tuupiline
    slippage_usd=0.10,      # $/unts keskmine, turuorderil
    sl_slippage_usd=0.20,   # $/unts LISAKS, kui valjub SL-iga (gapib labi)
    komisjon_lot=0.0,       # standard-konto: 0; ECN: ~6.0 per lot
    swap_aasta=0.0542,      # 5.42% aastas ule oo positsioonilt
    kontrakt=100.0,         # XAUUSD 1.00 lot = 100 untsi
)

# ECN-alternatiiv: kitsam spread, aga komisjon
ECN = dict(VAIKE, spread_usd=0.12, slippage_usd=0.06,
           sl_slippage_usd=0.12, komisjon_lot=6.0)


def tehingu_kulu(t, hind, p=None):
    """Uhe tehingu kulu EURODES (~USD). t = Trade objekt."""
    p = p or VAIKE
    untse = t.lot * p["kontrakt"]
    # spread makstakse uks kord (ost ask'ilt, sulgemine bid'ilt)
    kulu = p["spread_usd"] * untse
    # slippage sisenemisel + valjumisel
    kulu += 2 * p["slippage_usd"] * untse
    # SL-valjumine libiseb rohkem
    if t.reason and "sl" in str(t.reason).lower():
        kulu += p["sl_slippage_usd"] * untse
    # komisjon (edasi-tagasi, loti kohta)
    kulu += p["komisjon_lot"] * t.lot
    # swap ule oo
    if t.closed_at is not None and t.opened_at is not None:
        oid = max((t.closed_at - t.opened_at).days, 0)
        if oid > 0:
            kulu += hind * untse * p["swap_aasta"] / 365.0 * oid
    return kulu


def rakenda(res, hind_keskm, p=None, algbalanss=205.0):
    """
    Votab backtest.simulate_*() tulemuse ja arvutab kuludega tulemuse.
    Tagastab dict-i, mis vordleb kulude ja kuludeta versiooni.
    """
    p = p or VAIKE
    teh = res["trades"]
    if not teh:
        return None
    bruto = sum(t.pnl for t in teh if t.pnl is not None)
    kulud = [tehingu_kulu(t, hind_keskm, p) for t in teh]
    kulu_kokku = float(np.sum(kulud))
    neto = bruto - kulu_kokku
    # equity kuludega, et saada oige drawdown
    bal = algbalanss
    eq = [bal]
    for t, k in zip(teh, kulud):
        bal += (t.pnl or 0.0) - k
        eq.append(bal)
    eq = np.array(eq)
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    neto_teh = np.array([(t.pnl or 0.0) - k for t, k in zip(teh, kulud)])
    v, kk = neto_teh[neto_teh > 0], neto_teh[neto_teh <= 0]
    return dict(
        n=len(teh), bruto=bruto, kulu=kulu_kokku, neto=neto,
        kulu_teh=kulu_kokku / len(teh),
        bruto_teh=bruto / len(teh), neto_teh=neto / len(teh),
        wr=100 * float((neto_teh > 0).mean()),
        pf=float(v.sum() / abs(kk.sum())) if len(kk) and kk.sum() != 0 else float("inf"),
        maxdd=dd, lopp=float(eq[-1]),
        ruin=bool((eq <= algbalanss * 0.05).any()))
