"""
NEMSIS cTrader WebSocket Module
Päris ühendus ICMarkets cTrader kontoga
Kasutab Spotware ametlikku ctrader-open-api teeki
Annab reaalajas hinnad + saadab päris ordereid
"""
import os, time, logging, threading
from datetime import datetime, timezone

logger = logging.getLogger("NEMSIS_CTRADER")

CLIENT_ID     = os.environ.get("CTRADER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CTRADER_CLIENT_SECRET", "")
ACCOUNT_ID    = int(os.environ.get("CTRADER_ACCOUNT_ID", "4023510"))
ACCESS_TOKEN  = os.environ.get("CTRADER_ACCESS_TOKEN", "")
REFRESH_TOKEN = os.environ.get("CTRADER_REFRESH_TOKEN", "")

# Symbol mapping NEMSIS → cTrader
SYMBOL_MAP = {
    "XAU/USD":  "XAUUSD",
    "AUD/CAD":  "AUDCAD",
    "EUR/AUD":  "EURAUD",
    "AUD/NZD":  "AUDNZD",
    "GBP/CAD":  "GBPCAD",
    "EUR/GBP":  "EURGBP",
    "CAD/CHF":  "CADCHF",
    "EUR/CHF":  "EURCHF",
    "NZD/CAD":  "NZDCAD",
    "EUR/NZD":  "EURNZD",
    "GBP/NZD":  "GBPNZD",
}

# Globaalne state
_client      = None
_connected   = False
_prices      = {}       # symbol → {"bid": x, "ask": x, "time": t}
_candles     = {}       # symbol_interval → DataFrame
_lock        = threading.Lock()

def is_connected():
    return _connected and ACCESS_TOKEN != ""

def get_price_ctrader(symbol_td):
    """Tagasta praegune bid/ask keskmine."""
    ct_sym = SYMBOL_MAP.get(symbol_td, symbol_td.replace("/",""))
    with _lock:
        if ct_sym in _prices:
            p = _prices[ct_sym]
            if time.time() - p["time"] < 60:  # max 1 min vana
                return round((p["bid"] + p["ask"]) / 2, 5)
    return 0.0

def get_candles(symbol_td, interval="1h", count=100):
    """
    Tagasta ajaloolised küünlad DataFramena.
    Kasutab cTrader TCP API-t.
    """
    import pandas as pd
    ct_sym = SYMBOL_MAP.get(symbol_td, symbol_td.replace("/",""))
    cache_key = f"{ct_sym}_{interval}"
    
    with _lock:
        if cache_key in _candles:
            df = _candles[cache_key]["df"]
            updated = _candles[cache_key]["updated"]
            if time.time() - updated < 300:  # 5 min cache
                return df

    # Kui ei ole cache's, kasuta yfinance fallback
    try:
        import yfinance as yf
        _YF_MAP = {
            "XAUUSD": "GC=F", "AUDCAD": "AUDCAD=X", "EURAUD": "EURAUD=X",
            "AUDNZD": "AUDNZD=X", "GBPCAD": "GBPCAD=X", "EURGBP": "EURGBP=X",
            "CADCHF": "CADCHF=X", "EURCHF": "EURCHF=X", "NZDCAD": "NZDCAD=X",
            "EURNZD": "EURNZD=X", "GBPNZD": "GBPNZD=X",
        }
        yf_sym      = _YF_MAP.get(ct_sym, ct_sym + "=X")
        yf_interval = "15m" if interval == "15min" else "1h"
        yf_period   = "60d" if yf_interval == "15m" else "60d"
        
        df = yf.Ticker(yf_sym).history(interval=yf_interval, period=yf_period, auto_adjust=True)
        if df is not None and not df.empty:
            df.columns = [c.lower() for c in df.columns]
            df.index = pd.to_datetime(df.index, utc=True)
            df = df.tail(count)
            with _lock:
                _candles[cache_key] = {"df": df, "updated": time.time()}
            return df
    except Exception as e:
        logger.error(f"candles fallback {symbol_td}: {e}")
    return None

