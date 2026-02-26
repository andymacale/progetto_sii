import streamlit as st
from core.Portale import Portale
from core.Medical import Medical
from core.GestoreDB import GestoreDB
import os
from core.costanti import CHECK_CF, CHECK_EMAIL, CHECK_PASSWORD, CHIAVE, CHECK_ETA



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

if 'db' not in st.session_state:
    st.session_state.db = GestoreDB()

if not st.session_state.get('utente_loggato', False):
    portale = Portale() 
    portale.db = st.session_state.db 
    portale.homepage()
else:
    area_medica = Medical(st.session_state.db)
    area_medica.homepage()