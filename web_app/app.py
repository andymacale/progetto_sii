import streamlit as st
from core.Portale import Portale
from core.Medical import Medical

st.set_page_config(page_title="Medical", layout="centered")

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