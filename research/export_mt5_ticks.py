#!/usr/bin/env python3
"""
export_mt5_ticks.py — READ-ONLY MT5 tick-andmete eksportija (uurimistöö).

===============================================================================
SEE SKRIPT EI KAUPLE. SEE ON VÕIMATU KASUTADA TEHINGU TEGEMISEKS.
===============================================================================
  * ei kutsu KUNAGI mt5.order_send, mt5.order_check, mt5.order_modify,
    mt5.order_delete ega mt5.position_close (VERIFY: `grep -n "order_send\|
    order_check\|order_modify\|order_delete\|position_close" SEE_FAIL`
    peab tagastama TÜHJA — kontrolli seda enne käivitamist)
  * ei impordi main_v4.py, mt5_connector.py, config.py ega newstick_engine.py
    — ei puuduta live-boti koodi kuidagi, ei loe ega mõjuta
    NEWS_TICK_ENABLED't
  * kasutab AINULT MT5 turuandmete/kontometaandmete/ajaloo API'sid:
    symbols_get, symbol_info, symbol_info_tick, copy_ticks_from,
    copy_ticks_range
  * ei saada Telegrami, ei puuduta Oanorit, ei paljasta ühtegi API-võtit

KUS SEE TÖÖTAB
  See skript vajab PÄRIS MetaTrader5 Pythoni paketti (Windows-only) JA
  PÄRIS ühendust BlackBull MT5 terminaliga. See EI TÖÖTA selles
  liivakastis (Linux, MetaTrader5 pakett pole isegi installitav) —
  täpselt sama piirang, mis kehtib main_v4.py/mt5_connector.py kohta
  (vt CLAUDE.md). Käivita see VPS-il, kus BlackBull MT5 juba jookseb.

KASUTUS (VPS-il, kus MT5 terminal on avatud ja sisse logitud)
    set MT5_LOGIN=...      (Windowsil) / export MT5_LOGIN=...
    set MT5_PASSWORD=...
    set MT5_SERVER=...     (BlackBulli PÄRIS serverinimi, mitte oletus)

    # 1) Sümbolite avastamine + spetsifikatsioonid (ei ekspordi midagi)
    python export_mt5_ticks.py --mode discover

    # 2) Ajaloo saadavuse test ÜHE sümboli kohta (ei ekspordi midagi)
    python export_mt5_ticks.py --mode probe --symbol XAUUSD

    # 3) Väike valideerimis-eksport: viimased 24h, KOLM sümbolit korraga
    #    (BlackBull PÄRIS sümbolid, kinnitatud --mode discover'iga
    #    21.09.2026: nafta on "WTI", MITTE "USOIL")
    python export_mt5_ticks.py --mode validate24 --symbols XAUUSD,XAGUSD,WTI

    # 4) Suur eksport (KÄSITSI, ALLES pärast validate24 ülevaatust) —
    #    nõuab eksplitsiitset kinnituslippu, VAIKIMISI EI TEHTA
    python export_mt5_ticks.py --mode export --symbol XAUUSD \\
        --start 2026-03-01 --end 2026-09-01 --i-reviewed-validate24

Väljund: research/data/mt5_ticks/<SYMBOL>/<YYYY-MM-DD>.csv (üks fail
päeva kohta, et vältida hiiglaslikke ühefailiseid eksporte).

VEERUD (täpsuse säilitamine — EI ÜMARDATA midagi)
    timestamp_utc   ISO8601, millisekundi täpsusega (MT5 time_msc)
    timestamp_epoch_ms   toorne MT5 time_msc (taastatavuse jaoks)
    bid, ask, last  PÄRIS MT5 hinnad, muutmata täpsusega (str(), et
                    Pythoni float ei kaotaks/lisaks komakohti)
    volume, flags   MT5 enda väljad, muutmata

AJATSOON (vt allpool AJATSOONI_MÄRKUS)
    MT5 Pythoni API dokumentatsiooni järgi on tick.time / tick.time_msc
    UTC epohh (mitte "terminali kohalik aeg", nagu vanas MT4-s oli
    ebaselge). See skript EI TEE mingit tunni-nihutust — kasutab
    time_msc väärtust OTSE UTC epohhina. See on DOKUMENTEERITUD eeldus,
    MITTE selle skripti poolt empiiriliselt kinnitatud (ma ei saa seda
    ise käivitada). Kasutaja peab käivitamisel kontrollima: kas mõne
    TEADAOLEVA Tier1 avaldamise (nt NFP kell 12:30 UTC) juures on
    näha volüümi-hüpe ~kell 12:30 UTC ekspordi timestamp_utc veerus.
    Kui NIHKE on näha, ÄRA paranda seda skriptis vaikimisi — teata
    sellest, sest see viitab broker-spetsiifilisele ajanihkele, mis
    vajab eksplitsiitset, dokumenteeritud teisendust.
"""
from __future__ import annotations

