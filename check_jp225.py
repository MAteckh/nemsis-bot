"""
DIAGNOSTIKA — JP225 kaubeldavus BlackBulli kontol.  JOOKSUTA VPS-il.

See skript EI KAUPLE MIDAGI. Ta ainult loeb sumboli spetsifikatsiooni ja
kirjutab valja, kas paevasisene JP225 strateegia on 200EUR kontol
uldse teostatav.

Kasutus VPS-il (PowerShell, kaustas C:\\nemsis-bot):
    python check_jp225.py

VOIB JOOKSUTADA SAMAL AJAL, KUI BOT TOOTAB. Skript ei kauple ega
muuda midagi, ja ta EI LOGI UUESTI SISSE, kui terminal on juba
sisse logitud (mt5.login() teises protsessis voiks jooksva boti
uhenduse segada — seepaerast proovime esmalt lihtsalt kulge haakuda).

Miks see on kriitiline:
Kogu selle strateegia saatuse otsustab LEPINGU SUURUS ja MIINIMUM-LOT.
Kui uks miinimum-lot tahendab 3600EUR notsionaali, siis on uks keskmine
paev +/-17% kontost — sama miinimum-loti probleem, mis muutis kulla
1.5% riski 25-49% riskiks. Kui aga miinimum-lot annab ~350EUR
notsionaali, siis on risk ~1.7% ja strateegia on teostatav.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# .env laadimine — main_v4.py teeb sama. Ilma selleta on MT5_LOGIN ja
# MT5_PASSWORD tuhjad ja varu-sisselogimine allpool ebaonnestuks.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import MetaTrader5 as mt5
except ImportError:
    print("MetaTrader5 teek puudub — see skript töötab AINULT VPS-il (Windows).")
    sys.exit(1)

CANDIDATES = ["JP225", "JPN225", "JP225.cash", "Nikkei225", "NIKKEI",
              "JPN225.cash", "J225", "JP225Cash", "JPY225"]

# 1) Haaki kulge juba tootava terminali kulge — ILMA login'ita.
acc = None
if mt5.initialize():
    acc = mt5.account_info()

# 2) Ainult kui see ei andnud kontot, logi sisse .env andmetega.
if acc is None:
    print("Terminal ei olnud sisse logitud — login .env andmetega...")
    import mt5_connector as ct
    if not ct._connect():
        print("MT5 ühendus ebaõnnestus:", mt5.last_error())
        print("Kontrolli, et MT5 terminal on lahti ja .env failis on")
        print("MT5_LOGIN, MT5_PASSWORD ja MT5_SERVER.")
        sys.exit(1)
    acc = mt5.account_info()

if acc is None:
    print("account_info() tagastas None — MT5 terminal ei ole sisse logitud.")
    sys.exit(1)

print("=" * 78)
print(f"KONTO {acc.login}  {acc.server}   balance {acc.balance:.2f} {acc.currency}")
print(f"equity {acc.equity:.2f}   vaba marginaal {acc.margin_free:.2f}   "
      f"leverage 1:{acc.leverage}")
print("=" * 78)

found = None
for cand in CANDIDATES:
    info = mt5.symbol_info(cand)
    if info is None:
        continue
    if not info.visible:
        mt5.symbol_select(cand, True)
        info = mt5.symbol_info(cand)
    if info is not None:
        found = (cand, info)
        break

if found is None:
    print("\nJP225 EI LEITUD ühegi nime alt:", ", ".join(CANDIDATES))
    print("\nOtsin kõigist sümbolitest midagi Nikkei-sarnast...")
    for s in (mt5.symbols_get() or []):
        n = s.name.upper()
        if "225" in n or "NIK" in n or "JPN" in n:
            print("   kandidaat:", s.name)
    sys.exit(0)

name, info = found
tick = mt5.symbol_info_tick(name)
print(f"\nLEITUD: {name}   ({info.description})")
print("-" * 78)
print(f"  lepingu suurus (trade_contract_size) : {info.trade_contract_size}")
print(f"  miinimum lot (volume_min)            : {info.volume_min}")
print(f"  lot-samm (volume_step)               : {info.volume_step}")
print(f"  maksimum lot (volume_max)            : {info.volume_max}")
print(f"  point                                : {info.point}")
print(f"  digits                               : {info.digits}")
print(f"  praegune spread (punktides)          : {info.spread}")
print(f"  min stopi kaugus (trade_stops_level) : {info.trade_stops_level}")
print(f"  baasvaluuta / kasumivaluuta          : {info.currency_base} / {info.currency_profit}")
print(f"  swap long / short                    : {info.swap_long} / {info.swap_short}")
print(f"  kauplemisrežiim (trade_mode)         : {info.trade_mode}  (4 = täisulatus)")
if tick:
    print(f"  bid / ask                            : {tick.bid} / {tick.ask}")
    if tick.ask and tick.bid:
        sp_bp = 1e4 * (tick.ask - tick.bid) / ((tick.ask + tick.bid) / 2)
        print(f"  spread baaspunktides                 : {sp_bp:.2f}bp "
              f"(strateegia eeldas 3.0bp ühesuunaline)")

px = tick.ask if tick else info.trade_contract_size
minlot = info.volume_min
notional_profit_ccy = px * info.trade_contract_size * minlot

print("\n" + "-" * 78)
print("MIINIMUM-POSITSIOONI MÕJU")
print("-" * 78)
print(f"  notsionaal ({info.currency_profit}) miinimum-lotiga: {notional_profit_ccy:,.0f}")

margin = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, name, minlot, px)
if margin is not None:
    print(f"  nõutav marginaal ({acc.currency})            : {margin:,.2f}")
    print(f"  osa vabast marginaalist                : "
          f"{100*margin/max(acc.margin_free,1e-9):.1f}%")

# 1 std paevasisene liikumine oli ajaloos 0.94%
STD_MOVE = 0.0094
prof = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, name, minlot, px, px * (1 + STD_MOVE))
if prof is not None:
    print(f"\n  TÜÜPILINE PÄEV (+0.94% liikumine), miinimum-lot:")
    print(f"     kasum/kahjum : {prof:+,.2f} {acc.currency}")
    print(f"     osa kontost  : {100*abs(prof)/max(acc.balance,1e-9):.1f}%")
    worst = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, name, minlot, px, px * (1 - 0.0816))
    if worst is not None:
        print(f"  HALVIM AJALOOLINE PÄEV (-8.16%), miinimum-lot:")
        print(f"     kahjum       : {worst:+,.2f} {acc.currency}")
        print(f"     osa kontost  : {100*abs(worst)/max(acc.balance,1e-9):.1f}%")

    r = 100 * abs(prof) / max(acc.balance, 1e-9)
    print("\n" + "=" * 78)
    if r <= 2.5:
        print(f"  OTSUS: TEOSTATAV. Tüüpiline päev = {r:.1f}% kontost (siht 1-2%).")
    elif r <= 6.0:
        print(f"  OTSUS: PIIRIPEALNE. Tüüpiline päev = {r:.1f}% kontost — liiga suur,")
        print(f"         aga mitte hukatuslik. Vajab suuremat kontot.")
    else:
        print(f"  OTSUS: EI OLE TEOSTATAV selle konto suurusega.")
        print(f"         Tüüpiline päev = {r:.1f}% kontost. Sama miinimum-loti")
        print(f"         probleem, mis kullal. Vajalik konto ~"
              f"{acc.balance * r / 1.5:,.0f} {acc.currency}.")
    print("=" * 78)

print("\nKAUPLEMISAJAD (Jaapani sessioon on 00:00-06:00 UTC):")
# symbol_info_session_quote/-trade ei ole koigis MetaTrader5 teegi
# versioonides olemas — VPS-il andis see AttributeError'i. Kusi
# getattr'iga ja utle ausalt, kui teek seda ei paku.
_sess = getattr(mt5, "symbol_info_session_trade", None)
if _sess is None:
    print("   (see MetaTrader5 teegi versioon ei paku sessiooniaegade lugemist —")
    print("    vaata need vajadusel MT5 terminalist: Market Watch -> Specification)")
else:
    paevad = ["esmaspäev", "teisipäev", "kolmapäev", "neljapäev",
              "reede", "laupäev", "pühapäev"]
    for d in range(7):
        try:
            t = _sess(name, d, 0)
        except Exception:
            t = None
        if t:
            print(f"   {paevad[d]:12s} {t.open} .. {t.close}")

mt5.shutdown()
