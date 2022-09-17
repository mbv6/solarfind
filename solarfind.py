from email import header
from email.headerregistry import Address
from pyexpat import features
import pandas as pd
import plotly_express as px
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import altair as alt
import seaborn as sns
sns.set()

# ----Web App----
st.set_page_config(page_title="SolarFind",
page_icon=":high_brightness:",
layout="wide")

#----Containers----
header = st.container()
dataset = st.container()
features = st.container()
auswertung = st.container()
dashboard = st.container()
ende = st.container()

with header:
    st.title('Willkommen bei unserem TechLabs Projekt - SolarFind!')

with dataset:
    st.header('Solarkataster Münster Datenset')
    st.text('Hier ist ein Ausschnitt des originalen Datensets zusehen.')
    st.text('Es ist auf der Website "opendata.stadt-muenster.de" zu finden.')
    original_ds = pd.read_excel("resources/data_slim_2000.xlsx")
    st.write(original_ds.head())

#Link zum Datenset: https://opendata.stadt-muenster.de/dataset/solarkataster-m%C3%BCnster-solarpotenzial


#----Datengrundlage bereinigen----
# Spalten aussortieren, die nicht relevant sind
df = original_ds.drop(['Slope', 'RoofType', 'Eignung_T', 'PvAreaT', 'Aspect', 'Schatten', 'SchattenA', 'SchattenT', 'PercentMs', 'PercentMsA'], axis =1)

#Spalte Eignung auf <= 3 eingrenzen und bearbeitetes ds in df umbennen
df = df.loc[df['Eignung']<= 3]
df = df.loc[df['Eignung']>0]

#Spalte Eignung_G auf <= 5 eingrenzen
df = df.loc[df['Eignung_G']<= 5]
df = df.loc[df['Eignung_G']>0]

#Spalte Adresse spliten
angepasstes_df = df["Address"].str.split(",", n=1, expand = True)
df["Straße_Hausnummer"] = angepasstes_df[0]
df["PLZ_und_Ort"] = angepasstes_df[1]
df.drop(columns = ['Address'], inplace = True)

#Spalte PLZ_und_Ort spliten
neues_df = df["PLZ_und_Ort"].str.split(" ", n=2, expand =True)
df["PLZ"] = neues_df[1]
df["Ort"] = neues_df[2]
df.drop(columns = ['PLZ_und_Ort'], inplace = True)

#Spalte Adresse NaN Daten entfernen
#exceldaten = exceldaten[exceldaten.notna()]
df.dropna(subset=['Straße_Hausnummer'], inplace= True)

#Reihenfolge Spalten bestimmen
Spaltennamen = ['BuildingID', 'RoofID', 'Straße_Hausnummer', 'PLZ', 'Ort', 'Eignung','Eignung_G', 'Aufstd', 'Area', 'PvArea', 'GreenArea', 'ErtKwP_K', 'ErtKwP_KA', 'ErtKwhaK', 'ErtKwhaKA', 'Power']
df = df.reindex(columns = Spaltennamen)


#Berechnung Gesamtleistung in kwH je Jahr; Entscheidung für Aufständerung bei Ertragssteigerung
def gesamtleistung(s):
    if s['ErtKwhaK'] >= s['ErtKwhaKA']:
        return s['ErtKwhaK']
    else:
        return s['ErtKwhaKA']

#Anwendung Berechnung Gesamtleistung zur Erstellung entsprechender Spalte Total Power
df['Total Power (kwH)'] = df.apply(gesamtleistung, axis=1)

#externe Liste - Anlagenleitung und Bruttopreis
#Anlagenleistung = [4, 6, 8, 10, 12, 14, 16, 18, 20]
#Bruttopreis = [1900, 1740, 1630, 1550, 1440, 1400, 1360, 1320, 1300]

#Kosten berechnen
#Bedingung zur Berechnung des richtigen Bruttopreises 
def bruttopreis(s):
    if (s['Power'] <= 4):
        return 1900 * s['Power']
    elif (s['Power'] > 4) and (s['Power'] <= 6):
        return 1740*s['Power']
    elif (s['Power'] > 6) and (s['Power'] <= 8):
        return 1630*s['Power']
    elif (s['Power'] > 8) and (s['Power'] <= 10):
        return 1550*s['Power']
    elif (s['Power'] > 10) and (s['Power'] <= 12):
        return 1440*s['Power']
    elif (s['Power'] > 12) and (s['Power'] <= 14):
        return 1400*s['Power']
    elif (s['Power'] > 14) and (s['Power'] <= 16):
        return 1360 * s['Power']
    elif (s['Power'] > 16) and (s['Power'] <= 18):
        return 1320*s['Power']
    else:
        return 1300 * s['Power']
#Erstellung entsprechender Spalte - Bruttopreis  
df['Bruttopreis_EUR'] = df.apply(bruttopreis, axis=1)

#neue Reihenfolge der Spalten bestimmen
Spaltennamen = ['BuildingID', 'RoofID', 'Straße_Hausnummer', 'PLZ', 'Ort', 'Eignung', 'Eignung_G', 'Aufstd', 'Area', 'PvArea', 'ErtKwP_K', 'ErtKwP_KA', 'ErtKwhaK', 'ErtKwhaKA', 'Total Power (kwH)', 'Power', 'Bruttopreis_EUR']
df = df.reindex(columns = Spaltennamen)

