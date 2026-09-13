"""
v5_registry.py — HUPOTEESIREGISTER (Phase 4).

REEGEL: iga huopotees on siin kirjas ENNE testimist. Registrit ei
taiendata tagantjarele selleks, et tulemust ilusamaks teha. Kui test
annab positiivse tulemuse, korrigeeritakse see KOGU REGISTRI suuruse
jargi (Benjamini-Hochberg + Deflated Sharpe), mitte ainult selle uhe
testi jargi.

Iga kirje: ID, kuupaev, pohjendus, features, entry, exit, oodatav efekt.
"""

LOODUD = "2026-09-13"
PERIOOD = "2016-09-12 .. 2026-09-11 (TRAIN kuni 2021-12-31, VALID kuni 2024-12-31, FINAL OOS parast)"

REGISTER = [
 dict(id="H01", nimi="CS-MOM-1D",
   pohjendus="Luhiajaline ristloikeline poordumine on aktsiates dokumenteeritud; "
             "FX-is peaks 1-paevane edetabel poorduma, mitte jatkuma.",
   features="valuutatugevus, 1 paeva kumulatiiv", entry="LONG top-2, SHORT bottom-2, paevane rebalanss",
   exit="jargmine rebalanss", ootus="NEGATIIVNE momentum (ehk poordumine) voi null"),
 dict(id="H02", nimi="CS-MOM-5D",
   pohjendus="Nadalane edetabel — vahepealne horisont, kus ei toimi ei poordumine ega pikk momentum.",
   features="valuutatugevus, 5 paeva", entry="LONG top-2, SHORT bottom-2", exit="jargmine rebalanss",
   ootus="null"),
 dict(id="H03", nimi="CS-MOM-20D",
   pohjendus="Currency momentum on avaldatud JFE-s (Dissecting currency momentum). "
             "1 kuu edetabel on klassikaline formeerimisperiood.",
   features="valuutatugevus, 20 paeva", entry="LONG top-2, SHORT bottom-2", exit="jargmine rebalanss",
   ootus="POSITIIVNE, kui akadeemiline leid uldistub"),
 dict(id="H04", nimi="CS-MOM-60D",
   pohjendus="Kvartaalne formeerimine — momentumi klassikaline 3 kuu aken.",
   features="valuutatugevus, 60 paeva", entry="LONG top-2, SHORT bottom-2", exit="jargmine rebalanss",
   ootus="POSITIIVNE, kui H03 toimib"),
 dict(id="H05", nimi="CS-CARRY",
   pohjendus="Carry on FX-i koige paremini dokumenteeritud anomaalia (Burnside/Eichenbaum/"
             "Rebelo NBER). Korge intressiga valuuta ei devalveeru piisavalt, et vahet katta.",
   features="intressivahe ETF-idest (JARJESTUS, mitte tase)", entry="LONG korgeim carry, SHORT madalaim",
   exit="jargmine rebalanss", ootus="POSITIIVNE, aga suure tail-riskiga"),
 dict(id="H06", nimi="CS-CARRY+MOM",
   pohjendus="Carry ja momentum on ajalooliselt madalalt korreleeritud; kombinatsioon "
             "peaks andma parema riskiga korrigeeritud tulemuse kui kumbki eraldi.",
   features="carry jarjestus + 20d momentum jarjestus, summa", entry="LONG top-2 liitskoor, SHORT bottom-2",
   exit="jargmine rebalanss", ootus="POSITIIVNE, korgem Sharpe kui H03 voi H05 eraldi"),
 dict(id="H07", nimi="TS-MOM-MULTI",
   pohjendus="Time-series momentum (AQR, Moskowitz/Ooi/Pedersen) — iga valuuta OMA "
             "mineviku tootlus, mitte edetabel. Erineb H01-H04-st pohimotteliselt.",
   features="valuutatugevuse kumulatiiv 1/5/20/60/120 paeva, margi haaletus",
   entry="LONG kui enamik horisonte plussis, SHORT kui miinuses", exit="jargmine paev",
   ootus="POSITIIVNE, kui trendijargimine uldistub valuutadele"),
 dict(id="H08", nimi="MOM-ACCEL",
   pohjendus="Momentumi KIIRENDUS (2. tuletis) voib olla informatiivsem kui tase — "
             "poordepunktid tulevad enne taseme muutust.",
   features="20d momentum miinus eelmine 20d momentum", entry="LONG top-2 kiirendus, SHORT bottom-2",
   exit="jargmine rebalanss", ootus="ebaselge"),
 dict(id="H09", nimi="MOM-PERSIST",
   pohjendus="Momentumi PUSIVUS (mitu paeva jarjest samas suunas) voib eristada "
             "paris trendi muraliikumisest.",
   features="positiivsete paevade osakaal 20 paeva aknas", entry="LONG koige pusivam, SHORT koige ebapusivam",
   exit="jargmine rebalanss", ootus="ebaselge"),
 dict(id="H10", nimi="OVERNIGHT",
   pohjendus="Aktsiates on overnight-tootlus suurem kui paevasisene (dokumenteeritud). "
             "FX kaupleb 24h, seega kui sama muster esineb, peab tal olema teine pohjus "
             "(likviidsus, positsioonide sulgemine enne New Yorgi sulgemist).",
   features="close-to-open vs open-to-close", entry="hoia AINULT ules oo voi AINULT paeval",
   exit="vastavalt", ootus="null, kuna FX on 24h turg"),
 dict(id="H11", nimi="WEEKDAY",
   pohjendus="Nadalapaeva efekt vajab majanduslikku pohjust. FX-is on see reedene "
             "positsioonide sulgemine enne nadalavahetuse gap-riski.",
   features="nadalapaev", entry="ainult konkreetsel paeval", exit="paeva lopus",
   ootus="null — ilma pohjuseta on see andmekaevandamine"),
 dict(id="H12", nimi="MONTHEND",
   pohjendus="Kuu lopu rebalanss on PARIS mehhanism: fondid peavad valuutariski "
             "maandama kuu viimastel paevadel (nn London 4pm fix flow).",
   features="kuu viimased 3 paeva / esimesed 3", entry="positsioon nendel paevadel",
   exit="akna lopus", ootus="VOIB olla, mehhanism on olemas"),
 dict(id="H13", nimi="RELVAL-TRI",
   pohjendus="EURUSD, GBPUSD ja EURGBP on kolmnurgas matemaatiliselt seotud. "
             "Ajutine korvalekalle peaks tagasi poorduma — see ei ole ennustus, "
             "vaid arbitraazh, kui see eksisteerib.",
   features="log(EURUSD) - log(GBPUSD) - log(EURGBP) jaak, z-skoor",
   entry="fade korvalekallet", exit="tagasi keskmisele", ootus="null parast kulusid (arbitraaz on kadunud)"),
 dict(id="H14", nimi="RELVAL-AUDNZD",
   pohjendus="AUD ja NZD on tugevalt korreleeritud (sarnased toormemajandused). "
             "Nende SPREAD peaks olema statsionaarsem kui kumbki eraldi.",
   features="log(AUDUSD) - log(NZDUSD) z-skoor 60 paeva", entry="fade korvalekallet",
   exit="z tagasi nulli", ootus="VOIB olla, kui kointegratsioon kehtib"),
]

def kokku():
    return len(REGISTER)

if __name__ == "__main__":
    print(f"HUPOTEESIREGISTER — loodud {LOODUD}")
    print(f"Andmeperiood: {PERIOOD}")
    print(f"Huopoteese: {kokku()}")
    print()
    for h in REGISTER:
        print(f"  {h['id']}  {h['nimi']:16s} ootus: {h['ootus']}")
