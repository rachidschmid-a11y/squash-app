import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime


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
# Kartenstand
# ==========================


def get_karte():


    result = (
        supabase
        .table("karte")
        .select("*")
        .eq("aktiv",True)
        .execute()
    )


    return result.data[0]




# ==========================
# Spiel speichern
# ==========================


def speichern(
    spieler,
    einheiten
):


    kosten = (
        einheiten *
        PLATZPREIS *
        FAKTOR
    )


    pro_person = (
        kosten /
        len(spieler)
    )



    for person in spieler:


        supabase.table(
            "spiele"
        ).insert(

        {

        "spieler":person,

        "einheiten":einheiten,

        "kosten":pro_person

        }

        ).execute()



    # Guthaben reduzieren


    karte=get_karte()


    neues_guthaben = (

        karte["guthaben"]

        -

        kosten

    )



    supabase.table(
        "karte"
    ).update(

    {

    "guthaben":
    neues_guthaben

    }

    ).eq(

    "id",
    karte["id"]

    ).execute()



    if neues_guthaben <=0:

        abrechnung()



# ==========================
# Abrechnung
# ==========================


def abrechnung():


    daten=(

    supabase
    .table("spiele")
    .select("*")
    .execute()

    ).data



    df=pd.DataFrame(daten)



    gruppiert=(

    df.groupby(
        "spieler"
    )["kosten"]

    .sum()

    )



    for name,betrag in gruppiert.items():

        supabase.table(
        "abrechnung"
        ).insert(

        {

        "spieler":name,

        "betrag":float(betrag)

        }

        ).execute()



    supabase.table(
    "karte"
    ).update(

    {
    "aktiv":False
    }

    ).eq(
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


auswahl=[]


for p in SPIELER:


    if st.checkbox(p):

        auswahl.append(p)



einheiten=st.number_input(

"Einheiten (45 Minuten)",

1,

20,

1

)




if st.button(
"Spiel speichern"
):


    if len(auswahl)>0:


        speichern(

        auswahl,

        einheiten

        )


        st.success(
        "Gespeichert"
        )



# ==========================
# Anzeige
# ==========================


st.divider()


st.subheader(
"Aktueller Stand"
)


spiele=(

supabase
.table("spiele")
.select("*")
.execute()

).data



df=pd.DataFrame(spiele)



if len(df)>0:


    st.dataframe(df)



karte=get_karte()



st.metric(

"Kartenguthaben",

f"{karte['guthaben']:.2f} €"

)



# Neue Karte


if st.button(
"Neue Karte starten"
):


    supabase.table(
    "karte"
    ).insert(

    {

    "guthaben":250,

    "aktiv":True

    }

    ).execute()


    st.success(
    "Neue Karte gestartet"
    )
