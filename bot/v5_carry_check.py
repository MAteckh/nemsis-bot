"""
KAS CURRENCYSHARES ETF-idest SAAB INTRESSIVAHE KATTE?

IDEE: FXE hoiab euro-hoiust, mis TEENIB euro intressi. Tema tootlus on
  FXE_return ~ EURUSD spot muutus + EUR intress - fondi kulu (0.40%/a)
Seega
  FXE_return - EURUSD_return ~ EUR intress - 0.40%
Ja kuna USD-s istudes teeniksid USD intressi, on carry
  carry(EUR) = (FXE_return - EURUSD_return) + 0.40% - USD_intress

VALIDEERIMINE ENNE KASUTAMIST: kui tuletus toimib, peab tulemus
KATTUMA teadaoleva makropildiga:
  2016-2021: EUR intress NEGATIIVNE, JPY negatiivne, USD 0-2%
             => EUR ja JPY carry tugevalt NEGATIIVNE
  2023-2026: USD 4-5%, EUR 2-4%, JPY ~0-0.5%
             => JPY carry endiselt koige negatiivsem
  AUD: enamasti korgem kui USD kuni 2022, siis madalam
Kui need mustrid EI tule valja, on tuletus katki ja ma EI TOHI seda
kasutada.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np, pandas as pd

def lae(f, nimi=None):
    d = pd.read_csv(f"data/{f}", parse_dates=["Date"]).set_index("Date").sort_index()
    d.columns = [c.strip().lower() for c in d.columns]
    d = d[~d.index.duplicated(keep="last")]
    return pd.to_numeric(d["close"], errors="coerce").dropna().rename(nimi or f)

# ETF (sisaldab intressi)  vs  SPOT (ainult hinnaliikumine)
# FXE ~ EURUSD; FXB ~ GBPUSD; FXA ~ AUDUSD  (koik USD kohta)
# FXY ~ JPYUSD = 1/USDJPY ; FXF ~ CHFUSD = 1/USDCHF ; FXC ~ CADUSD = 1/USDCAD
ETF  = {"EUR":"FXEA_d.csv","GBP":"FXBA_d.csv","JPY":"FXYA_d.csv",
        "AUD":"FXAA_d.csv","CHF":"FXFA_d.csv","CAD":"FXCA_d.csv"}
SPOT = {"EUR":("EURUSD_d.csv",False),"GBP":("GBPUSD_d.csv",False),
        "JPY":("USDJPY_d.csv",True),"AUD":("AUDUSD_d.csv",False),
        "CHF":("USDCHF_d.csv",True),"CAD":("USDCAD_d.csv",True)}
KULU_ETF = 0.0040          # CurrencyShares haldustasu 0.40%/a

print("="*88)
print("CARRY-TULETUSE VALIDEERIMINE — kas ETF miinus spot annab intressivahe?")
print("="*88)
print("Arvutatud: (ETF tootlus - spot tootlus) + 0.40% haldustasu")
print("= valuuta X intress MIINUS USD intress, aastapohiselt")
print()
print(f"  {'valuuta':>8s} " + "".join(f"{a:>9d}" for a in range(2017, 2027)))
print("  " + "-"*(8+9*10))

read = {}
for val, ef in ETF.items():
    e = lae(ef, "etf")
    sf, poord = SPOT[val]
    s = lae(sf, "spot")
    if poord:
        s = 1.0 / s                       # USDJPY -> JPYUSD
    ix = e.index.intersection(s.index)
    re_ = e.reindex(ix).pct_change()
    rs_ = s.reindex(ix).pct_change()
    vahe = (re_ - rs_).dropna()
    read[val] = vahe
    rida = f"  {val:>8s} "
    for a in range(2017, 2027):
        g = vahe[vahe.index.year == a]
        rida += f"{100*(g.mean()*252 + KULU_ETF):>8.2f}%" if len(g) > 100 else f"{'-':>9s}"
    print(rida)

print()
print("  OOTUS (teadaolev makropilt), kui tuletus TÖÖTAB:")
print("    2017-2021: EUR ja JPY peavad olema NEGATIIVSED (USD intress kõrgem)")
print("    2023-2026: JPY kõige negatiivsem; EUR negatiivne aga vähem")
print("    AUD 2017-2019 ~0 või kergelt negatiivne; 2023+ negatiivne")
print()

# kontroll: kas margid vastavad?
ok = []
for val in ("EUR","JPY"):
    g = read[val]
    varane = g[(g.index.year>=2017)&(g.index.year<=2021)]
    v = 100*(varane.mean()*252 + KULU_ETF)
    ok.append(v < 0)
    print(f"  KONTROLL {val} 2017-2021: {v:+.2f}%  "
          f"{'OK (negatiivne, nagu peab)' if v < 0 else 'VIGA (peaks olema negatiivne)'}")

g = read["JPY"]; h = read["EUR"]
hilja_j = 100*(g[g.index.year>=2023].mean()*252 + KULU_ETF)
hilja_e = 100*(h[h.index.year>=2023].mean()*252 + KULU_ETF)
print(f"  KONTROLL JPY vs EUR 2023-2026: JPY {hilja_j:+.2f}%, EUR {hilja_e:+.2f}%  "
      f"{'OK (JPY madalam)' if hilja_j < hilja_e else 'VIGA'}")
ok.append(hilja_j < hilja_e)

print()
print("="*88)
if all(ok):
    print("TULETUS TÖÖTAB — carry on andmetest kättesaadav, võib testida.")
else:
    print("TULETUS EI TÖÖTA — carry't EI TOHI nende andmetega testida.")
print("="*88)
