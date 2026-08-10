"""
mt5_connector.py — asendab ctrader.py, identne interface.
Kasutab MetaTrader5 Python teeki (töötab ainult Windowsil).
"""

import os
import time
import logging
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timezone

logger = logging.getLogger("NEMSIS_V4")

MT5_LOGIN   = int(os.environ.get("MT5_LOGIN", "0"))
MT5_PASSWORD = os.environ.get("MT5_PASSWORD", "")
MT5_SERVER  = os.environ.get("MT5_SERVER", "ICMarketsEU-MT5-5")

MAGIC = 234000

_connected = False

_TF_MAP = {
    "1m":  mt5.TIMEFRAME_M1,
    "5m":  mt5.TIMEFRAME_M5,
    "15m": mt5.TIMEFRAME_M15,
    "30m": mt5.TIMEFRAME_M30,
    "1h":  mt5.TIMEFRAME_H1,
    "4h":  mt5.TIMEFRAME_H4,
    "1d":  mt5.TIMEFRAME_D1,
}

_SYMBOL_MAP = {
    "XAU/USD": "XAUUSD",
    "XAUUSD":  "XAUUSD",
    "AUD/CAD": "AUDCAD",
    "AUD/NZD": "AUDNZD",
    "EUR/AUD": "EURAUD",
    "EUR/GBP": "EURGBP",
    "EUR/CHF": "EURCHF",
    "CAD/CHF": "CADCHF",
    "NZD/CAD": "NZDCAD",
    "GBP/CAD": "GBPCAD",
    "EUR/NZD": "EURNZD",
    "GBP/NZD": "GBPNZD",
}


def _connect():
    global _connected
    if _connected:
        return True
    if not mt5.initialize():
        logger.error(f"MT5 initialize failed: {mt5.last_error()}")
        return False
    if not mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        logger.error(f"MT5 login failed: {mt5.last_error()}")
        mt5.shutdown()
        return False
    _connected = True
    logger.info(f"MT5 ühendatud: konto {MT5_LOGIN} @ {MT5_SERVER}")
    return True


def is_connected():
    global _connected
    if not _connected:
        return _connect()
    info = mt5.account_info()
    if info is None:
        _connected = False
        return _connect()
    return True


def start():
    """Käivita MT5 ühendus (ctrader.start() ekvivalent)."""
    _connect()


def refresh_access_token():
    """MT5-l pole tokeneid — ühildusvuse jaoks olemas."""
    pass


def get_price_ctrader(symbol_td):
    """Tagasta hetke bid/ask keskmine."""
    if not is_connected():
        return 0.0
    sym = _SYMBOL_MAP.get(symbol_td, symbol_td.replace("/", ""))
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        logger.error(f"MT5 tick puudub: {sym}")
        return 0.0
    return round((tick.bid + tick.ask) / 2, 5)