import argparse
import csv
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

SILT = "MT5 TICK EXPORT — READ-ONLY — RESEARCH ONLY — NO TRADING"

# Kandidaatide otsingumustrid — EI EELDATA broker'i sümbolinimesid.
KANDIDAADID = {
    "gold":   ["XAU"],
    "silver": ["XAG"],
    "oil":    ["OIL", "WTI", "CRUDE", "USOIL", "UKOIL", "BRENT", "XTI", "XBR"],
}

# Ainult ETTEPANEK eelistusjärjekorrast, kui mitu kandidaati leitakse —
# EI VALITA vaikimisi automaatselt, kutsuja/kasutaja peab nägema KÕIKI
# kandidaate ja otsustama. Vt --mode discover väljund.
EELISTUS_OIL = ["USOIL", "WTI", "XTIUSD", "UKOIL", "BRENT", "XBRUSD", "CRUDE"]

VEERUD = ["timestamp_utc", "timestamp_epoch_ms", "bid", "ask", "last", "volume", "flags"]


# ═════════════════════════════════════════════════════════════
#  TURVAKAITSE — see funktsioon on AINUS koht, kus mt5.* kutsutakse,
#  et oleks lihtne auditeerida, ET SIIT EI LÄHE UHTEGI KAUPLEMIS-
#  KÄSKU LÄBI. Iga kutse siin on LOE-ainult (turg/konto/ajalugu).
# ═════════════════════════════════════════════════════════════

def yhenda():
    """Loe-ainult MT5 ühendus. EI kutsu KUNAGI trade-funktsioone."""
    if mt5 is None:
        print("❌ MetaTrader5 pakett pole installitud — see skript peab "
              "jooksma VPS-il, kus MT5 terminal on avatud (Windows-only).")
        return False
    login = int(os.environ.get("MT5_LOGIN", "0"))
    password = os.environ.get("MT5_PASSWORD", "")
    server = os.environ.get("MT5_SERVER", "")
    if not login or not password or not server:
        print("❌ MT5_LOGIN / MT5_PASSWORD / MT5_SERVER puuduvad keskkonnast. "
              "Need PEAVAD olema samad, mis VPS-il main_v4.py juba kasutab — "
              "see skript EI OLETA serverinime.")
        return False
    if not mt5.initialize():
        print(f"❌ mt5.initialize() ebaõnnestus: {mt5.last_error()}")
        return False
    if not mt5.login(login, password=password, server=server):
        print(f"❌ mt5.login() ebaõnnestus: {mt5.last_error()}")
        mt5.shutdown()
        return False
    info = mt5.account_info()
    if info is None:
        print("❌ mt5.account_info() tagastas None pärast edukat login'i — "
              "ühendus ebastabiilne, peatun.")
        return False
    print(f"✅ MT5 ühendatud (LOE-AINULT): konto {info.login} @ {server}, "
          f"trade_allowed(terminal)={mt5.terminal_info().trade_allowed if mt5.terminal_info() else '?'}")
    print("   See skript EI SAADA KUNAGI order_send/order_check/order_modify/"
          "order_delete/position_close — ainult turuandmete lugemine.")
    return True


