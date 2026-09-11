import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import intraday as I

for sym in ("XAUUSD", "WTI"):
    df = I.load_h1(sym)
    print("=" * 104)
    print(f"{sym}  —  {len(df)} tunnibaari  {df.index[0]} .. {df.index[-1]}")
    print("=" * 104)

    intr, over = I.overnight_split(df)
    n = min(len(intr), len(over))
    print(f"  PAEVASISENE (avamine->sulgemine) : kokku {100*((1+intr).prod()-1):+8.1f}%   "
          f"keskm {1e4*intr.mean():+6.1f}bp/p   Sharpe {intr.mean()/intr.std()*np.sqrt(252):+5.2f}")
    print(f"  OOINE      (sulgemine->avamine)  : kokku {100*((1+over).prod()-1):+8.1f}%   "
          f"keskm {1e4*over.mean():+6.1f}bp/p   Sharpe {over.mean()/over.std()*np.sqrt(252):+5.2f}")

    hp = I.hour_profile(df)
    print(f"\n  TUNNIPROFIIL (UTC) — 'sama' = molemad ajapooled sama margiga")
    print(f"  {'h':>3s} {'n':>5s} {'kogu bp':>9s} {'1.pool':>8s} {'2.pool':>8s} {'t':>6s}  sama")
    for _, r in hp.iterrows():
        star = " *" if abs(r["t"]) > 2 and r["sama_margi"] else ""
        print(f"  {int(r['h']):3d} {int(r['n']):5d} {r['bp']:+9.2f} {r['bp_1pool']:+8.2f} "
              f"{r['bp_2pool']:+8.2f} {r['t']:+6.2f}  {'jah' if r['sama_margi'] else 'ei '}{star}")
    rob = hp[(hp["t"].abs() > 2) & (hp["sama_margi"])]
    print(f"\n  -> statistiliselt oluline JA molemas ajapooles sama suund: "
          f"{len(rob)} tundi {len(hp)}-st" + (f"  => {list(rob['h'].astype(int))}" if len(rob) else ""))
    print()
