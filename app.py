# Version 4.0

import streamlit as st
import pandas as pd
from supabase import create_client


# ==========================
# Supabase Verbindung
# ==========================

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(
    URL,
    KEY
)


# ==========================
# Einstellungen
# ==========================

SPIELER = [
    "Marlon",
    "Vossi",
    "Paul",
    "Jonas"
]

PLATZPREIS = 19
FAKTOR = 200 / 250


# ==========================
# Fehleranzeige
# ==========================

def db_error(e):

    st.error("Datenbank Fehler:")
    st.write(e)



# ==========================
# Aktive Karte holen
# ==========================

def get_karte():

    try:

        result = (
            supabase
            .table("public.karte")
            .select("*")
            .eq("aktiv", True)
            .execute()
        )


        if not result.data:

            return None


        return result.data[0]


    except Exception as e:

        db_error(e)

        return None



# ==========================
# Spiele laden
# ==========================

def get_spiele():

    try:

        result = (
            supabase
            .table("public.spiele")
            .select("*")
            .execute()
        )


        return result.data or []


    except Exception as e:

        db_error(e)

        return []



# ==========================
# Spiel speichern
# ==========================

def speichern(spieler, einheiten):


    karte = get_karte()


    if karte is None:

        st.error(
            "Keine aktive Karte vorhanden"
        )

        return



    gesamtkosten = (
        einheiten *
        PLATZPREIS *
        FAKTOR
    )


    kosten_pro_person = (
        gesamtkosten /
        len(spieler)
    )



    for person in spieler:


        supabase.table(
            "public.spiele"
        ).insert({

            "spieler": person,

            "einheiten": einheiten,

            "kosten": kosten_pro_person

        }).execute()



    neues_guthaben = (
        karte["guthaben"]
        -
        gesamtkosten
    )



    supabase.table(
        "public.karte"
    ).update({

        "guthaben": max(neues_guthaben, 0)

    }).eq(

        "id",
        karte["id"]

    ).execute()



    if neues_guthaben <= 0:

        abrechnung()



# ==========================
# Abrechnung erstellen
# ==========================

def abrechnung():


    daten = get_spiele()


    if not daten:

        return



    df = pd.DataFrame(daten)



    summen = (
        df
        .groupby("spieler")
        ["kosten"]
        .sum()
    )



    for name, betrag in summen.items():


        supabase.table(
            "public.abrechnung"
        ).insert({

            "spieler": name,

            "betrag": float(betrag)

        }).execute()



    supabase.table(
        "public.karte"
    ).update({

        "aktiv": False

    }).eq(

        "aktiv",
        True

    ).execute()



# ==========================
# Oberfläche
# ==========================

st.title(
    "🏸 Squash Abrechnung"
)


st.subheader(
    "Spieler auswählen"
)



auswahl = []


for spieler in SPIELER:


    if st.checkbox(spieler):

        auswahl.append(spieler)



einheiten = st.number_input(

    "Einheiten (45 Minuten)",

    min_value=1,

    max_value=20,

    value=1

)



if st.button(
    "Spiel speichern"
):


    if len(auswahl) == 0:


        st.warning(
            "Bitte mindestens einen Spieler auswählen"
        )


    else:


        speichern(
            auswahl,
            einheiten
        )


        st.success(
            "Spiel gespeichert"
        )



# ==========================
# Anzeige
# ==========================

st.divider()


st.subheader(
    "Aktueller Stand"
)



spiele = get_spiele()



if spiele:


    df = pd.DataFrame(spiele)


    st.dataframe(
        df,
        use_container_width=True
    )


else:


    st.info(
        "Noch keine Spiele vorhanden"
    )



# ==========================
# Kartenguthaben
# ==========================

karte = get_karte()



if karte:


    st.metric(

        "Kartenguthaben",

        f"{karte['guthaben']:.2f} €"

    )


else:


    st.warning(
        "Keine aktive Karte vorhanden"
    )



# ==========================
# Neue Karte
# ==========================

if st.button(
    "Neue Karte starten"
):


    supabase.table(
        "public.karte"
    ).insert({

        "guthaben": 250,

        "aktiv": True

    }).execute()



    st.success(
        "Neue Karte gestartet"
    )
