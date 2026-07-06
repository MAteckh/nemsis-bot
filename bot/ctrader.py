"""
NEMSIS cTrader WebSocket Module
Päris ühendus ICMarkets cTrader kontoga
Kasutab Spotware ametlikku ctrader-open-api teeki
Annab reaalajas hinnad + saadab päris ordereid
"""
import os, time, logging, threading, requests
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
_client          = None
_connected       = False
_prices          = {}       # symbol → {"bid": x, "ask": x, "time": t}
_candles         = {}       # symbol_interval → DataFrame
_symbol_ids      = {}       # symbolName → symbolId
_symbol_lot_sizes = {}      # symbolName → lotSize
_lock            = threading.Lock()
_disconnect_times = []      # ühenduskatkestuste ajatemplid (viimase 60s throttling jaoks)

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

        symbol_ids = _symbol_ids  # viide globaalsele

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
            # Reconnect-backoff: kui katkestusi tuleb liiga tihti (klaster),
            # oota enne järgmist katset, et vältida serveri ülekoormamist
            now_t = time.time()
            _disconnect_times.append(now_t)
            while _disconnect_times and now_t - _disconnect_times[0] > 60:
                _disconnect_times.pop(0)
            if len(_disconnect_times) >= 4:
                wait_s = min(30, 3 * len(_disconnect_times))
                logger.warning(f"⏳ {len(_disconnect_times)} katkestust 60s jooksul — ootan {wait_s}s enne jätkamist")
                time.sleep(wait_s)

        def on_message(client, message):
            global _connected
            msg_type = message.payloadType

            # Error vastus
            if msg_type == 2142:
                try:
                    error = Protobuf.extract(message)
                    logger.error(f"cTrader ERROR: {error.errorCode} — {error.description}")
                except Exception as e:
                    logger.error(f"cTrader ERROR (raw): {message}")

            # App auth vastus — küsi konto nimekiri
            elif msg_type == 2101:
                logger.info("✅ cTrader App auth OK")
                # Hangi kõik kontod et leida õige ctidTraderAccountId
                from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOAGetAccountListByAccessTokenReq
                req = ProtoOAGetAccountListByAccessTokenReq()
                req.accessToken = ACCESS_TOKEN
                deferred = client.send(req)
                deferred.addErrback(on_error)

            # Kontode nimekiri — leia õige ID
            elif msg_type == 2150:
                accounts = Protobuf.extract(message)
                logger.info(f"cTrader kontod:")
                target_id = None
                for acc in accounts.ctidTraderAccount:
                    # Logi kõik saadaval väljad
                    acc_dict = {}
                    for field in acc.DESCRIPTOR.fields:
                        try:
                            acc_dict[field.name] = getattr(acc, field.name)
                        except:
                            pass
                    logger.info(f"  konto: {acc_dict}")
                    if acc.isLive:
                        target_id = acc.ctidTraderAccountId

                if target_id:
                    logger.info(f"✅ Kasutan ctidTraderAccountId={target_id}")
                    global ACCOUNT_ID
                    ACCOUNT_ID = target_id
                    req = ProtoOAAccountAuthReq()
                    req.ctidTraderAccountId = target_id
                    req.accessToken = ACCESS_TOKEN
                    deferred = client.send(req)
                    deferred.addErrback(on_error)
                else:
                    logger.error("cTrader: live kontot ei leitud!")

            # Account auth vastus
            elif msg_type == 2103:  # PROTO_OA_ACCOUNT_AUTH_RES
                _connected = True
                logger.info(f"✅ cTrader konto {ACCOUNT_ID} autentitud — reaalajas hinnad algavad")
                # Telli kõik sümboli IDs
                req = ProtoOASymbolsListReq()
                req.ctidTraderAccountId = ACCOUNT_ID
                deferred = client.send(req)
                deferred.addErrback(on_error)

            # Order täitmise vastus — logi KÕIK
            elif msg_type == 2126:
                try:
                    event = Protobuf.extract(message)
                    logger.info(f"🔔 EXECUTION EVENT: type={event.executionType} errorCode={event.errorCode if event.errorCode else 'none'}")
                    if event.order:
                        logger.info(f"  Order: id={event.order.orderId} status={event.order.orderStatus} vol={event.order.tradeData.volume}")
                    if event.position:
                        logger.info(f"  Position: id={event.position.positionId} price={event.position.price}")
                except Exception as e:
                    logger.error(f"Execution event parse: {e}")

            # Sümbolite nimekiri
            elif msg_type == 2115:  # PROTO_OA_SYMBOLS_LIST_RES
                symbols_list = Protobuf.extract(message)
                # Leia meie sümbolite IDs
                our_symbols = set(SYMBOL_MAP.values())
                ids_to_subscribe = []
                for sym in symbols_list.symbol:
                    if sym.symbolName in our_symbols:
                        symbol_ids[sym.symbolName] = sym.symbolId
                        # ICMarkets: kõik instrumendid lotSize=100000 (0.01 lot = 1000 units)
                        lot_size = 100000
                        _symbol_lot_sizes[sym.symbolName] = lot_size
                        ids_to_subscribe.append(sym.symbolId)
                        logger.info(f"  Symbol: {sym.symbolName} → ID:{sym.symbolId} lotSize:{lot_size}")

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

            # Order error event
            elif msg_type == 2132:  # PROTO_OA_ORDER_ERROR_EVENT
                try:
                    event = Protobuf.extract(message)
                    logger.error(f"❌ ORDER ERROR: {event.errorCode} — {event.description}")
                except Exception as e:
                    logger.error(f"Order error event: {e}")

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

