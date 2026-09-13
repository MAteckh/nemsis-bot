# NEMSIS — mida on testitud ja mis välja tuli

Koostatud 12. sept 2026. Kokkuvõte 59 commitist ja 66 analüüsiskriptist
(10.–12. sept 2026).

**Miks see fail on olemas:** et keegi — sina ise kuu aja pärast või uus
vestlus — ei peaks sama asja uuesti testima. Iga rida siin on tehtud
testi tulemus, mitte arvamus. Skripti nimi on iga leiu juures.

---

## 1. Boti praegune seis

| | |
|---|---|
| Konto | BlackBull 525854 LIVE, ~205€ |
| Aktiivne | Portfell, **1 jalg: XAUUSD donchian(50)**, päevabaarid |
| Väljas | Kulla grid, scalp, core_overlay (`INSTRUMENTS["XAUUSD"]["enabled"]=False`) |
| Väljas | Kõik 10 forex meanrev instrumenti |
| Eemaldatud | SPX, USDJPY, EURUSD jalad (12. sept, põhjused all) |

**Kaitsed:**
- `portfolio_max_loss_eur = 45.0` — SL-i kaugus piiratakse, läheb brokerile
- `portfolio_max_open_total = 1` — korraga max 1 positsioon kokku
- Circuit breaker −10% päevas / −15% nädalas (peatab **uued** tehingud,
  ei sulge avatud positsiooni)

**Päris risk tehingu kohta: 22% kontost** (oli 68% enne 12. sept lage).

⚠️ **Pikim kaotusseeria ajaloos: 4 tehingut.** Juhtunud 2 korda 6,7 aasta
jooksul, viimane **31. august 2026**. Neli kaotust × 45€ = konto 25€ peal.

---

## 2. Põhiline aritmeetika (kõige tähtsam osa)

Tootlus on **protsent kapitalist**. Maailma parimad teevad ~20%/aastas.

```
20% × 205€      =    41€ aastas  =  0,11€/päevas
20% × 180 000€  = 36 000€ aastas =  3 000€/kuus
```

**Sama bot, sama kood. Vahet teeb ainult kapital.**

Parim strateegia, mis leiti (JP225, Sharpe +1,87), 205€ kontol:

| Võimendus | Kuus | Päevas | Parim päev | Laostumine |
|---|---|---|---|---|
| 1x | 3€ | 0,11€ | +22€ | 0% |
| 5x | 17€ | **0,56€** | +110€ | 0% |
| 8x | 27€ | 0,90€ | +175€ | suri 2019 |
| 10x | 34€ | 1,12€ | +219€ | suri 2018 |

**5x on ülemine piir** — 8x ja 10x tapsid konto päris ajaloolises jadas.

**Mis on vaja 1000€/kuus jaoks:** 60 000€ (1x) või 12 000€ (5x).
Aga 12 000€/5x kontolt 1000€/kuus välja võttes elab konto 10 aastat üle
ainult **32%** juhtudest (`run_withdraw.py`).

> **"Jõuda X-ni" ja "omada X sissetulekut" ei ole sama asi.**

---

## 3. Mis on testitud ja LÄBI KUKKUNUD

### Strateegiaperekonnad

| Perekond | Skript | Tulemus |
|---|---|---|
| Kulla grid (31 konfi) | `run_grid_fixes`, `run_grid_tpsl` | **Kõik 31 surevad** |
| Grid viimasel 2 aastal | `run_grid_windows`, `run_grid_protect` | Kõik surevad |
| Grid ilma kaitseteta | `run_grid_noprotect`, `run_grid_ruin` | **Kõik 18 lahtrit surevad** |
| Paariskauplemine (63 kombot) | `run_pairs` | Parim Sharpe +0,26 |
| Regiimivahetus | `run_regime_switch` | 8/21 positiivne CAGR |
| Öine triiv (10 instrumenti) | `run_overnight_all` | Anomaalia on päris (t=+2,3…+4,2), aga kulud söövad ära |
| Breakout-straddle | `run_vol_breakout` → `run_breakout_h1` | Päevabaaridel +4,76, **H1-l −1,48** |
| Krüpto trend (8 strateegiat) | `run_crypto_trend` | Ükski ei löö osta-ja-hoia |
| M5 kuld (4 perekonda) | `run_m5_feasible`, `run_m5_intraday` | Kõik läbi kukkunud |
| Akadeemilised anomaaliad | `run_academic_anomalies` | Kõik 3 |
| VIX-signaal | `run_vix_signal` | Nõrk, hajus |
| Kulla hooajalisus | `run_gold_seasonality` | Ei tööta |
| Prop-firma | `run_propfirm`, `run_propfirm_jp225` | 50% läbimine 1x juures |

