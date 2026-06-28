import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime


# ==========================
# Supabase Verbindung
# ==========================

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(URL, KEY)


# ==========================
# Einstellungen
# ==========================

SPIELER = ["Marlon", "Vossi", "Paul", "Jonas"]

PLATZPREIS = 19
FAKTOR = 200 / 250


# ==========================
# Karte holen (SAFE)
# ==========================

def get_karte():
    result = (
        supabase
        .table("karte")
        .select("*")
        .eq("aktiv", True)
        .execute()
    )

    data = result.data

    if not data:
        return None

    return data[0]


# ==========================
# Spiel speichern
# ==========================

def speichern(spieler, einheiten):

    kosten = einheiten * PLATZPREIS * FAKTOR
    pro_person = kosten / len(spieler)

    for person in spieler:
        supabase.table("spiele").insert({
            "spieler": person,
            "einheiten": einheiten,
            "kosten": pro_person
        }).execute()

    # Karte holen (SAFE)
    karte = get_karte()

    if karte is None:
        st.error("Keine aktive Karte vorhanden")
        return

    neues_guthaben = karte["guthaben"] - kosten

    supabase.table("karte").update({
        "guthaben": max(neues_guthaben, 0)
    }).eq("id", karte["id"]).execute()

    if neues_guthaben <= 0:
        abrechnung()


# ==========================
# Abrechnung
# ==========================

def abrechnung():

    daten = supabase.table("spiele").select("*").execute().data or []

    if not daten:
        return

    df = pd.DataFrame(daten)

    gruppiert = df.groupby("spieler")["kosten"].sum()

    for name, betrag in gruppiert.items():
        supabase.table("abrechnung").insert({
            "spieler": name,
            "betrag": float(betrag)
        }).execute()

    supabase.table("karte").update({
        "aktiv": False
    }).eq("aktiv", True).execute()


# ==========================
# UI
# ==========================

st.title("🏸 Squash Abrechnung")

st.subheader("Spieler auswählen")

auswahl = []

for p in SPIELER:
    if st.checkbox(p):
        auswahl.append(p)


einheiten = st.number_input(
    "Einheiten (45 Minuten)",
    min_value=1,
    max_value=20,
    value=1
)


if st.button("Spiel speichern"):
    if len(auswahl) == 0:
        st.warning("Bitte Spieler auswählen")
    else:
        speichern(auswahl, einheiten)
        st.success("Gespeichert")


# ==========================
# Anzeige
# ==========================

st.divider()
st.subheader("Aktueller Stand")

spiele = supabase.table("spiele").select("*").execute().data or []

df = pd.DataFrame(spiele)

if not df.empty:
    st.dataframe(df)
else:
    st.info("Noch keine Spiele vorhanden")


karte = get_karte()

if karte:
    st.metric("Kartenguthaben", f"{karte['guthaben']:.2f} €")
else:
    st.error("Keine aktive Karte vorhanden")


if st.button("Neue Karte starten"):
    supabase.table("karte").insert({
        "guthaben": 250,
        "aktiv": True
    }).execute()

    st.success("Neue Karte gestartet")
