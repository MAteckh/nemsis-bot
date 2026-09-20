"""
newstick_engine.py — BENEDICTUS NEWS-TICK v1 PUHTAD FUNKTSIOONID.

Nagu gold_logic.py: puhtad funktsioonid, ei tee I/O-d ega loe globaalset
olekut, importitav Linuxil ilma MT5/Supabase'ita. Kõik siin olev on
otse offline-testitav (vt research/newstick_test.py stiili, mis kordab
research/oanor_latency_test.py juba testitud mustreid).

LUKUSTATUD SPETSIFIKATSIOON (kasutaja 20.09.2026 sõnumitest):
  * z = (actual - forecast) / SD(eelmised avaldamisvead), SD viimase 20
    avaldamisvea pealt, shift(1) (ei kasuta kunagi enda värsket viga),
    minimaalselt 10 vaatlust enne kui z üldse arvutatakse.
  * Kaubelda ainult kui |z| >= 1.0.
  * Sama valuuta + sama minut -> summeeri MÄRGI-KOHANDATUD z (z_i * mark_i)
    enne suunaotsust, seejärel üks tehing. See on TÕLGENDUSVALIK (spec oli
    napisõnaline "sum(z) enne suunaotsust") — vt NEWSTICK_AGGREGATION_NOTE.
  * Suund: sign(summa) * mark, inverteeritud QUOTE-valuuta sündmuste jaoks.
  * XAUUSD on News-Tick'ist TÄIELIKULT väljas.
"""
import re
import statistics
from datetime import datetime, timezone

NEWSTICK_AGGREGATION_NOTE = (
    "Spets ütles 'summeeri z enne suunaotsust', aga ei täpsustanud, kas "
    "indikaatori märk (mark, nt Unemployment Rate = -1) rakendub enne või "
    "pärast summeerimist mitme samaaegse sündmuse korral. Ainus majanduslikult "
    "sidus tõlgendus: summeeri MÄRGI-KOHANDATUD z (z_i * mark_i) ja võta "
    "summa märk suunaks, |summa| >= 1.0 lävi. Rakendatud nii, dokumenteeritud "
    "siin ja lõpuraportis."
)

# Tier1 indikaatorid — TÄPSED nimed, mitte hägus vaste (vt oanor_client.py
# sobib_tier1(), mis kasutab neid täpseid stringe võtmena).
TIER1_INDICATORS = (
    "Inflation Rate",
    "Core Inflation Rate",
    "Inflation Rate MoM",
    "Unemployment Rate",
    "GDP Growth Rate",
    "GDP Annual Growth Rate",
    "Retail Sales MoM",
    "Retail Sales YoY",
    "Interest Rate",
    "Employment Change",
    "Non Farm Payrolls",
)

# Indikaatori "mark" — kas kõrgem actual (vs forecast) on valuutale
# tugevdav (+1) või nõrgendav (-1) signaal. Unemployment Rate on ainus
# indikaator, kus kõrgem number on halb (nõrgendav).
INDICATOR_MARK = {
    "Inflation Rate":        1,
    "Core Inflation Rate":   1,
    "Inflation Rate MoM":    1,
    "Unemployment Rate":    -1,
    "GDP Growth Rate":       1,
    "GDP Annual Growth Rate": 1,
    "Retail Sales MoM":      1,
    "Retail Sales YoY":      1,
    "Interest Rate":         1,
    "Employment Change":     1,
    "Non Farm Payrolls":     1,
}

# valuuta -> (instrument, quote) — quote=True tähendab, et see valuuta on
# instrumendi QUOTE-pool (nt USD on EURUSD quote), seega suund tuleb
# inverteerida. XAUUSD ei ole siin kunagi.
CURRENCY_MAP = {
    "EUR": ("EURUSD", False),
    "USD": ("EURUSD", True),
    "GBP": ("GBPUSD", False),
    "JPY": ("USDJPY", True),
    "CHF": ("USDCHF", True),
    "AUD": ("AUDUSD", False),
    "CAD": ("USDCAD", True),
    "NZD": ("NZDUSD", False),
}