### Miks portfelli jalad eemaldati (`run_legs_exact`)

Täpselt need seaded, mis configis olid, 200€ konto, lot 0,01:

| Jalg | P&L | Võit% | Madalaim konto | Poolte-test |
|---|---|---|---|---|
| SPX bollinger_fade | +1 370€ | 54,9% | **−45,46€** 🛑 | läbib |
| USDJPY donchian_trend | +156€ | 38,7% | 94,60€ | **ei läbi** |
| EURUSD ts_momentum(60) | +137€ | 40,0% | 165,80€ | läbib |

- **SPX** teenis kõige rohkem ja **lõi konto tühjaks** (53% riski tehingu kohta)
- **USDJPY** ei läbi poolte-testi
- **EURUSD** risk on ainus korralik (4,1%), aga serv on **üks aasta**:
  2023 üksi +125,40€ = **92% kogu 10 aasta kasumist**; ilma 2023-ta
  +11,10€ üheksa aasta peale; 5/10 positiivset aastat; 2026 −55,40€

---

## 4. Ainus leid, mis kontrollid läbis — ja miks ta kasutamata jäi

**SPX → JP225 päevasisene** (`run_jp225_*`): osta/müü JP225 Jaapani
avanemisel eilse SPX-i suunas, kui |z| > 1,0, sulge sulgemisel.
Päevasisene ⇒ **null finantseerimist** (5,42%/a, mis tappis kõik muu).

**Läbis:** monotoonne plato, sama SPX/NAS100/keskmisega, vol-aken 20…250p,
OOS (lävend 1. poolel → 2. poolel Sharpe +1,66), permutatsioonitest
p<0,0002, kontsentratsioon (ilma 5 parima päevata +1,35), andmete
terviklikkus, **kuupäevade joondamine** (lünk korreleerub SPX-iga täpselt
lag=1 juures, r=+0,587, p=1e-271).

**Kukkus läbi kahel viisil:**

1. **Regiim, mitte seadus** (`run_jp225_why`): korrelatsioon ISE muutus —
   2018–2021 r=−0,002 (seost ei ole), 2024–2026 r=+0,226. Volatiilsus ei
   seleta. Esimene pool tervikuna ei läbi Bonferronit.

2. **Ei mahu kontosse** (`check_jp225`, jooksutatud VPS-il):
   BlackBull JPN225 `trade_contract_size=100`, `volume_min=0.1` ⇒
   notsionaal **3 622€** ⇒ **17,7x võimendus** 205€ kontol.
   Tüüpiline päev = 16,7% kontost. Vajalik konto ~2 270€.

   *Hea uudis sealt:* päris spread on **0,93bp**, mitte eeldatud 3,0bp —
   strateegia on kuludelt **parem** kui modelleeritud (Sharpe +1,11 → +1,41).

**Laiemat perekonda ei ole** (`run_intraday_scan`, `run_scan_null`):
220 paari, 3 läbijat — aga müra annab sama palju (p=0,10).

---

## 5. Vead, mis leiti ja parandati

### Live-koodis

| Viga | Kus | Parandus |
|---|---|---|
| `sync_mt5_positions` kontrollis sulgemist magic-filtreeritud hulga vastu | `main_v4.py` | Kasutab `get_all_positions()`. Tekitas live'is 13 duplikaatrida ja 13 Telegrami hoiatust |
| Spekulatiivne sulgemistuvastus baari high/low järgi — `if TP … elif SL` eeldas mõlema tabamisel **võitu**, P&L teoreetiline, kirjutas `executed=True` enne sync'i | `run_portfolio_leg`, `run_gold_core_overlay` | Eemaldatud. Sulgemisi haldab ainult sync, päris P&L brokerilt |
| **Märgiviga:** `max_float × (balance/account_balance)` — negatiivse balance'i juures pöördus võrdlus ümber ja sulgeks **kõik** positsioonid, ka kasumis | `get_scaled_max_float`, `backtest.py` | `max(balance, 0.0)` |
| Surnud config-nupud: `tp_min`/`tp_max`/`sl_max` ei mõjutanud gridi (TP/SL koodis sees) | `main_v4.py`, `backtest.py` | `grid_tp_usd`/`grid_sl_usd`, vaikeväärtused samad |

### Minu enda analüüsis (kolm korda eksisin)

