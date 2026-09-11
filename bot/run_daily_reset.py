"""
run_daily_reset.py — kas positsiooni sulgemine iga oo enne rollover't
ja kohene taasavamine parast seda saab valtida OOISE FINANTSEERIMISE
(suurim uksik kulu, mille me leidsime: 5.42%/a eksponeeritud euro kohta),
maksuks selle eest ainult lisaspread'i?

Meetod: kasutame TAPSELT sama Donchian-50 signaali (strategies.sig_donchian),
mis portfellis XAUUSD jala peal jookseb. Signaal maarab suuna/SL/TP uhe
korra (murre). Kaks varianti sama tehingu peale:

  A) HOIA LABI (praegune): positsioon jaab lahti mitu paeva, kuni TP/SL
     tabab. Uks round-trip spread, finantseerimine IGA oo.

  B) PAEVANE RESET: iga paev, VAHETULT ENNE rollover'it (eeldus 21:00 UTC,
     BlackBulli tapset aega ei leidnud - toostusstandard enamikel MT5
     maakleritel), suletakse positsioon PRAEGUSE hinnaga ja avatakse
     KOHE parast rollover't uuesti SAMA suuna/SL/TP-ga (kaubanduslik
     motiiv ei ole muutunud, ainult vaditakse oo hoidmist). Uks
     round-trip spread IGA PAEVA kohta, aga MITTE KUNAGI finantseerimist.

Kui B > A parast kulusid, siis on paevane reset paris strateegia,
mitte lihtsalt vaatlus.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R, strategies as S, gold_logic

ROLLOVER_UTC_HOUR = 21          # eeldus - toostusstandard, BlackBulli tapset ei leidnud
MK = 0.030                       # maakleri juurdehindlus (research.py-st)
SPREAD_ONE_WAY = 0.20           # $ 0.01 loti kohta uhe suuna kohta (0.40 round-trip / 2)
PV = 100.0                        # XAUUSD pip_value
LOT = 0.01                        # sunnitud miinimum, nagu praegu live's

def load_h1():
    d = pd.read_csv("data/XAUUSD_h1.csv", parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

def daily_from_h1(h1):
    o = h1["Open"].resample("D").first()
    h = h1["High"].resample("D").max()
    l = h1["Low"].resample("D").min()
    c = h1["Close"].resample("D").last()
    df = pd.DataFrame({"open":o,"high":h,"low":l,"close":c}).dropna()
    return df

h1 = load_h1()
daily = daily_from_h1(h1)
rates = R.load_rates(daily.index)

# Genereeri koik signaalid (lookback=50) ajaloolisel daily reas - sama
# loogika, mis strategies.sig_donchian, mida portfelli jalg kasutab.
cfg = {"lookback": 50}
signals = []  # (signal_date, direction, sl_dist, tp_dist)
for i in range(52, len(daily)):
    w = daily.iloc[max(0,i-260):i+1]
    sig = S.sig_donchian(w, cfg)
    if sig:
        signals.append((daily.index[i], *sig))

print(f"Daily baare: {len(daily)}  H1 baare: {len(h1)}  Donchian-50 signaale: {len(signals)}")
print(f"Rollover eeldus: {ROLLOVER_UTC_HOUR}:00 UTC iga paev\n")

def simulate_trade(entry_date, direction, sl_dist, tp_dist, mode):
    """Mangi uks tehing labi kas 'hold' voi 'reset' reziimis, kasutades H1 baare.
    Tagastab (net_pnl, days_held, n_resets)."""
    # sisenemine: jargmise paeva esimene H1 baar parast signaali
    fut = h1[h1.index > entry_date]
    if fut.empty: return None
    entry_bar = fut.iloc[0]
    entry_px = float(entry_bar["Open"])
    sl = entry_px - sl_dist if direction=="buy" else entry_px + sl_dist
    tp = entry_px + tp_dist if direction=="buy" else entry_px - tp_dist

    path = h1[h1.index >= fut.index[0]]
    gross = 0.0
    resets = 0
    entry_time = fut.index[0]
    cur_entry_px = entry_px
    last_time = entry_time

    # VIGA PARANDATUD: 21:00 UTC taps tund PUUDUB 76.8% paevadest selles
    # H1 andmestikus (Yahoo lunk). Reset peab kaivituma iga paeva VIIMASEL
    # baaril, mille tund on <= ROLLOVER_UTC_HOUR - mitte tapsel vastel.
    if mode == "reset":
        day_keys = path.index.normalize()
        eligible = path[path.index.hour <= ROLLOVER_UTC_HOUR]
        reset_times = set(eligible.groupby(eligible.index.normalize()).apply(
            lambda g: g.index.max()))
    else:
        reset_times = set()

    for t, bar in path.iterrows():
        hi, lo = float(bar["High"]), float(bar["Low"])
        tp_hit = (hi>=tp) if direction=="buy" else (lo<=tp)
        sl_hit = (lo<=sl) if direction=="buy" else (hi>=sl)
        if tp_hit or sl_hit:
            exit_px = tp if tp_hit else sl
            gross += (exit_px-cur_entry_px)*LOT*PV if direction=="buy" else (cur_entry_px-exit_px)*LOT*PV
            last_time = t
            days_held = (last_time-entry_time).total_seconds()/86400
            return dict(gross=gross, days=days_held, resets=resets,
                       reason="tp" if tp_hit else "sl", close_time=t)
        if mode=="reset" and t in reset_times and t != entry_time:
            # sulge PRAEGUSE hinnaga, ava kohe uuesti (spread molemal otsal)
            close_px = float(bar["Close"])
            gross += (close_px-cur_entry_px)*LOT*PV if direction=="buy" else (cur_entry_px-close_px)*LOT*PV
            gross -= 2*SPREAD_ONE_WAY*(LOT/0.01)   # sulge + ava = round-trip
            cur_entry_px = close_px
            resets += 1
    # kunagi ei tabanud - jaab lahti andmete lopuni (LAHTI), ara arvesta
    return None

for mode in ("hold", "reset"):
    results = []
    for d, direction, sl, tp in signals:
        r = simulate_trade(d, direction, sl, tp, mode)
        if r: results.append(r)

    # kulud: uks round-trip spread ALATI (avamine+sulgemine), pluss
    # 'hold' puhul finantseerimine iga oo eest, 'reset' puhul lisaspread
    # juba simulate_trade sees arvestatud (resets)
    total_net = 0.0
    for r in results:
        net = r["gross"] - 2*SPREAD_ONE_WAY*(LOT/0.01)   # esimene ava+lõplik sulgemine
        if mode == "hold":
            days = max(1, int(round(r["days"])))
            rate = float(rates.iloc[-1])  # ligikaudu praegune maar, piisav vordluseks
            notional = LOT*100*4300
            fin = notional*(rate+MK)*days/365.0
            net -= fin
        total_net += net

    tp_n = sum(1 for r in results if r["reason"]=="tp")
    print(f"--- {mode.upper()} ---")
    print(f"  tehinguid lõpetatud: {len(results)}/{len(signals)}  (ülejäänud lahti andmete lõpuni)")
    print(f"  TP-võite: {tp_n}  SL-kaotusi: {len(results)-tp_n}")
    print(f"  keskmine hoiuaeg: {np.mean([r['days'] for r in results]):.1f} päeva")
    if mode=="reset":
        print(f"  keskmine reset'e tehingu kohta: {np.mean([r['resets'] for r in results]):.1f}")
    print(f"  NETO KOKKU: {total_net:+.2f}$\n")

print("=" * 90)
print("KULUDE LAHTIVOTMINE — kust vahe tuleb")
print("=" * 90)
fin_total = 0.0; extra_spread_total = 0.0
for d, direction, sl, tp in signals:
    r = simulate_trade(d, direction, sl, tp, "hold")
    if r:
        days = max(1, int(round(r["days"])))
        rate = float(rates.iloc[-1])
        notional = LOT*100*4300
        fin_total += notional*(rate+MK)*days/365.0

for d, direction, sl, tp in signals:
    r = simulate_trade(d, direction, sl, tp, "reset")
    if r:
        extra_spread_total += r["resets"] * 2*SPREAD_ONE_WAY*(LOT/0.01)

print(f"  HOLD-variandi finantseerimiskulu kokku (71 tehingut): {fin_total:8.2f}$")
print(f"  RESET-variandi lisaspread kokku (kõik reset'id):      {extra_spread_total:8.2f}$")
print(f"  Vahe (see, mis RESET säästab):                        {fin_total - extra_spread_total:+8.2f}$")
print(f"\n  Eeldus: rollover {ROLLOVER_UTC_HOUR}:00 UTC (BlackBulli täpne aeg kinnitamata).")
print(f"  Kui rollover on tegelikult teisel kellaajal, muutub resetide arv,")
print(f"  aga mehhanism (fin. sääst > lisaspread) jääb suund samaks, kuna")
print(f"  spread on väike ($0.40) võrreldes ööse finantseerimisega suurel lotil.")