# Pip-suurus hinnaühikutes (24-pip SL kaugusesse teisendamiseks).
PIP_SIZE = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "AUDUSD": 0.0001,
    "NZDUSD": 0.0001,
    "USDCHF": 0.0001,
    "USDCAD": 0.0001,
    "USDJPY": 0.01,
}

Z_THRESHOLD = 1.0
HOLD_SECONDS = 30
SL_PIPS = 24
RISK_PCT = 0.01
MIN_ERROR_HISTORY = 10
ERROR_HISTORY_MAX = 20


def compute_z(actual, forecast, error_history):
    """
    z = (actual - forecast) / SD(error_history), min 10 vaatlust.

    error_history peab olema juba kutsuja poolt shift(1)'itud, st SEDA
    sündmust ENNE toimunud avaldamisvead — see funktsioon ise EI TEA
    ega EI TOHI teada praegust actual/forecast paari, kui ta history
    listi ehitab (vt update_error_history()).

    Tagastab None, kui vaatlusi on vähem kui MIN_ERROR_HISTORY (ei
    kaubelda, kuni piisavalt ajalugu on kogutud) või SD on null.
    """
    if actual is None or forecast is None:
        return None
    hist = [h for h in error_history if h is not None][-ERROR_HISTORY_MAX:]
    if len(hist) < MIN_ERROR_HISTORY:
        return None
    try:
        sd = statistics.stdev(hist)
    except statistics.StatisticsError:
        return None
    if sd == 0:
        return None
    return (float(actual) - float(forecast)) / sd


def update_error_history(error_history, actual, forecast, max_len=ERROR_HISTORY_MAX):
    """Lisa UUS avaldamisviga ajaloo lõppu (järgmiste sündmuste jaoks —
    shift(1) semantika: SEE sündmus ei näe kunagi iseenda viga)."""
    if actual is None or forecast is None:
        return list(error_history)
    err = float(actual) - float(forecast)
    updated = list(error_history) + [err]
    return updated[-max_len:]


def aggregate_zscores(events):
    """
    events: list of {"indicator": str, "z": float|None}, kõik SAMA
    valuuta + SAMA minut kohta.

    Tagastab (agg: float, n_used: int) — agg on summa z_i * mark_i üle
    kõigi kasutatavate (teadaoleva indikaatori, mitte-None z) sündmuste.
    """
    agg = 0.0
    n = 0
    for ev in events:
        mark = INDICATOR_MARK.get(ev.get("indicator"))
        z = ev.get("z")
        if mark is None or z is None:
            continue
        agg += z * mark
        n += 1
    return agg, n


def decide_direction(agg_z, quote_currency):
    """
    agg_z: aggregate_zscores() väljund (mark-kohandatud summa).
    quote_currency: True, kui vallandanud valuuta on paari QUOTE-pool.

    Tagastab "buy" / "sell" / None (allapoole läve, ei kaubelda).
    """
    if agg_z is None or abs(agg_z) < Z_THRESHOLD:
        return None
    base_dir = 1 if agg_z > 0 else -1
    if quote_currency:
        base_dir = -base_dir
    return "buy" if base_dir > 0 else "sell"


def instrument_for_currency(currency):
    """Tagastab (instrument, quote_flag) või (None, None) tundmatu valuuta jaoks."""
    return CURRENCY_MAP.get(currency, (None, None))


def sl_distance_price(instrument):
    """24-pip katastroofi-stopi kaugus HINNAÜHIKUTES antud instrumendi jaoks."""
    pip = PIP_SIZE.get(instrument)
    if pip is None:
        return None
    return round(SL_PIPS * pip, 6)


