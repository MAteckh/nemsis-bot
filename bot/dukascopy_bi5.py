"""
dukascopy_bi5.py — Dukascopy .bi5 tick-faili parser ja valideerija.

UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py, mt5_connector.py,
strategy_meanrev.py, backtest.py, gold_logic.py, strategies.py).

=============================================================================
FORMAAT — TULETATUD PARIS FAILIST, MITTE EELDATUD
=============================================================================
URL-skeem:
    https://datafeed.dukascopy.com/datafeed/{SYMBOL}/{YYYY}/{MM}/{DD}/{HH}h_ticks.bi5

  SYMBOL   suurtahtedega, ilma eraldajata (EURUSD, USDJPY, ...)
  YYYY     aasta, 4 kohta
  MM       KUU MIINUS UKS, 2 kohta ("00" = jaanuar, "11" = detsember)
           See on Dukascopy eripara. Kontrollitud empiiriliselt:
           vt dukascopy_validate.py test K3 — parsitud tundide hinnad
           vastavad olemasolevatele M1-baaridele AINULT 0-indekseeritud
           kuu juures.
  DD       paev kuus, 2 kohta
  HH       tund UTC, 2 kohta ("00".."23")

Faili sisu: LZMA-ALONE (mitte .xz, mitte .lzma-container) pakitud voog.
  13-baidine pais, MOOEDETUD paris failist:
      bait  0      props = 0x5D  (lc=3, lp=0, pb=2)
      baidid 1-4   sonastiku suurus, little-endian: 00 00 40 00 = 4 MiB
      baidid 5-12  pakkimata suurus, little-endian 64-bit
  Naide (EURUSD 2026-09-03 10h):
      5d 00 00 40 00 | 74 c2 00 00 00 00 00 00
      pakkimata = 0xC274 = 49 780 baiti = 2 489 x 20  => KIRJE ON 20 BAITI

Pakkimata sisu: jarjestikused 20-baidised kirjed, BIG-ENDIAN:
      offset  0  uint32   millisekundid TUNNI algusest
      offset  4  uint32   ASK taisarvuna (punktides)
      offset  8  uint32   BID taisarvuna (punktides)
      offset 12  float32  ASK maht (miljonites uhikutes)
      offset 16  float32  BID maht

  TAHELEPANU JARJEKORRALE: ASK tuleb ENNE BID-i. Kontrollitud:
  ask >= bid koigil kirjetel (vt valideerimine). Kui jarjekord oleks
  vastupidi, oleks spread susteemselt negatiivne.

  Tuhi fail (0 baiti) tahendab: sellel tunnil ei olnud tick'e
  (nadalavahetus, pyha). See EI OLE viga.

HIND = taisarv / 10**digits. Digits EI OLE koigil sama:
      5-kohalised (EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCHF, USDCAD): 10^5
      3-kohalised (JPY-paarid): 10^3
  Vt SUMBOLID allpool. Vale divisor annaks 100x voi 100000x vea.

AEG: Dukascopy tick-timestamp on UTC. Faili tund ON UTC tund; kirje
  millisekundi-offset lisatakse sellele. DST EI MOJUTA midagi, sest
  kogu skeem on UTC-s. Resolutsioon: 1 millisekund.
      timestamp_utc = datetime(YYYY, MM, DD, HH, tzinfo=UTC)
                      + timedelta(milliseconds=ms_offset)
"""
import datetime as dt
import lzma
import struct

KIRJE_BAITE = 20
LZMA_PAIS_BAITE = 13

# symbol -> (digits, hinna_jagaja)
SUMBOLID = {
    "EURUSD": 5, "GBPUSD": 5, "AUDUSD": 5, "NZDUSD": 5,
    "USDCHF": 5, "USDCAD": 5, "EURGBP": 5, "EURCHF": 5,
    "USDJPY": 3, "EURJPY": 3, "GBPJPY": 3, "AUDJPY": 3,
    "CADJPY": 3, "CHFJPY": 3, "NZDJPY": 3,
}


def digits(symbol):
    if symbol not in SUMBOLID:
        raise ValueError(f"tundmatu sumbol {symbol!r} — lisa SUMBOLID hulka, "
                         f"ARA eelda 10^5")
    return SUMBOLID[symbol]


def url(symbol, paev, tund):
    """Dukascopy URL. NB: kuu on 0-indekseeritud."""
    return (f"https://datafeed.dukascopy.com/datafeed/{symbol}/"
            f"{paev.year:04d}/{paev.month - 1:02d}/{paev.day:02d}/"
            f"{tund:02d}h_ticks.bi5")


