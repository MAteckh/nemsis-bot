"""
weekly_report.py — PÄRIS nädala tulemus MT5 tehinguajaloost.

Miks see fail vajalik: trades-tabel Supabase's oli tühi kuni 11 sept
(vt CLAUDE.md), nii et minevikutehingute päris tulemust ei saa
andmebaasist lugeda. Hinnaandmete pealt rekonstrueerimine (mida prooviti)
EI arvesta boti trendipöörde-loogikat (kõik vastutrendi positsioonid
suletakse käsitsi trendi vahetudes, mitte alati SL-i tabamisel) ja
seetõttu ülehindab kahjumit.

See skript küsib PÄRIS tulemuse otse MT5-lt — history_deals_get() —
ja eristab:
  - boti enda tehingud (magic=234000)
  - käsitsi/muu tehingud (muu magic, nt naise oma)
  - konto BALANSSI operatsioonid (sisse-/väljamaksed) — MT5 logib
    need eraldi "DEAL_TYPE_BALANCE" tüübina, seega saab eristada
    "kaotasin trading'uga" vs "võtsin välja".

Kasuta VPS-il (Windows, kus MT5 on installitud):
    python weekly_report.py [paevi_tagasi]
Vaikimisi 14 paeva.
"""
import sys
from datetime import datetime, timedelta, timezone
import MetaTrader5 as mt5
import mt5_connector as ct

MAGIC = ct.MAGIC


def main():
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 14
    if not ct.is_connected():
        print("MT5 ei ühendunud — kontrolli, kas MT5 terminal on lahti ja .env on õige.")
        return

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    deals = mt5.history_deals_get(start, now)
    if deals is None:
        print(f"Tehinguajalugu puudub: {mt5.last_error()}")
        return

    bot_pnl = other_pnl = balance_ops = 0.0
    bot_n = other_n = 0
    print(f"{'aeg':19s} {'tuup':10s} {'symbol':10s} {'maht':>7s} {'hind':>10s} {'pnl':>9s}  magic")
    print("-" * 90)
    for d in sorted(deals, key=lambda x: x.time):
        t = datetime.fromtimestamp(d.time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        pnl = d.profit + d.commission + d.swap
        if d.type == mt5.DEAL_TYPE_BALANCE:
            balance_ops += d.profit
            print(f"{t:19s} {'BALANSS':10s} {'--':10s} {'--':>7s} {'--':>10s} {d.profit:+9.2f}  "
                  f"({d.comment!r})")
            continue
        if d.entry != mt5.DEAL_ENTRY_OUT:
            continue  # ainult sulgemis-deal'id, avamine ei kanna realiseeritud P&L-i
        own = d.magic == MAGIC
        if own:
            bot_pnl += pnl; bot_n += 1
        else:
            other_pnl += pnl; other_n += 1
        print(f"{t:19s} {'sulgemine':10s} {d.symbol:10s} {d.volume:7.2f} {d.price:10.2f} "
              f"{pnl:+9.2f}  magic={d.magic}{' (BOT)' if own else ' (MUU)'}")

    print("-" * 90)
    print(f"\nViimased {days} päeva ({start.date()} .. {now.date()}):")
    print(f"  Boti tehingud:        {bot_n:3d} tk   kokku {bot_pnl:+9.2f}")
    print(f"  Muud/käsitsi tehingud:{other_n:3d} tk   kokku {other_pnl:+9.2f}")
    print(f"  Sisse-/väljamaksed:              kokku {balance_ops:+9.2f}")
    print(f"  KOKKU balansi muutus:            {bot_pnl+other_pnl+balance_ops:+9.2f}")


if __name__ == "__main__":
    main()
