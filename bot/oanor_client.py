"""
oanor_client.py — Oanor Economic Calendar API HTTP klient BENEDICTUS
NEWS-TICK v1 jaoks.

Ainult see moodul puudutab võrku News-Tick funktsionaalsuse jaoks.
Kasutab OANOR_API_KEY keskkonnamuutujat — VÕTIT EI TOHI KUNAGI LOGIDA
ega mujale kirjutada. redact() peab käima läbi IGA teksti, mis võib
võtit sisaldada, enne logimist/salvestamist (sama muster, mis
research/oanor_latency_test.py redigeeri_saladus() — juba testitud).

Endpoint kasutaja lukustatud spetsifikatsioonist (20.09.2026):
    GET https://api.oanor.com/economiccalendar-api/v1/week
    väljad: time_gmt, country, event, actual, consensus, previous

See moodul EI OTSUSTA kaubelda — ta ainult toob ja filtreerib toorandmed.
Otsustusloogika (z-arvutus, suund, agregeerimine) on newstick_engine.py's.
"""
import os
import re

import requests

from newstick_engine import TIER1_INDICATORS

BASE_URL = "https://api.oanor.com/economiccalendar-api"
WEEK_PATH = "/v1/week"
KEY_HEADER = "x-oanor-key"

# Riik -> valuuta. Ainult meie sihtvaluutad (8 tk); kõik muu jäetakse
# vahele (unmapped -> None -> SKIP kutsuja poolt).
COUNTRY_TO_CURRENCY = {
    "United States": "USD",
    "Euro Zone":     "EUR",
    "Germany":       "EUR",
    "France":        "EUR",
    "Italy":         "EUR",
    "Spain":         "EUR",
    "Netherlands":   "EUR",
    "United Kingdom": "GBP",
    "Japan":         "JPY",
    "Canada":        "CAD",
    "Australia":     "AUD",
    "New Zealand":   "NZD",
    "Switzerland":   "CHF",
}

_TIER1_SET = frozenset(TIER1_INDICATORS)


def redact(text, secrets=None):
    """Eemalda API-võti tekstist ENNE logimist. Vt research/oanor_latency_test.py
    redigeeri_saladus() — sama muster, siia toodud ilma research/ sõltuvuseta,
    kuna production kood ei tohi research/ moodulitest importida."""
    if text is None:
        return None
    t = str(text)
    for s in (secrets or []):
        if s:
            t = t.replace(s, "***REDACTED***")
    t = re.sub(r"oanor_[A-Za-z0-9_]{6,}", "***REDACTED***", t)
    t = re.sub(r"(?i)(x-oanor-key\s*[:=]\s*)\S+", r"\1***REDACTED***", t)
    return t


def get_api_key():
    return os.environ.get("OANOR_API_KEY", "").strip()


def country_to_currency(country):
    return COUNTRY_TO_CURRENCY.get(str(country or "").strip())


def is_tier1(event_name):
    """TÄPNE (mitte hägus) vaste TIER1_INDICATORS vastu. Oanori toorandmete
    event-nimi peab olema TÄPSELT üks lukustatud 11-st, muidu ignoreeritakse.
    Kasutaja spec ei täpsustanud fuzzy matchingut — täpne string on ohutum
    valeklassifikatsiooni vastu kui research/'i regex-mustrid."""
    return event_name in _TIER1_SET if event_name else False


def fetch_week(timeout_s=10):
    """
    GET /v1/week. Tagastab dict:
      {"ok": bool, "events": list[dict], "status": int|None, "error": str|None}

    events on FILTREERIMATA toorandmed (kõik väljad, mis Oanor tagastab) —
    filtreerimine (Tier1, valuuta, puuduv consensus/actual) toimub
    filter_tier1_events()'is, et see oleks eraldi testitav ilma võrguta.

    EI TÕSTA erindit kunagi — võrguviga on kutsuja jaoks "ei saanud
    andmeid", mitte crash.
    """
    key = get_api_key()
    if not key:
        return {"ok": False, "events": [], "status": None,
                "error": "OANOR_API_KEY puudub"}
    headers = {KEY_HEADER: key, "Accept": "application/json"}
    try:
        r = requests.get(f"{BASE_URL}{WEEK_PATH}", headers=headers, timeout=timeout_s)
    except Exception as e:
        return {"ok": False, "events": [], "status": None,
                "error": redact(f"{type(e).__name__}: {e}", [key])}
    if r.status_code != 200:
        return {"ok": False, "events": [], "status": r.status_code,
                "error": redact(r.text[:300], [key])}
    try:
        payload = r.json()
    except Exception as e:
        return {"ok": False, "events": [], "status": r.status_code,
                "error": redact(f"vigane JSON: {e}", [key])}

    events = payload.get("data") if isinstance(payload, dict) else None
    if events is None and isinstance(payload, dict):
        events = payload.get("events")
    if events is None and isinstance(payload, list):
        events = payload
    if not isinstance(events, list):
        return {"ok": False, "events": [], "status": r.status_code,
                "error": "ootamatu vastuse skeem — 'data'/'events' puudub"}
    return {"ok": True, "events": events, "status": r.status_code, "error": None}


def filter_tier1_events(raw_events, date_str=None):
    """
    Filtreeri toorandmed lukustatud reeglite järgi:
      - event peab olema TÄPSELT üks 11-st Tier1 nimest
      - country peab kaarduma ühele 8 sihtvaluutast
      - consensus PEAB olema olemas (muidu SKIP)
      - actual VÕIB puududa (sündmus pole veel toimunud — kutsuja otsustab)

    Tagastab list dict'e: {date, time_gmt, country, currency, indicator,
    actual, consensus, previous, skip_reason}. skip_reason on None, kui
    sündmus on kasutatav; muidu string (logitav [NEWS-TICK SKIP] all).
    """
    out = []
    for ev in raw_events or []:
        name = ev.get("event")
        if not is_tier1(name):
            continue
        currency = country_to_currency(ev.get("country"))
        if currency is None:
            continue
        consensus = ev.get("consensus")
        actual = ev.get("actual")
        skip_reason = None
        if consensus in (None, ""):
            skip_reason = "no consensus"
        row = {
            "date": date_str or ev.get("date"),
            "time_gmt": ev.get("time_gmt"),
            "country": ev.get("country"),
            "currency": currency,
            "indicator": name,
            "actual": actual if actual not in (None, "") else None,
            "consensus": consensus if consensus not in (None, "") else None,
            "previous": ev.get("previous"),
            "skip_reason": skip_reason,
        }
        out.append(row)
    return out