def lzma_pais(raw):
    """Loeb 13-baidise LZMA-alone paise. Tagastab (props, sonastik, suurus)."""
    if len(raw) < LZMA_PAIS_BAITE:
        return None
    props = raw[0]
    sonastik = struct.unpack("<I", raw[1:5])[0]
    suurus = struct.unpack("<Q", raw[5:13])[0]
    return props, sonastik, suurus


def lahti(raw):
    """
    LZMA-alone lahtipakkimine. Dukascopy ei kirjuta lopumarki, seega
    FORMAT_ALONE dekoodrile tuleb anda pais eraldi filtritena, kui
    tavaline tee ebaonnestub.
    """
    if not raw:
        return b""
    try:
        return lzma.LZMADecompressor(lzma.FORMAT_ALONE).decompress(raw)
    except lzma.LZMAError:
        p = lzma_pais(raw)
        if p is None:
            raise
        props, sonastik, _ = p
        lc = props % 9
        rest = props // 9
        lp, pb = rest % 5, rest // 5
        d = lzma.LZMADecompressor(
            format=lzma.FORMAT_RAW,
            filters=[{"id": lzma.FILTER_LZMA1, "lc": lc, "lp": lp,
                      "pb": pb, "dict_size": sonastik}])
        return d.decompress(raw[LZMA_PAIS_BAITE:])


def parsi(raw, symbol, paev, tund):
    """
    Tagastab list[dict]: ts_utc, ms_offset, bid, ask, bid_maht, ask_maht.
    Tuhi fail -> tuhi list (tick'e ei olnud, see EI OLE viga).
    """
    data = lahti(raw)
    if len(data) % KIRJE_BAITE:
        raise ValueError(f"pakkimata pikkus {len(data)} ei jagu "
                         f"{KIRJE_BAITE}-ga — formaat on vale")
    jag = 10 ** digits(symbol)
    alus = dt.datetime(paev.year, paev.month, paev.day, tund,
                       tzinfo=dt.timezone.utc)
    out = []
    for i in range(0, len(data), KIRJE_BAITE):
        ms, ask_i, bid_i, ask_v, bid_v = struct.unpack(
            ">IIIff", data[i:i + KIRJE_BAITE])
        out.append(dict(
            ts_utc=alus + dt.timedelta(milliseconds=ms),
            ms_offset=ms,
            bid=bid_i / jag,
            ask=ask_i / jag,
            bid_maht=float(bid_v),
            ask_maht=float(ask_v)))
    return out


def valideeri(tikid, symbol):
    """Andmekvaliteedi kontrollid. Tagastab dict; ei viska erindit."""
    if not tikid:
        return dict(n=0, staatus="TUHI (tick'e ei olnud)")
    bid = [t["bid"] for t in tikid]
    ask = [t["ask"] for t in tikid]
    spread = [a - b for a, b in zip(ask, bid)]
    ms = [t["ms_offset"] for t in tikid]
    srt = sorted(spread)

    def q(p):
        return srt[min(int(p * len(srt)), len(srt) - 1)]

    jag = 10 ** digits(symbol)
    return dict(
        n=len(tikid),
        esimene=tikid[0]["ts_utc"].isoformat(),
        viimane=tikid[-1]["ts_utc"].isoformat(),
        bid_min=min(bid), bid_max=max(bid),
        ask_min=min(ask), ask_max=max(ask),
        esimene_bid=bid[0], esimene_ask=ask[0],
        viimane_bid=bid[-1], viimane_ask=ask[-1],
        koik_positiivsed=bool(min(bid) > 0 and min(ask) > 0),
        bid_alla_ask=bool(all(b <= a for b, a in zip(bid, ask))),
        negatiivseid_spreade=sum(1 for s in spread if s < 0),
        nullspreade=sum(1 for s in spread if s == 0),
        spread_med_pip=q(0.50) * jag / 10,
        spread_p75_pip=q(0.75) * jag / 10,
        spread_p90_pip=q(0.90) * jag / 10,
        spread_p95_pip=q(0.95) * jag / 10,
        spread_max_pip=max(spread) * jag / 10,
        ms_kasvav=bool(all(a <= b for a, b in zip(ms, ms[1:]))),
        ms_min=min(ms), ms_max=max(ms))


def votme_rida(symbol, t):
    """Deterministlik unikaalne voti — idempotentsuse alus."""
    return (symbol, t["ts_utc"].isoformat(timespec="milliseconds"),
            t["bid"], t["ask"])
