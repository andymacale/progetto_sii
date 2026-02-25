import streamlit as st
from core.Portale import Portale
from core.Medical import Medical
import os


# Grafica: carimento del file css
def load_css(nome_file):
    cartella_attuale = os.path.dirname(__file__)
    path = os.path.join(cartella_attuale, nome_file)
    try:
        with open(path) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"File css non trovato: {path}")


st.set_page_config(page_title="Medical", layout="centered")

load_css("stile.css")

# Inizializzi la sessione per il login
if "utente_loggato" not in st.session_state:
    st.session_state.utente_loggato = False

if "dati_utente" not in st.session_state:
    st.session_state.dati_utente = None

# Routing principale: Portale o Medical?
if not st.session_state.utente_loggato:
    # Utente non loggato
    portale = Portale()
    portale.homepage()
else:
    # Utente loggato
    medical = Medical()
    medical.homepage()