def katkesta():
    if mt5 is not None:
        mt5.shutdown()


# ═════════════════════════════════════════════════════════════
#  1) SÜMBOLITE AVASTAMINE
# ═════════════════════════════════════════════════════════════

def leia_kandidaadid():
    """
    Tagastab dict {"gold": [...], "silver": [...], "oil": [...]} —
    KÕIK MT5 sümbolid, mille nimi sisaldab vastavat mustrit
    (case-insensitive). EI VALI automaatselt ÜHTEGI — ainult loetleb.
    """
    kandidaadid = {"gold": [], "silver": [], "oil": []}
    koik = mt5.symbols_get()
    if koik is None:
        print(f"❌ symbols_get() tagastas None: {mt5.last_error()}")
        return kandidaadid
    for s in koik:
        nimi_upper = s.name.upper()
        for votme, mustrid in KANDIDAADID.items():
            if any(m in nimi_upper for m in mustrid):
                kandidaadid[votme].append(s.name)
    for votme in kandidaadid:
        kandidaadid[votme].sort()
    return kandidaadid


def soovita_oil(kandidaadid_oil):
    """Ainult ETTEPANEK — ÄRA nimeta ümber "USOIL"-iks, kui see pole
    tegelikult broker'i sümbol. Tagastab esimese EELISTUS_OIL vaste
    KANDIDAATIDE hulgast, või None kui midagi ei leitud."""
    for eelistatud in EELISTUS_OIL:
        if eelistatud in kandidaadid_oil:
            return eelistatud
    return kandidaadid_oil[0] if kandidaadid_oil else None


def kirjelda_sumbol(symbol):
    """Loe-ainult symbol_info + symbol_info_tick. Tagastab dict või None."""
    if not mt5.symbol_select(symbol, True):
        print(f"⚠️ symbol_select({symbol}) ebaõnnestus: {mt5.last_error()}")
        return None
    info = mt5.symbol_info(symbol)
    if info is None:
        print(f"⚠️ symbol_info({symbol}) tagastas None: {mt5.last_error()}")
        return None
    tick = mt5.symbol_info_tick(symbol)
    d = {
        "symbol": symbol,
        "description": info.description,
        "digits": info.digits,
        "point": info.point,
        "trade_tick_size": info.trade_tick_size,
        "trade_tick_value": info.trade_tick_value,
        "trade_tick_value_profit": info.trade_tick_value_profit,
        "trade_tick_value_loss": info.trade_tick_value_loss,
        "contract_size": info.trade_contract_size,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "currency_base": info.currency_base,
        "currency_profit": info.currency_profit,
        "currency_margin": info.currency_margin,
        "trade_mode": info.trade_mode,
        "filling_mode": info.filling_mode,
        "spread_points": info.spread,
        "bid": tick.bid if tick else None,
        "ask": tick.ask if tick else None,
    }
    return d


def cmd_discover(args):
    print("\n[1] Sümbolite avastamine (KÕIK MT5-s nähtavad kandidaadid)...")
    kand = leia_kandidaadid()
    for votme, nimed in kand.items():
        print(f"\n  {votme.upper()} kandidaadid ({len(nimed)}):")
        for n in nimed:
            print(f"    - {n}")
        if not nimed:
            print("    (ühtegi ei leitud)")

    valik = {
        "gold": "XAUUSD" if "XAUUSD" in kand["gold"] else (kand["gold"][0] if kand["gold"] else None),
        "silver": "XAGUSD" if "XAGUSD" in kand["silver"] else (kand["silver"][0] if kand["silver"] else None),
        "oil": soovita_oil(kand["oil"]),
    }
    print("\n[2] ETTEPANEK (mitte automaatne valik — kontrolli enne kasutamist):")
    for votme, sym in valik.items():
        print(f"    {votme}: {sym or 'EI LEITUD ÜHTEGI KANDIDAATI'}")
    if valik["oil"] and valik["oil"] != "USOIL":
        print(f"    ⚠️ Nafta broker-sümbol EI OLE 'USOIL', vaid '{valik['oil']}' — "
              f"kasuta SEDA nime, ÄRA nimeta 'USOIL'-iks ümber.")

    print("\n[3] Spetsifikatsioonid valitud sümbolitele:")
    for votme, sym in valik.items():
        if not sym:
            continue
        d = kirjelda_sumbol(sym)
        if d is None:
            continue
        print(f"\n  --- {sym} ({votme}) ---")
        for k, v in d.items():
            print(f"    {k:26s} {v}")
    return valik


