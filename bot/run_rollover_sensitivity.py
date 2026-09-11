import warnings; warnings.filterwarnings("ignore")
import importlib
import run_daily_reset as D
import numpy as np

print("Tundlikkus rollover-kellaaja eelduse suhtes:")
print(f"{'rollover UTC':>13s} {'HOLD net':>10s} {'RESET net':>10s} {'vahe':>9s} {'keskm resets':>13s}")
for hour in (18, 19, 20, 21, 22, 23):
    D.ROLLOVER_UTC_HOUR = hour
    hold_res = [D.simulate_trade(d, dirn, sl, tp, "hold") for d, dirn, sl, tp in D.signals]
    reset_res = [D.simulate_trade(d, dirn, sl, tp, "reset") for d, dirn, sl, tp in D.signals]
    hold_res = [r for r in hold_res if r]; reset_res = [r for r in reset_res if r]

    hold_net = 0.0
    for r in hold_res:
        days = max(1, int(round(r["days"])))
        rate = float(D.rates.iloc[-1])
        notional = D.LOT*100*4300
        fin = notional*(rate+D.MK)*days/365.0
        hold_net += r["gross"] - 2*D.SPREAD_ONE_WAY*(D.LOT/0.01) - fin

    reset_net = sum(r["gross"] - 2*D.SPREAD_ONE_WAY*(D.LOT/0.01) for r in reset_res)
    avg_resets = np.mean([r["resets"] for r in reset_res])
    print(f"{hour:>10d}:00 {hold_net:10.0f} {reset_net:10.0f} {reset_net-hold_net:+9.0f} {avg_resets:13.1f}")