def pip_value_usd(instrument, mid_price):
    """
    $ väärtus 1.0 hinnaühiku liikumise kohta 1.0 loti peale (standard lot
    = 100 000 baasvaluutat).

    EURUSD/GBPUSD/AUDUSD/NZDUSD: quote = USD, kasum on juba $-des, ei vaja
    teisendust -> 100000.0.

    USDJPY/USDCHF/USDCAD: quote EI OLE USD (JPY/CHF/CAD), kasum tekib
    quote-valuutas ja tuleb $ teisendada. KASUTAB PÄRIS ELUSAT hinda
    (mid_price antud kutsuja poolt, samast tick'ist mis order'i jaoks
    juba niikuinii küsitakse) — mitte staatilist ligikaudset kurssi.
    See väldib staatilise JPY/CHF/CAD kursi ligikaudistuse, mida
    algselt kaaluti.
    """
    if instrument in ("USDJPY", "USDCHF", "USDCAD"):
        if not mid_price or mid_price <= 0:
            return None
        return 100000.0 / float(mid_price)
    return 100000.0


def risk_based_lot(balance, sl_distance, pip_value, risk_pct=RISK_PCT,
                    min_lot=0.01, max_lot=0.5):
    """Sama valem, mis gold_logic.get_risk_based_lot() — siia toodud
    eraldi, et News-Tick moodul ei sõltuks kulla moodulist ega vastupidi."""
    if sl_distance is None or sl_distance <= 0 or pip_value is None or pip_value <= 0:
        return min_lot
    risk_amount = balance * risk_pct
    lot = risk_amount / (sl_distance * pip_value)
    return max(min_lot, min(round(lot, 3), max_lot))


def event_dedup_key(date_str, time_gmt, country, event_name):
    """Stabiilne identifikaator ühe Oanor sündmuse jaoks. Oanor ei anna
    event_id-d — kombineeritud võti nagu research/oanor_latency_test.py
    sundmuse_voti() eeskujul, aga ilma järjekorranumbrita, sest News-Tick
    dedup ei loe kogu päeva korraga, vaid sündmust ükshaaval."""
    return "|".join([
        str(date_str or "?"),
        str(time_gmt or "??:??"),
        str(country or "?"),
        str(event_name or "?"),
    ])


def minute_key(date_str, time_gmt):
    """Sama-minuti agregeerimise võti (valuuta lisatakse kutsuja poolt)."""
    return f"{date_str or '?'}T{time_gmt or '??:??'}"


def group_by_currency_minute(rows):
    """
    Grupeeri Oanor Tier1 read (oanor_client.filter_tier1_events() väljund)
    SAMA valuuta + SAMA avaldamisminuti järgi — see on ühik, mille peale
    z-skoorid summeeritakse (spec: "sama valuuta + sama minut -> summeeri
    enne suunaotsust").

    rows: list of dict, igaüks vähemalt {"currency","date","time_gmt"}.
    Tagastab dict {(currency, date, time_gmt): [rows]}, sisemine
    järjekord säilitatud.
    """
    groups = {}
    for r in rows:
        key = (r.get("currency"), r.get("date"), r.get("time_gmt"))
        groups.setdefault(key, []).append(r)
    return groups


def scheduled_utc(date_str, time_gmt):
    """
    Teisenda Oanor "date" (YYYY-MM-DD) + "time_gmt" (HH:MM) UTC
    ajatempliks. Tagastab None, kui kumbki väli puudub või on parsimatu
    (nt "All Day", "Tentative") — kutsuja peab None korral käituma nagu
    "aeg teadmata", mitte oletama.
    """
    if not date_str or not time_gmt:
        return None
    if not re.match(r"^\d{1,2}:\d{2}$", str(time_gmt).strip()):
        return None
    try:
        h, m = [int(x) for x in str(time_gmt).strip().split(":")]
        y, mo, d = [int(x) for x in str(date_str).split("-")]
        if h > 23 or m > 59:
            return None
        return datetime(y, mo, d, h, m, tzinfo=timezone.utc)
    except Exception:
        return None
