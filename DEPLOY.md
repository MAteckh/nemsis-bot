# NEMSIS v2 — Cloud Deploy Guide

## Ülevaade
- **Supabase** — andmebaas ✅ (juba loodud)
- **Railway** — bot jookseb 24/7 pilves
- **Vercel** — dashboard mobiilil/brauseris

---

## SAMM 1 — Supabase tabelid (5 min)

1. Mine: https://supabase.com/dashboard/project/xqinzjaqorjqaexeoyqc
2. Vasakul menüüs: **SQL Editor** → **New query**
3. Kopeeri kogu `supabase/schema.sql` sisu sinna
4. Vajuta **Run** (▶)
5. Peaksid nägema "Success" — tabelid on loodud ✅

---

## SAMM 2 — GitHub repo (5 min)

1. Mine github.com → **New repository**
2. Nimi: `nemsis-bot`
3. Private ✅
4. **Create repository**
5. Terminalis:
```bash
cd C:\Users\angel\Desktop
# Kopeeri bot kaust GitHubi
git init nemsis-bot
cd nemsis-bot
# Kopeeri bot/main.py, bot/requirements.txt, bot/railway.toml siia
git add .
git commit -m "NEMSIS v2 cloud bot"
git remote add origin https://github.com/SINU_KASUTAJANIMI/nemsis-bot.git
git push -u origin main
```

---

## SAMM 3 — Railway (bot, 10 min)

1. Mine railway.app → **Login with GitHub**
2. **New Project** → **Deploy from GitHub repo**
3. Vali `nemsis-bot` repo
4. Railway tuvastab automaatselt Python
5. **Variables** tab — lisa need:
   ```
   SUPABASE_URL  = https://xqinzjaqorjqaexeoyqc.supabase.co
   SUPABASE_KEY  = sb_secret_geYNl5euHLVWXQtone_N0g_K5nB0Zel
   TELEGRAM_TOKEN = 7502951774:AAFEdMlowZumpFlLm817UEP4ws40SeZtROo
   TELEGRAM_CHAT_ID = 7638697143
   SCAN_INTERVAL = 300
   ACCOUNT_BALANCE = 10000
   ```
6. **Deploy** — bot käivitub automaatselt ✅

---

## SAMM 4 — Vercel (dashboard, 5 min)

1. Mine vercel.com → **Login with GitHub**
2. **New Project** → **Import Git Repository**
   - Või lihtsam: **Add New** → **Project** → lohista `dashboard` kaust
3. Framework: **Other**
4. Root directory: `dashboard`
5. **Deploy** ✅
6. Saad URL nagu: `nemsis-v2.vercel.app`

**See on sinu mobiili URL!** Lisa see telefoni avakuvale:
- iPhone: Safari → Jaga → "Lisa avakuvale"
- Android: Chrome → ⋮ → "Lisa avakuvale"

---

## Tulemus

| Komponent | Status | URL |
|---|---|---|
| Andmebaas | Supabase (Frankfurt) | — |
| Bot 24/7 | Railway | — |
| Dashboard | Vercel | `nemsis-v2.vercel.app` |

Bot skaneerib iga 5 minuti järel, suunab andmed Supabase'i,
dashboard loeb Supabase'ist reaalajas.

**Arvuti võib kinni olla!** 🎉