# ═════════════════════════════════════════════════════════════
#  2) AJALOO SAADAVUSE PROOVIMINE (ilma suurt eksporti tegemata)
# ═════════════════════════════════════════════════════════════

def proovi_ajalugu(symbol, kandidaat_algused=None):
    """
    Loe-ainult sondeerimine: mitu tükki väikeseid copy_ticks_from
    kutseid, et hinnata vanimat/uusimat saadaolevat tick'i ILMA kogu
    ajalugu alla laadimata. EI KIRJUTA ÜHTEGI faili.

    Tagastab dict: {"earliest": ..., "latest": ..., "est_count_24h": ...}
    """
    if kandidaat_algused is None:
        # Proovi mitut ankrupunkti minevikus — EI EELDA, et N kuud on olemas.
        nyyd = datetime.now(timezone.utc)
        kandidaat_algused = [nyyd - timedelta(days=d) for d in
                              (1, 7, 30, 90, 180, 365, 730)]

    tulemused = []
    for algus in kandidaat_algused:
        ticks = mt5.copy_ticks_from(symbol, algus, 5, mt5.COPY_TICKS_ALL)
        n = 0 if ticks is None else len(ticks)
        esimene = None
        if n > 0:
            esimene = datetime.fromtimestamp(int(ticks[0]["time_msc"]) / 1000.0, tz=timezone.utc)
        tulemused.append({"anker": algus.date().isoformat(), "leitud": n,
                          "esimene_tick_utc": esimene.isoformat() if esimene else None})
        print(f"    anker {algus.date()}: {n} tick'i tagastati "
              f"(esimene: {esimene.isoformat() if esimene else '—'})")

    # Uusim tick — viimased 5 minutit
    viimased = mt5.copy_ticks_from(symbol, datetime.now(timezone.utc) - timedelta(minutes=5),
                                    1000, mt5.COPY_TICKS_ALL)
    uusim = None
    if viimased is not None and len(viimased) > 0:
        uusim = datetime.fromtimestamp(int(viimased[-1]["time_msc"]) / 1000.0, tz=timezone.utc)

    return {"sondeeringud": tulemused, "uusim_tick_utc": uusim.isoformat() if uusim else None}


def cmd_probe(args):
    print(f"\n[PROOVI] {args.symbol} ajaloo saadavus (EI EKSPORDI midagi)...")
    if not mt5.symbol_select(args.symbol, True):
        print(f"❌ symbol_select({args.symbol}) ebaõnnestus")
        return
    tulemus = proovi_ajalugu(args.symbol)
    print(f"\n  Uusim tick: {tulemus['uusim_tick_utc']}")
    print("\n  ⚠️ See on ANKURPUNKTIDE sondeering, mitte täpne "
          "'vanim saadaolev tick' — copy_ticks_from(algus, count=5, ...) "
          "tagastab esimesed 5 tick'i ALATES sellest ajahetkest, kui neid "
          "on olemas. Kui vanima ankru (730 päeva) juures on ikka tulemus, "
          "võib PÄRIS ajalugu ulatuda veel kaugemale — see funktsioon "
          "annab ALAMTÕKKE, mitte täpset vanimat kuupäeva.")


