"""
NEMSIS cTrader Module
Päris ühendus ICMarkets cTrader kontoga
Asendab TwelveData andmete jaoks
Saadab päris ordereid kontole 4023510
"""
import os, time, logging, requests
from datetime import datetime, timezone

logger = logging.getLogger("NEMSIS_CTRADER")

# cTrader API endpoints
AUTH_URL    = "https://openapi.ctrader.com/apps/token"
API_HOST    = "live.ctraderapi.com"
API_PORT    = 5035

CLIENT_ID     = os.environ.get("CTRADER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("CTRADER_CLIENT_SECRET", "")
ACCOUNT_ID    = int(os.environ.get("CTRADER_ACCOUNT_ID", "4023510"))
REDIRECT_URI  = "https://nemsis-bot.vercel.app"

# Token cache — laeb Railway Variables-ist automaatselt
_token_cache = {
    "access_token":  os.environ.get("CTRADER_ACCESS_TOKEN", None),
    "refresh_token": os.environ.get("CTRADER_REFRESH_TOKEN", None),
    "expires_at":    time.time() + 2628000 if os.environ.get("CTRADER_ACCESS_TOKEN") else 0,
}

# Price cache
_price_cache = {}

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

def get_access_token():
    """Hangi access token cTrader API-lt."""
    global _token_cache
    now = time.time()

    # Kasuta cache'd tokenit kui veel kehtib
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    # Refresh token kui olemas
    if _token_cache["refresh_token"]:
        try:
            r = requests.post(AUTH_URL, params={
                "grant_type":    "refresh_token",
                "refresh_token": _token_cache["refresh_token"],
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            }, timeout=15)
            if r.status_code == 200:
                data = r.json()
                _token_cache["access_token"]  = data["accessToken"]
                _token_cache["refresh_token"] = data["refreshToken"]
                _token_cache["expires_at"]    = now + data.get("expiresIn", 2628000)
                logger.info("✅ cTrader token refreshed")
                return _token_cache["access_token"]
        except Exception as e:
            logger.error(f"Token refresh: {e}")

    logger.warning("⚠️ cTrader: access token puudub — vaja OAuth autentimist")
    return None

def get_auth_url():
    """Genereeri OAuth autentimise URL."""
    return (
        f"https://connect.spotware.com/apps/auth"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=trading"
    )

def exchange_code_for_token(auth_code):
    """Vaheta authorization code access token vastu."""
    try:
        r = requests.get(f"{AUTH_URL}", params={
            "grant_type":   "authorization_code",
            "code":         auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id":    CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }, timeout=15)
        if r.status_code == 200:
            data = r.json()
            _token_cache["access_token"]  = data["accessToken"]
            _token_cache["refresh_token"] = data["refreshToken"]
            _token_cache["expires_at"]    = time.time() + data.get("expiresIn", 2628000)
            logger.info("✅ cTrader autentimine õnnestus!")
            return True
        else:
            logger.error(f"Token exchange failed: {r.status_code} {r.text}")
            return False
    except Exception as e:
        logger.error(f"Token exchange: {e}")
        return False

def save_tokens(access_token, refresh_token, expires_in=2628000):
    """Salvesta tokenid Railway Variables kaudu (manuaalne)."""
    _token_cache["access_token"]  = access_token
    _token_cache["refresh_token"] = refresh_token
    _token_cache["expires_at"]    = time.time() + expires_in
    logger.info("✅ cTrader tokenid salvestatud")

def get_account_info():
    """Hangi konto informatsioon."""
    token = get_access_token()
    if not token:
        return None
    try:
        # cTrader Open API kasutab protobuf TCP ühendust
        # Lihtsustatud HTTP REST versioon
        r = requests.get(
            f"https://openapi.ctrader.com/apps/{CLIENT_ID}/accounts",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.status_code == 200:
            return r.json()
        logger.error(f"Account info: {r.status_code}")
        return None
    except Exception as e:
        logger.error(f"Account info: {e}")
        return None

def get_price_ctrader(symbol_td):
    """
    Hangi praegune hind cTrader-ist.
    Fallback TwelveData peale kui cTrader ei tööta.
    """
    global _price_cache
    now = time.time()
    cache_key = symbol_td

    # Cache 30 sekundit
    if cache_key in _price_cache and now - _price_cache[cache_key]["t"] < 30:
        return _price_cache[cache_key]["price"]

    token = get_access_token()
    if token:
        try:
            ct_symbol = SYMBOL_MAP.get(symbol_td, symbol_td.replace("/",""))
            # cTrader tick data endpoint
            r = requests.get(
                f"https://openapi.ctrader.com/apps/{CLIENT_ID}/quotes/{ct_symbol}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                bid = float(data.get("bid", 0))
                ask = float(data.get("ask", 0))
                mid = round((bid + ask) / 2, 5)
                if mid > 0:
                    _price_cache[cache_key] = {"price": mid, "t": now}
                    return mid
        except Exception as e:
            logger.debug(f"cTrader price {symbol_td}: {e}")

    # Fallback: TwelveData
    try:
        td_key = os.environ.get("TWELVEDATA_KEY", "")
        if td_key:
            r = requests.get("https://api.twelvedata.com/price",
                params={"symbol": symbol_td, "apikey": td_key}, timeout=10)
            price = float(r.json().get("price", 0))
            if price > 0:
                _price_cache[cache_key] = {"price": price, "t": now}
                return price
    except:
        pass

    # Kasuta viimast teadaolevat hinda
    if cache_key in _price_cache:
        return _price_cache[cache_key]["price"]
    return 0.0

def place_order(direction, symbol, lot, tp, sl, label="NEMSIS"):
    """
    Saada päris order cTrader kontole.
    direction: "buy" või "sell"
    symbol: "XAUUSD" vm
    lot: 0.01 vm
    """
    token = get_access_token()
    if not token:
        logger.warning("⚠️ cTrader order: token puudub")
        return None

    try:
        ct_symbol = SYMBOL_MAP.get(symbol, symbol)
        volume    = int(lot * 100)  # cTrader: 1 lot = 100 units

        order_data = {
            "accountId":    ACCOUNT_ID,
            "symbolName":   ct_symbol,
            "orderType":    "MARKET",
            "tradeSide":    "BUY" if direction == "buy" else "SELL",
            "volume":       volume,
            "label":        label,
        }

        if tp:
            order_data["takeProfit"] = round(tp, 5)
        if sl:
            order_data["stopLoss"]   = round(sl, 5)

        r = requests.post(
            f"https://openapi.ctrader.com/apps/{CLIENT_ID}/orders",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type":  "application/json"
            },
            json=order_data,
            timeout=15
        )

        if r.status_code in (200, 201):
            data = r.json()
            order_id = data.get("orderId") or data.get("id")
            logger.info(f"✅ cTrader order: {direction.upper()} {ct_symbol} {lot}lot | ID:{order_id}")
            return order_id
        else:
            logger.error(f"cTrader order failed: {r.status_code} — {r.text[:100]}")
            return None

    except Exception as e:
        logger.error(f"cTrader place_order: {e}")
        return None

def close_position(position_id):
    """Sulge positsioon cTrader kontol."""
    token = get_access_token()
    if not token: return False
    try:
        r = requests.delete(
            f"https://openapi.ctrader.com/apps/{CLIENT_ID}/positions/{position_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        return r.status_code in (200, 204)
    except Exception as e:
        logger.error(f"cTrader close: {e}")
        return False

def get_open_positions():
    """Hangi kõik avatud positsioonid cTrader kontolt."""
    token = get_access_token()
    if not token: return []
    try:
        r = requests.get(
            f"https://openapi.ctrader.com/apps/{CLIENT_ID}/accounts/{ACCOUNT_ID}/positions",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.status_code == 200:
            return r.json().get("positions", [])
        return []
    except Exception as e:
        logger.error(f"cTrader positions: {e}")
        return []

def get_account_balance():
    """Hangi konto bilanss otse cTrader-ist."""
    token = get_access_token()
    if not token: return None
    try:
        r = requests.get(
            f"https://openapi.ctrader.com/apps/{CLIENT_ID}/accounts/{ACCOUNT_ID}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=15
        )
        if r.status_code == 200:
            data = r.json()
            balance = data.get("balance", 0) / 100  # cTrader tagastab sentides
            return round(balance, 2)
        return None
    except Exception as e:
        logger.error(f"cTrader balance: {e}")
        return None

def is_connected():
    """Kontrolli kas cTrader ühendus töötab."""
    return get_access_token() is not None

def setup_oauth():
    """
    OAuth seadistamise juhend.
    Kutsutakse esimest korda kui tokenid puuduvad.
    """
    url = get_auth_url()
    return f"""
cTrader OAuth seadistamine:
1. Mine sellele URL-ile brauseris:
   {url}
2. Logi sisse oma cTrader kontoga
3. Kinnita juurdepääs
4. Kopeeri URL-ist 'code' parameeter
5. Anna see kood mulle — lisan botti
"""
