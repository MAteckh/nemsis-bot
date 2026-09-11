"""Rekonstrueeri 4.-11. sept grid-tehingute PARIS tulemus H1 hinnaajaloo pealt,
kuna trades-tabel oli sel ajal tuhi (parandati alles 11 sept).

HOIATUS — TULEMUS ON TOENAOLISELT OLULISELT ULEHINNATUD, ARA USALDA SEDA:
see eeldab, et iga positsioon soidab oma TP/SL-ini. Paris grid-kood
(main_v4.py run_gold_grid, "trend reset" haru) sulgeb aga KOIK
vastutrendi positsioonid KASITSI trendi poordumisel, praeguse HINNAGA —
mitte alati SL tabamisel. Kui trend nadala jooksul mitu korda poordus
(mida gold_bear/gold_bull vaheldumine signals-tabelis viitab), suleti
paljud positsioonid varem ja vaiksema kahjumiga kui see skript eeldab.

Jooksutamisel sai tulemuseks -1075$ nadala kohta, mis ON FUUSILISELT
EBAUSUTAV 305€ konto jaoks (tahendaks konto mitmekordset hovimist,
mida circuit breaker (paevane -10%/nadalane -15%) oleks ammu peatanud).
Ara tsiteeri seda numbrit kellelegi kui paris tulemust.

PARIS vastuse jaoks kasuta weekly_report.py, mis loeb PARIS suletud
deal'id otse MT5 tehinguajaloost (toimib ainult VPS-il, kus MT5 on)."""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np

h1 = pd.read_csv("data/XAUUSD_h1.csv", parse_dates=["Date"]).set_index("Date").sort_index()
h1 = h1[~h1.index.duplicated(keep="last")]
for c in ("Open","High","Low","Close"): h1[c] = pd.to_numeric(h1[c], errors="coerce")
h1 = h1.dropna()

signals = [
 # (id, session, direction, entry, tp, sl, lot, created_at)
 (182,"gold_bear","sell",4470.16,4440.16,4515.16,0.01,"2026-09-04 01:32:24"),
 (183,"gold_bull","buy", 4486.79,4516.79,4441.79,0.01,"2026-09-04 07:50:32"),
 (184,"gold_bear","sell",4465.37,4435.37,4510.37,0.01,"2026-09-04 09:26:59"),
 (185,"gold_bear","sell",4407.02,4377.02,4452.02,0.01,"2026-09-04 12:33:46"),
 (186,"scalp_bear","sell",4407.02,4395.02,4432.02,0.01,"2026-09-04 12:33:51"),
 (187,"scalp_bear","sell",4394.66,4382.66,4419.66,0.02,"2026-09-04 12:35:00"),
 (188,"scalp_bear","sell",4388.43,4376.43,4413.43,0.02,"2026-09-04 12:36:08"),
 (189,"gold_bear","sell",4390.87,4360.87,4435.87,0.01,"2026-09-04 12:46:08"),
 (190,"gold_bear","sell",4405.03,4375.03,4450.03,0.01,"2026-09-04 12:54:59"),
 (191,"gold_bear","sell",4383.64,4353.64,4428.64,0.01,"2026-09-04 13:03:48"),
 (192,"scalp_bear","sell",4380.95,4368.95,4405.95,0.02,"2026-09-04 13:04:55"),
 (193,"scalp_bear","sell",4379.36,4367.36,4404.36,0.02,"2026-09-04 13:06:03"),
 (194,"scalp_bear","sell",4383.45,4371.45,4408.45,0.02,"2026-09-04 13:07:11"),
 (195,"scalp_bear","sell",4385.81,4373.81,4410.81,0.02,"2026-09-04 13:08:19"),
 (196,"scalp_bear","sell",4387.53,4375.53,4412.53,0.02,"2026-09-04 13:09:26"),
 (197,"gold_bear","sell",4406.83,4376.83,4451.83,0.01,"2026-09-07 01:07:51"),
 (198,"gold_bear","sell",4396.75,4366.75,4441.75,0.01,"2026-09-08 07:46:07"),
 (199,"gold_bear","sell",4397.23,4367.23,4442.23,0.01,"2026-09-08 13:37:53"),
 (200,"gold_bear","sell",4357.26,4327.26,4402.26,0.01,"2026-09-09 01:03:35"),
 (201,"gold_bear","sell",4379.15,4349.15,4424.15,0.01,"2026-09-09 03:14:38"),
 (202,"gold_bear","sell",4379.82,4349.82,4424.82,0.01,"2026-09-09 15:22:52"),
 (203,"gold_bull","buy", 4417.76,4447.76,4372.76,0.01,"2026-09-09 18:04:07"),
 (204,"gold_bear","sell",4384.37,4354.37,4429.37,0.01,"2026-09-10 10:41:35"),
 (205,"scalp_bear","sell",4348.91,4336.91,4373.91,0.01,"2026-09-10 12:34:01"),
 (206,"scalp_bear","sell",4341.45,4329.45,4366.45,0.01,"2026-09-10 12:35:09"),
 (207,"scalp_bear","sell",4335.59,4323.59,4360.59,0.01,"2026-09-10 12:37:25"),
 (208,"scalp_bear","sell",4327.92,4315.92,4352.92,0.01,"2026-09-10 12:38:33"),
 (209,"gold_bear","sell",4327.08,4297.08,4372.08,0.01,"2026-09-10 12:40:47"),
 (210,"gold_bear","sell",4347.35,4317.35,4392.35,0.01,"2026-09-10 12:49:48"),
 (211,"gold_bear","sell",4342.52,4312.52,4387.52,0.01,"2026-09-10 12:58:43"),
 (212,"gold_bull","buy", 4355.83,4385.83,4310.83,0.01,"2026-09-11 06:02:47"),
 (213,"gold_bull","buy", 4355.45,4385.45,4310.45,0.01,"2026-09-11 06:11:26"),
]

def find_exit(entry_time, direction, tp, sl):
    fut = h1[h1.index > entry_time]
    if fut.empty:
        return None, None, None
    for t, bar in fut.iterrows():
        hi, lo = bar["High"], bar["Low"]
        tp_hit = (hi >= tp) if direction == "buy" else (lo <= tp)
        sl_hit = (lo <= sl) if direction == "buy" else (hi >= sl)
        if tp_hit and sl_hit:
            return "sl(mõlemad korraga)", sl, t
        if tp_hit:
            return "tp", tp, t
        if sl_hit:
            return "sl", sl, t
    return "LAHTI (pole veel tabatud)", None, None

print(f"{'id':>4s} {'session':11s} {'suund':5s} {'entry':>9s} {'tulemus':>26s} {'pnl$':>9s}  suletud")
print("-" * 100)
total = 0.0
for sid, sess, d, entry, tp, sl, lot, ts in signals:
    et = pd.Timestamp(ts)
    reason, exit_px, exit_t = find_exit(et, d, tp, sl)
    if exit_px is None:
        print(f"{sid:4d} {sess:11s} {d:5s} {entry:9.2f} {reason:>26s} {'--':>9s}")
        continue
    pnl = (exit_px - entry) * lot * 100 if d == "buy" else (entry - exit_px) * lot * 100
    total += pnl
    print(f"{sid:4d} {sess:11s} {d:5s} {entry:9.2f} {reason:>26s} {pnl:+9.2f}  {exit_t}")

print("-" * 100)
print(f"KOKKU (rekonstrueeritud, H1 baaride pohjal, ei arvesta spread/slippage): {total:+.2f}$")