def get_candles(symbol_td, interval="1h", count=100):
    """
    Tagasta ajaloolised küünlad DataFramena.
    Kasutab MT5-t otse — yfinance fallback puudub.
    """
    if not is_connected():
        logger.error("MT5 pole ühendatud — küünlad puuduvad")
        return None

    sym = _SYMBOL_MAP.get(symbol_td, symbol_td.replace("/", ""))
    tf  = _TF_MAP.get(interval, mt5.TIMEFRAME_H1)

    rates = mt5.copy_rates_from_pos(sym, tf, 0, count)
    if rates is None or len(rates) == 0:
        logger.error(f"MT5 küünlad puuduvad: {sym} {interval} — {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df.set_index("time", inplace=True)
    df.rename(columns={
        "open": "open", "high": "high",
        "low": "low", "close": "close",
        "tick_volume": "volume"
    }, inplace=True)
    return df[["open", "high", "low", "close", "volume"]]


def place_order(direction, symbol_name, lot, tp=None, sl=None):
    """
    Täida order MT5 kaudu.
    direction: "buy" või "sell"
    symbol_name: MT5 sümbol (nt "XAUUSD")
    lot: maht
    tp/sl: hind (mitte punktid)
    Tagastab dict orderId-ga edukuse korral, {"error": ...} vea korral.
    """
    if not is_connected():
        return {"error": "MT5 pole ühendatud"}

    sym = _SYMBOL_MAP.get(symbol_name, symbol_name.replace("/", ""))
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        return {"error": f"Tick puudub: {sym}"}

    order_type = mt5.ORDER_TYPE_BUY if direction == "buy" else mt5.ORDER_TYPE_SELL
    price = tick.ask if direction == "buy" else tick.bid

    # Küsi broker'i PÄRIS minimaalne stopi-vahemaa (trade_stops_level/
    # trade_freeze_level, punktides) ja laienda TP/SL vajadusel selle
    # täitmiseks — varem lükkas broker mõned scalp-orderid tagasi
    # "Invalid stops" (10016) veaga, kui arvutatud SL/TP jäi liiga lähedale.
    info = mt5.symbol_info(sym)
    min_dist = 0.0
    if info is not None:
        min_stop_points = max(getattr(info, "trade_stops_level", 0),
                               getattr(info, "trade_freeze_level", 0))
        min_dist = min_stop_points * info.point

    request = {
        "action":   mt5.TRADE_ACTION_DEAL,
        "symbol":   sym,
        "volume":   float(lot),
        "type":     order_type,
        "price":    price,
        "deviation": 20,
        "magic":    MAGIC,
        "comment":  "NEMSIS_v4",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    if tp:
        tp_val = float(tp)
        if min_dist > 0:
            if direction == "buy" and tp_val - price < min_dist:
                tp_val = round(price + min_dist, 2)
            elif direction == "sell" and price - tp_val < min_dist:
                tp_val = round(price - min_dist, 2)
        request["tp"] = tp_val
    if sl:
        sl_val = float(sl)
        if min_dist > 0:
            if direction == "buy" and price - sl_val < min_dist:
                sl_val = round(price - min_dist, 2)
            elif direction == "sell" and sl_val - price < min_dist:
                sl_val = round(price + min_dist, 2)
        request["sl"] = sl_val

    result = mt5.order_send(request)
    if result is None:
        return {"error": f"order_send tagastas None: {mt5.last_error()}"}
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return {"error": f"Order ebaõnnestus: {result.retcode} {result.comment}"}

    logger.info(f"✅ MT5 order täidetud: {direction} {lot} {sym} @ {result.price}")
    return {
        "orderId": result.order,
        "price":   result.price,
        "volume":  result.volume,
    }


def close_position(ticket):
    """
    Sulge konkreetne positsioon ticket numbri järgi.
    Tagastab True edukuse korral, False vea korral.
    """
    if not is_connected():
        logger.error("close_position: MT5 pole ühendatud")
        return False

    pos = mt5.positions_get(ticket=ticket)
    if not pos:
        logger.warning(f"close_position: positsioon {ticket} ei leitud MT5-s")
        return False

    p = pos[0]
    sym = p.symbol
    tick = mt5.symbol_info_tick(sym)
    if tick is None:
        logger.error(f"close_position: tick puudub {sym}")
        return False

    close_type = mt5.ORDER_TYPE_SELL if p.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    price = tick.bid if p.type == mt5.ORDER_TYPE_BUY else tick.ask

    request = {
        "action":    mt5.TRADE_ACTION_DEAL,
        "symbol":    sym,
        "volume":    p.volume,
        "type":      close_type,
        "position":  ticket,
        "price":     price,
        "deviation": 20,
        "magic":     MAGIC,
        "comment":   "NEMSIS_v4_close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        err = result.comment if result else mt5.last_error()
        logger.error(f"close_position ebaõnnestus ticket={ticket}: {err}")
        return False

    logger.info(f"✅ Positsioon {ticket} suletud @ {result.price}")
    return True


def get_open_positions(symbol=None):
    """
    Tagasta kõik lahti positsioonid magic=MAGIC filtriga.
    Tagastab listi dict-idega: ticket, symbol, type (buy/sell), volume, price_open, profit, sl, tp
    """
    if not is_connected():
        return []

    if symbol:
        sym = _SYMBOL_MAP.get(symbol, symbol.replace("/", ""))
        positions = mt5.positions_get(symbol=sym)
    else:
        positions = mt5.positions_get()

    if positions is None:
        return []

    result = []
    for p in positions:
        if p.magic != MAGIC:
            continue
        result.append({
            "ticket":     p.ticket,
            "symbol":     p.symbol,
            "direction":  "buy" if p.type == mt5.ORDER_TYPE_BUY else "sell",
            "volume":     p.volume,
            "price_open": p.price_open,
            "profit":     p.profit,
            "sl":         p.sl,
            "tp":         p.tp,
        })
    return result


def get_account_balance():
    """Tagasta konto saldo."""
    if not is_connected():
        return None
    info = mt5.account_info()
    if info is None:
        return None
    return info.balance


def get_account_equity():
    """Tagasta konto equity (balance + lahtiste positsioonide P&L)."""
    if not is_connected():
        return None
    info = mt5.account_info()
    if info is None:
        return None
    return info.equity
