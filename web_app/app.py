import streamlit as st
from core.Portale import Portale
from core.Medical import Medical
from core.GestoreDB import GestoreDB
from grafica.GestoreUI import GestoreUI
import os
#from core.costanti import CHECK_CF, CHECK_EMAIL, CHECK_PASSWORD, CHIAVE, RESET_TIMER



# Grafica: carimento del file css
st.set_page_config(page_title="Medical", layout="centered")

GestoreUI.carica_css()

if 'db' not in st.session_state:
    st.session_state.db = GestoreDB()

if not st.session_state.get('utente_loggato', False):
    portale = Portale() 
    portale.db = st.session_state.db 
    portale.homepage()
else:
    area_medica = Medical(st.session_state.db)
    area_medica.homepage()