#Definiert Berechnung Ertrag für Haushalte wo Potential über durchschnittlichen Verbrauch von 5000 kwH liegt
def ertrag(s):
    if (s['Total Power (kwH)'] >= 5000):
        return ((s['Total Power (kwH)'] - 5000) * 8.2) / 100
    else:
        return 0

# Wendet Berechnung Ertrag an, um neue Spalte mit diesen informationen zu erstellen
df['Ertrag (EUR)'] = df.apply(ertrag, axis=1)


#Spalte Eignung auf <= 3 eingrenzen
#sortiertes_df = sortiertes_df.loc[sortiertes_df['Ertrag (EUR)']> 0]

#Definiert Rechenweg erwarteter Einsparung durch Wegfall Zukauf Strom 
#(Annahme Strompreis 9.5 cent 2030 bei Kohleausstieg und 65% EE)
def einsparung(s):
    if (s['Total Power (kwH)'] >=5000):
        return (5000*(9.5)/100)
    else:
        return 0
    
#Anwendung Berechnung Einsparung
df['Einsparung (EUR)'] = df.apply(einsparung, axis=1)


#Berechnung Amortisationszeitraum
def amortisationszeitraum(s):
    if (s['Total Power (kwH)'] >=5000):
        return s['Bruttopreis_EUR']/(s['Ertrag (EUR)']+s['Einsparung (EUR)'])
    else:
        return 0
         #x heißt individuelle Prüfung nötig, da ds.Vebrauch höher ist als erzeugbare Power

    
df['Amortisationszeitraum (Jahre)'] = df.apply(amortisationszeitraum, axis=1)

avg_amort = sum(df['Amortisationszeitraum (Jahre)']) / len(df['Amortisationszeitraum (Jahre)'])

with features:
    st.header('Anpassungen und Berechnungen')
    st.text('Hier ist ein Ausschnitt des angepassten Datensets zusehen.')
    st.text('Es wurden irrelevante oder falsche Daten entfernt und Werte wie Bruttopreis, Ersparnis, Ertrag etc. berechnet.')
    st.write(df.head())

with auswertung:
    st.header('Hier ein Überblick über die Daten')

    st.subheader('Eignung der Dächer für PV')
    eignung_dist = pd.DataFrame(df['Eignung'].value_counts())
    st.bar_chart(eignung_dist)
    st.text('1 = sehr gut; 2 = gut; 3 = ausreichend')

    st.subheader('Eignung der Dächer für Grünflächen')
    eignung_g_dist = pd.DataFrame(df['Eignung_G'].value_counts())
    st.bar_chart(eignung_g_dist)
    st.text('1 = sehr gut; 2 = gut; 3 = ausreichend; 4 = muss individuell geprüft werden')

    st.subheader('Durchschnittliche Armortisationsdauer:')
    st.write(avg_amort)



with dashboard:
    st.header('Schaue nach, ob dein Haus für eine PV geeignet ist!')

    sel_col, disp_col = st.columns(2)


    #plz_sel = sel_col.selectbox('PLZ auswählen:',  options = df['PLZ'].unique())
    adresse_sel = sel_col.selectbox('Adresse auswählen:',  options = df['Straße_Hausnummer'].unique())
    #roof_sel = sel_col.selectbox('Dachseite auswählen:',  options = df['RoofID'].unique())
    
    df_selection = df.query(
        "Straße_Hausnummer == @adresse_sel"
    )

    st.dataframe(df_selection)



with ende:
    st.text(' ')
    st.text(' ')
    st.text(' ')
    st.text(' ')
    st.text(' ')
    st.text(' ')
    st.text('Dieses Projekt wurde erstellt von Matthias Schulze Tilling, Kim Forst & Michelle Buston Vega')


#----deploy the app----



#----Auswahlbereich----
#st.sidebar.header("Hier filtern:")

#Straße_Hausnummer = st.sidebar.multiselect(
 #   "Straße auswählen:",
  #  options=df["Straße_Hausnummer"].unique() #,
    #default=df["Straße_Hausnummer"].unique() #alle PLZ werden aufgelistet (Komma vorher nicht vergessen!)
#)

#PLZ = st.sidebar.multiselect(
 #   "PLZ auswählen:",
  #  options=df["PLZ"].unique() ,
   # default=df["PLZ"].unique() #alle PLZ werden aufgelistet (Komma vorher nicht vergessen!)
#)

#VERKNÜPFUNG VON AUSWAHLBEREICH ZU DATEN FUNKTIONIERT NICHT
#df_selection = df.query(
 #  "Straße_Hausnummer == @Straße_Hausnummer & PLZ == @PLZ"
#)

#st.dataframe(df)
#st.dataframe(df_selection)

#df als CSV Datei exportieren .. liegt im Solarfind Ordner
#df.to_csv (r'C:\Users\Michelle\Schreibtisch\export_dataframe.csv', index = False, header=True)

#df