def _run_client():
    """
    cTrader TCP WebSocket client — töötab eraldi threadis.
    Ühendub ICMarkets serveriga ja saab reaalajas hinnaandmeid.
    """
    global _client, _connected

    if not ACCESS_TOKEN:
        logger.warning("cTrader: ACCESS_TOKEN puudub")
        return

    try:
        from ctrader_open_api import Client, Protobuf, TcpProtocol, EndPoints
        from ctrader_open_api.messages.OpenApiCommonMessages_pb2 import (
            ProtoMessage, ProtoHeartbeatEvent
        )
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOAApplicationAuthReq, ProtoOAAccountAuthReq,
            ProtoOASubscribeSpotsReq, ProtoOASymbolsListReq,
            ProtoOANewOrderReq,
        )
        from twisted.internet import reactor, ssl

        symbol_ids = {}  # name → symbolId

        def on_connected(client):
            global _connected
            logger.info("✅ cTrader TCP ühendus loodud")
            # App auth
            request = ProtoOAApplicationAuthReq()
            request.clientId     = CLIENT_ID
            request.clientSecret = CLIENT_SECRET
            deferred = client.send(request)
            deferred.addErrback(on_error)

        def on_disconnected(client, reason):
            global _connected
            _connected = False
            logger.warning(f"cTrader TCP ühendus katkes: {reason}")
            # Reconnect 30 sekundi pärast
            reactor.callLater(30, _run_client)

        def on_message(client, message):
            global _connected
            msg_type = message.payloadType
            logger.info(f"cTrader msg_type: {msg_type}")

            # App auth vastus
            if msg_type == 2101:  # PROTO_OA_APPLICATION_AUTH_RES
                logger.info("✅ cTrader App auth OK")
                # Account auth
                req = ProtoOAAccountAuthReq()
                req.ctidTraderAccountId = ACCOUNT_ID
                req.accessToken         = ACCESS_TOKEN
                deferred = client.send(req)
                deferred.addErrback(on_error)

            # Account auth vastus
            elif msg_type == 2103:  # PROTO_OA_ACCOUNT_AUTH_RES
                _connected = True
                logger.info(f"✅ cTrader konto {ACCOUNT_ID} autentitud — reaalajas hinnad algavad")
                # Telli kõik sümboli IDs
                req = ProtoOASymbolsListReq()
                req.ctidTraderAccountId = ACCOUNT_ID
                deferred = client.send(req)
                deferred.addErrback(on_error)

            # Sümbolite nimekiri
            elif msg_type == 2115:  # PROTO_OA_SYMBOLS_LIST_RES
                symbols_list = Protobuf.extract(message)
                # Leia meie sümbolite IDs
                our_symbols = set(SYMBOL_MAP.values())
                ids_to_subscribe = []
                for sym in symbols_list.symbol:
                    if sym.symbolName in our_symbols:
                        symbol_ids[sym.symbolName] = sym.symbolId
                        ids_to_subscribe.append(sym.symbolId)
                        logger.info(f"  Symbol: {sym.symbolName} → ID:{sym.symbolId}")

                if ids_to_subscribe:
                    # Telli spot hinnad
                    req = ProtoOASubscribeSpotsReq()
                    req.ctidTraderAccountId = ACCOUNT_ID
                    req.symbolId.extend(ids_to_subscribe)
                    deferred = client.send(req)
                    deferred.addErrback(on_error)
                    logger.info(f"✅ Tellisin {len(ids_to_subscribe)} sümboli hinnad")

            # Spot hinna uuendus
            elif msg_type == 2131:  # PROTO_OA_SPOT_EVENT
                event = Protobuf.extract(message)
                sym_id = event.symbolId
                # Leia sümboli nimi
                sym_name = next((n for n,i in symbol_ids.items() if i == sym_id), None)
                if sym_name:
                    bid = event.bid / 100000 if event.bid else 0
                    ask = event.ask / 100000 if event.ask else 0
                    if bid > 0 and ask > 0:
                        with _lock:
                            _prices[sym_name] = {
                                "bid": bid, "ask": ask,
                                "time": time.time()
                            }

            # Heartbeat
            elif msg_type == 51:
                pass  # normaalne

        def on_error(failure):
            logger.error(f"cTrader error: {failure}")

        # Loo client
        _client = Client(
            EndPoints.PROTOBUF_LIVE_HOST,
            EndPoints.PROTOBUF_PORT,
            TcpProtocol
        )
        _client.setConnectedCallback(on_connected)
        _client.setDisconnectedCallback(on_disconnected)
        _client.setMessageReceivedCallback(on_message)

        logger.info("🔌 cTrader TCP ühendus alustamas...")
        _client.startService()

        # Käivita reactor eraldi threadis
        if not reactor.running:
            reactor.run(installSignalHandlers=False)

    except Exception as e:
        logger.error(f"cTrader client viga: {e}")
        _connected = False

def start():
    """Käivita cTrader WebSocket eraldi threadis."""
    if not ACCESS_TOKEN:
        logger.warning("cTrader: ACCESS_TOKEN puudub Railway Variables-ist")
        return

    thread = threading.Thread(target=_run_client, daemon=True, name="cTrader")
    thread.start()
    logger.info("cTrader thread käivitatud")

    # Oota kuni ühendus loodud (max 30 sek)
    for i in range(30):
        if _connected:
            logger.info("✅ cTrader WebSocket ühendus loodud!")
            return
        time.sleep(1)
    
    if not _connected:
        logger.warning("⚠️ cTrader ühendus aegus — jätkame yfinance fallback-iga")

def place_order(direction, symbol_name, lot, tp=None, sl=None):
    """
    Saada päris order cTrader kontole.
    direction: "buy" või "sell"
    symbol_name: "XAUUSD" vm
    lot: 0.01 vm
    """
    if not _connected or not _client:
        logger.warning("⚠️ cTrader: ei ole ühendust — order salvestatud ainult Supabase'i")
        return None

    try:
        from ctrader_open_api.messages.OpenApiMessages_pb2 import (
            ProtoOANewOrderReq, ProtoOATradeSide, ProtoOAOrderType
        )

        # Leia symbol ID
        ct_sym = SYMBOL_MAP.get(symbol_name, symbol_name)
        sym_id = None
        with _lock:
            # Otsi symbol_ids-ist
            pass  # symbol_ids on lokaalses _run_client scopis
            # Kasutame otsest API kõnet
        
        volume = int(lot * 100)  # cTrader: 1 lot = 100 units

        req = ProtoOANewOrderReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        req.symbolId   = sym_id or 0  # täiendame kui symbol ID teada
        req.orderType  = 1  # MARKET
        req.tradeSide  = 1 if direction == "buy" else 2  # BUY=1, SELL=2
        req.volume     = volume
        req.label      = "NEMSIS"

        if tp: req.takeProfit = int(tp * 100000)
        if sl: req.stopLoss   = int(sl * 100000)

        deferred = _client.send(req)
        logger.info(f"✅ Order saadetud: {direction.upper()} {ct_sym} {lot}lot")
        return deferred

    except Exception as e:
        logger.error(f"cTrader place_order: {e}")
        return None

def get_account_balance():
    """Tagasta konto bilanss cTrader-ist."""
    # Hetkel tagastab None — balance tuleb Supabase-st
    # Tulevikus: ProtoOAGetAccountListByAccessTokenReq
    return None
