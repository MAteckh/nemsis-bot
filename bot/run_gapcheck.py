import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R

# Millised Yahoo sumbolid: sulgeb turg paris voi kaupleb 24h?
SRC = {
 "SPX":("^GSPC","kassaindeks, SULGEB 16:00 ET"), "NAS100":("^NDX","kassaindeks, SULGEB"),
 "GER40":("^GDAXI","kassaindeks, SULGEB"), "JP225":("^N225","kassaindeks, SULGEB"),
 "UK100":("^FTSE","kassaindeks, SULGEB"),
 "XAUUSD":("GC=F","FUTUUR, kaupleb ~23h"), "XAGUSD":("SI=F","FUTUUR, ~23h"),
 "COPPER":("HG=F","FUTUUR, ~23h"), "WTI":("CL=F","FUTUUR, ~23h"), "NGAS":("NG=F","FUTUUR, ~23h"),
 "US10Y":("ZN=F","FUTUUR, ~23h"),
 "EURUSD":("EURUSD=X","FX, 24/5"), "GBPUSD":("GBPUSD=X","FX, 24/5"),
 "USDJPY":("USDJPY=X","FX, 24/5"), "AUDUSD":("AUDUSD=X","FX, 24/5"),
 "USDCAD":("USDCAD=X","FX, 24/5"), "USDCHF":("USDCHF=X","FX, 24/5"),
 "NZDUSD":("NZDUSD=X","FX, 24/5"), "EURJPY":("EURJPY=X","FX, 24/5"),
 "BTCUSD":("BTC-USD","24/7 - 'oo' pole olemas"), "ETHUSD":("ETH-USD","24/7"),
}

print("=" * 120)
print("METOODIKA KONTROLL: kas 'ooine tootlus' on paris aken voi mooteartefakt?")
print("=" * 120)
print(f"{'sumbol':9s} {'Yahoo':11s} {'iseloom':26s} {'|gap|/|paevaliikumine|':>22s} {'gap==0 osa':>11s}  verdikt")
print("-" * 120)
for s in sorted(SRC):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p): continue
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna()
    gap = (d["Open"] / d["Close"].shift(1) - 1).abs()
    day = (d["Close"] / d["Open"] - 1).abs()
    ratio = gap.mean() / day.mean() if day.mean() else np.nan
    zero = (gap < 1e-9).mean()
    yh, kind = SRC[s]
    if zero > 0.30:
        v = "KAHTLANE: Open==eelm Close"
    elif "FUTUUR" in kind or "24/5" in kind or "24/7" in kind:
        v = "ARTEFAKT: turg ei sulge"
    else:
        v = "OK - paris ooaken"
    print(f"{s:9s} {yh:11s} {kind:26s} {ratio:22.2f} {100*zero:10.1f}%  {v}")