def refresh_access_token():
    """
    Uuenda access token refresh tokeni abil.
    Käivitatakse automaatselt iga 25 päeva tagant.
    """
    global ACCESS_TOKEN, REFRESH_TOKEN
    if not REFRESH_TOKEN or not CLIENT_ID or not CLIENT_SECRET:
        logger.warning("Token refresh: puuduvad credentials")
        return False
    try:
        r = requests.get(
            "https://openapi.ctrader.com/apps/token",
            params={
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
            timeout=15
        )
        data = r.json()
        if data.get("accessToken"):
            ACCESS_TOKEN = data["accessToken"]
            REFRESH_TOKEN = data.get("refreshToken", REFRESH_TOKEN)
            logger.info("✅ cTrader token uuendatud edukalt")
            return True
        else:
            logger.error(f"Token refresh ebaõnnestus: {data}")
            return False
    except Exception as e:
        logger.error(f"Token refresh viga: {e}")
        return False

def _token_refresh_loop():
    """Uuenda token iga 25 päeva tagant (token kehtib 30 päeva)."""
    while True:
        time.sleep(25 * 24 * 60 * 60)  # 25 päeva
        logger.info("🔄 Token refresh alustab...")
        refresh_access_token()

def start():
    """Käivita cTrader WebSocket eraldi threadis."""
    if not ACCESS_TOKEN:
        logger.warning("cTrader: ACCESS_TOKEN puudub Railway Variables-ist")
        return

    # Käivita token refresh thread
    refresh_thread = threading.Thread(target=_token_refresh_loop, daemon=True, name="TokenRefresh")
    refresh_thread.start()

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
    Tagastab True kui broker kinnitas tehingu, False kui broker lükkas tagasi
    (nt TRADING_NOT_ALLOWED), None kui pole ühendust või kinnitust ei tulnud.
    """
    if not _connected or not _client:
        logger.warning(f"⚠️ cTrader place_order: ei ole ühendust ({symbol_name})")
        return None

    ct_sym   = SYMBOL_MAP.get(symbol_name, symbol_name)
    sym_id   = _symbol_ids.get(ct_sym)
    lot_size = _symbol_lot_sizes.get(ct_sym, 100000)

    if not sym_id:
        logger.error(f"cTrader place_order: symbol ID puudub {ct_sym}")
        return None

    try:
        from ctrader_open_api.messages.OpenApiMessages_pb2 import ProtoOANewOrderReq

        volume = int(lot * lot_size)
        logger.info(f"cTrader order: {direction.upper()} {ct_sym} lot={lot} volume={volume} lotSize={lot_size}")

        req = ProtoOANewOrderReq()
        req.ctidTraderAccountId = ACCOUNT_ID
        req.symbolId   = sym_id
        req.orderType  = 1   # MARKET
        req.tradeSide  = 1 if direction == "buy" else 2
        req.volume     = volume
        req.label      = "NEMSIS"
        req.comment    = f"NEMSIS {direction.upper()} {ct_sym}"

        if tp:
            req.takeProfit = int(round(tp * 100000))
        if sl:
            req.stopLoss = int(round(sl * 100000))

        # Order-kinnituse ootamine: blokeerib kuni cTrader vastab (max 8 sek),
        # et signaal salvestataks Supabase'i alles PÄRAST kinnitust
        confirm_event = threading.Event()
        result_holder = {"success": None}

        def on_order_response(result):
            try:
                # payloadType 2132 = ORDER_ERROR_EVENT (nt TRADING_NOT_ALLOWED)
                if getattr(result, "payloadType", None) == 2132:
                    result_holder["success"] = False
                else:
                    result_holder["success"] = True
            except Exception:
                result_holder["success"] = False
            confirm_event.set()
            return result

        def on_order_error(failure):
            logger.error(f"cTrader order failed: {failure}")
            result_holder["success"] = False
            confirm_event.set()
            return failure

        deferred = _client.send(req)
        deferred.addCallback(on_order_response)
        deferred.addErrback(on_order_error)

        confirmed = confirm_event.wait(timeout=8)
        if not confirmed:
            logger.warning(f"⚠️ cTrader order timeout — kinnitust ei tulnud 8s jooksul ({ct_sym})")
            return None

        if result_holder["success"]:
            logger.info(f"✅ cTrader ORDER kinnitatud: {direction.upper()} {ct_sym} {lot}lot | TP:{tp} SL:{sl}")
            return True
        else:
            logger.warning(f"❌ cTrader ORDER tagasi lükatud: {direction.upper()} {ct_sym} {lot}lot")
            return False

    except Exception as e:
        logger.error(f"cTrader place_order {symbol_name}: {e}")
        return None

def get_account_balance():
    """Tagasta konto bilanss cTrader-ist."""
    # Hetkel tagastab None — balance tuleb Supabase-st
    # Tulevikus: ProtoOAGetAccountListByAccessTokenReq
    return None