# ═════════════════════════════════════════════════════════════
#  3) EKSPORT
# ═════════════════════════════════════════════════════════════

def ekspordi_paev(symbol, paev, valjundi_kaust):
    """Loe-ainult copy_ticks_range ÜHE UTC päeva kohta. Kirjutab CSV,
    tagastab (rea_arv, esimene_ts, viimane_ts, kvaliteedi_dict)."""
    algus = datetime(paev.year, paev.month, paev.day, tzinfo=timezone.utc)
    lopp = algus + timedelta(days=1)
    ticks = mt5.copy_ticks_range(symbol, algus, lopp, mt5.COPY_TICKS_ALL)
    if ticks is None or len(ticks) == 0:
        return 0, None, None, {}

    os.makedirs(os.path.join(valjundi_kaust, symbol), exist_ok=True)
    tee = os.path.join(valjundi_kaust, symbol, f"{paev.isoformat()}.csv")

    read = []
    for t in ticks:
        ms = int(t["time_msc"])
        ts = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
        read.append({
            "timestamp_utc": ts.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            "timestamp_epoch_ms": ms,
            "bid": repr(float(t["bid"])),
            "ask": repr(float(t["ask"])),
            "last": repr(float(t["last"])),
            "volume": float(t["volume"]),
            "flags": int(t["flags"]),
        })

    with open(tee, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=VEERUD)
        w.writeheader()
        w.writerows(read)

    kv = hinda_kvaliteeti(read)
    return len(read), read[0]["timestamp_utc"], read[-1]["timestamp_utc"], kv


def hinda_kvaliteeti(read):
    """Andmekvaliteedi kontroll ÜHE ekspordi (list dict) peale.
    EI KUSTUTA midagi — ainult loendab/lipustab."""
    n = len(read)
    if n == 0:
        return {}
    bids = [float(r["bid"]) for r in read]
    asks = [float(r["ask"]) for r in read]
    spreads = [a - b for a, b in zip(asks, bids)]
    tss = [r["timestamp_epoch_ms"] for r in read]

    duplikaat_ts = n - len({(r["timestamp_epoch_ms"], r["bid"], r["ask"]) for r in read})
    mitte_monotoonne = sum(1 for i in range(1, n) if tss[i] < tss[i - 1])
    puuduv_bid = sum(1 for b in bids if b <= 0)
    puuduv_ask = sum(1 for a in asks if a <= 0)
    null_negatiivne_spread = sum(1 for s in spreads if s <= 0)

    return {
        "n": n,
        "min_bid": min(bids), "max_bid": max(bids),
        "min_ask": min(asks), "max_ask": max(asks),
        "min_spread": min(spreads), "median_spread": statistics.median(spreads),
        "mean_spread": statistics.fmean(spreads), "max_spread": max(spreads),
        "null_negatiivne_spread": null_negatiivne_spread,
        "duplikaat_ridu": duplikaat_ts,
        "mitte_monotoonseid_jarjestikke": mitte_monotoonne,
        "puuduv_bid": puuduv_bid, "puuduv_ask": puuduv_ask,
    }