1. **TP/SL monkey-patch** asendas ainult ostupoole (muster
   `price - 30.0 if direction` ei esine originaalis) → 14 numbrit mõttetud
2. **Plato-kontroll** luges ellujäänute *arvu*, mitte kas nad on *kõrvuti*
   → andis vale "võib olla plato"
3. **"Nõrgem serv"** modelleeriti kui `TR × 0,5`, mis vähendab ka kõikumist
   → see on väiksem positsioon, mitte nõrgem serv

---

## 6. Metoodika — mida iga leiu juures kontrollida

Need testid tapsid enamiku kandidaatidest:

1. **Poolte-test** — mõlemad pooled positiivsed?
2. **Parameetri-plato** — kas naabrid töötavad, või on üksik tipp?
   (Loe **kõrvuti** ellujäänuid, mitte nende arvu.)
3. **Null-jaotus** — mitu "läbijat" annab müra samas sõelas?
4. **Bonferroni** — mitu testi tegelikult tehti?
5. **Andmete terviklikkus** — kas Open on päris? (UK100: 93,4% lünkadest
   täpselt null. FX: Open==Close, aga High/Low on korras)
6. **Baari lahutus** — päevabaaril **ei tohi** testida päevasiseseid TP/SL
   tasemeid. Kuld: päevabaaril +4,76, H1-l −1,48
7. **Kulupiir enne strateegiat** — kas liikumine on spread'ist suurem?
8. **Kas konto elab üle?** — simulaator kaupleb miinuses kontoga edasi.
   Kõik pärast surma on väljamõeldis
9. **Miinimum-lot** — kas positsioon üldse mahub kontosse?

---

## 7. Prop-firma — kas praegune strateegia läbiks?

Testitud `run_prop_xauusd.py`. Strateegia R-ühikutes: **+0,525R** keskmiselt,
50,8% võite, fikseeritud 2:1, **8,8 tehingut aastas**.

**Ajalimiidiga (180 päeva) EI LÄBI:** 0,0% 0,5–1% riski juures. Põhjus:
~4 tehingut 180 päeva jooksul, neljast ei saa +10%.

**Ilma ajalimiidita LÄBIB:**

| Risk/tehing | Läbib 1. sammu | Lõhub | Mediaan aeg | Oodatav %/a |
|---|---|---|---|---|
| 1,0% | 94,5% | 0,4% | 622 p | 4,6% |
| **2,0%** | **94,7%** | 4,9% | **249 p** | 9,3% |
| 3,0% | 87,9% | 12,1% | 166 p | 13,9% |

2% riskiga läbi mõlema sammu: **90,7%, ~332 päeva.**
Rahastatud $25 000: 9,3%/a → kaupleja 85% osa = **$164/kuus**.

Miinimum-loti probleem kaob: 205€ kontol on üks positsioon 68% riski,
$25 000 kontol **0,56%**.

### ⚠️ Kaks asja, mis tapaksid katse

**1. Boti limiidid on prop-firma omadest laiemad**
```
bot        : -10% PÄEVAS, -15% nädalas
prop-firma :  -5% päevas, -10% KOKKU
```
Bot rikuks reegli enne, kui tema enda kaitse käivituks. Vaja muuta
päevalimiit → −4%, kogulimiit → −8%. **Veel tegemata.**

**2. Tegevusetuse reegel (kriitilisem)**
```
keskmine vahe tehingute vahel : 36 päeva
mediaan                       : 20 päeva
PIKIM VAHE                    : 144 päeva

vahesid üle 30 päeva: 26 / 58 = 45%
```
Paljudel firmadel suletakse konto 30-päevase tegevusetuse järel.
Selle strateegiaga juhtuks see **45% pausidest**.

**Nõuded firmale (kõik peavad täituma):**
1. **Ajalimiiti ei tohi olla**
2. **Tegevusetuse reegel puudub või ≥150 päeva**
3. EA/bot lubatud
4. XAUUSD lubatud

---

## 8. Mis on veel testimata

- **FX päevasisesed andmed** Supabase `load_yahoo_bars()` kaudu. FX
  mikro-lott (0,01 = ~860€) on ainus asi, mida 205€ kontol õiges suuruses
  kaubelda saab. Praegused FX päevabaarid on Open'i poolest katki.
- Masinõpe walk-forward valideerimisega.

**Ootus on madal.** Parim, mis sealt tulla saab, on teine ~20%/a strateegia —
ja see on 205€ kontol 41€ aastas.