def cmd_validate24(args):
    valjundi_kaust = args.out
    nyyd = datetime.now(timezone.utc)
    tana = nyyd.date()
    eile = tana - timedelta(days=1)

    print(f"\n[VALIDATE24] Viimased 24h, sümbolid: {args.symbols}")
    print(f"  UTC vahemik: {eile} .. {tana}  (kaks päevafaili, kuna copy_ticks_range "
          f"jookseb UTC-kalendripäeva kaupa)")

    kokkuvote = []
    for symbol in args.symbols.split(","):
        symbol = symbol.strip()
        if not mt5.symbol_select(symbol, True):
            print(f"  ❌ {symbol}: symbol_select ebaõnnestus — jätan vahele")
            continue
        print(f"\n  --- {symbol} ---")
        for paev in (eile, tana):
            n, esimene, viimane, kv = ekspordi_paev(symbol, paev, valjundi_kaust)
            rida = {"symbol": symbol, "paev": paev.isoformat(), "ridu": n,
                    "esimene_ts": esimene, "viimane_ts": viimane, **kv}
            kokkuvote.append(rida)
            print(f"    {paev}: {n} tick'i"
                  + (f", spread median={kv.get('median_spread')}, "
                     f"max={kv.get('max_spread')}, "
                     f"duplikaate={kv.get('duplikaat_ridu')}, "
                     f"mittemonot.={kv.get('mitte_monotoonseid_jarjestikke')}, "
                     f"0/neg spread={kv.get('null_negatiivne_spread')}"
                     if n else " (tühi — nädalavahetus/pühad VÕI andmeid pole)"))

    kv_tee = os.path.join(valjundi_kaust, "validate24_summary.csv")
    if kokkuvote:
        veerud = list(kokkuvote[0].keys())
        with open(kv_tee, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=veerud, extrasaction="ignore")
            w.writeheader()
            for r in kokkuvote:
                row = {k: r.get(k, "") for k in veerud}
                w.writerow(row)
        print(f"\n  Kokkuvõte: {kv_tee}")
    return kokkuvote


def cmd_export(args):
    if not args.i_reviewed_validate24:
        print("❌ Suur eksport nõuab --i-reviewed-validate24 lippu — käivita "
              "ENNE seda --mode validate24 ja vaata tulemused üle.")
        return
    algus = datetime.strptime(args.start, "%Y-%m-%d").date()
    lopp = datetime.strptime(args.end, "%Y-%m-%d").date()
    if (lopp - algus).days > 190:
        print(f"⚠️ {args.symbol}: {(lopp-algus).days} päeva nõutud — see on "
              f"PALJU tick-andmeid (potentsiaalselt GB-suurusjärgus). "
              f"Jätkan, aga jälgi ketta ruumi.")
    paev = algus
    kokku = 0
    while paev <= lopp:
        n, esimene, viimane, kv = ekspordi_paev(args.symbol, paev, args.out)
        kokku += n
        print(f"  {paev}: {n} tick'i" + (f" ({esimene} .. {viimane})" if n else ""))
        paev += timedelta(days=1)
    print(f"\nKOKKU: {kokku} tick'i, {args.symbol}, {algus}..{lopp}")


# ═════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description=SILT)
    p.add_argument("--mode", required=True,
                   choices=["discover", "probe", "validate24", "export"])
    p.add_argument("--symbol", help="üks sümbol (probe, export)")
    p.add_argument("--symbols", default="XAUUSD,XAGUSD,WTI",
                   help="komaga eraldatud (validate24). Vaikeväärtus on "
                        "BlackBull PÄRIS kinnitatud sümbolid (discover, "
                        "21.09.2026) — nafta on 'WTI', mitte 'USOIL'.")
    p.add_argument("--start", help="YYYY-MM-DD (export)")
    p.add_argument("--end", help="YYYY-MM-DD (export)")
    p.add_argument("--out", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "mt5_ticks"))
    p.add_argument("--i-reviewed-validate24", action="store_true",
                   help="kohustuslik --mode export jaoks — kinnitab, et "
                        "validate24 tulemused on üle vaadatud")
    args = p.parse_args()

    print("=" * 78)
    print(SILT)
    print("=" * 78)

    if not yhenda():
        return 1
    try:
        os.makedirs(args.out, exist_ok=True)
        if args.mode == "discover":
            cmd_discover(args)
        elif args.mode == "probe":
            if not args.symbol:
                print("❌ --mode probe nõuab --symbol"); return 1
            cmd_probe(args)
        elif args.mode == "validate24":
            cmd_validate24(args)
        elif args.mode == "export":
            if not (args.symbol and args.start and args.end):
                print("❌ --mode export nõuab --symbol --start --end"); return 1
            cmd_export(args)
    finally:
        katkesta()
    return 0


if __name__ == "__main__":
    sys.exit(main())
