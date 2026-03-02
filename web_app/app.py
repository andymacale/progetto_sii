import streamlit as st
from core.Portale import Portale
from core.Medical import Medical
from core.GestoreDB import GestoreDB
from grafica.GestoreUI import GestoreUI
from streamlit_local_storage import LocalStorage
import os
import datetime
#from core.costanti import CHECK_CF, CHECK_EMAIL, CHECK_PASSWORD, CHIAVE, RESET_TIMER



# Grafica: carimento del file css
st.set_page_config(page_title="Medical", layout="centered")

GestoreUI.carica_css()

if 'db' not in st.session_state:
    st.session_state.db = GestoreDB()

local_storage = LocalStorage()

if not st.session_state.get('utente_loggato', False):
    token_salvato = local_storage.getItem("auth_token")
    if token_salvato:
        dati_sessione = st.session_state.db.verifica_token_sessione(token_salvato)
        if dati_sessione:
            scadenza = dati_sessione['scadenza']
            medico = dati_sessione['medico']
            if datetime.now() < scadenza:
                st.session_state.utente_loggato = True
                st.session_state.dati_utente = medico
                st.rerun()
            else:
                st.session_state.db.elimina_token_sessione(medico.credenziali.email)
                local_storage.deleteAll()

if not st.session_state.get('utente_loggato', False):
    portale = Portale() 
    portale.db = st.session_state.db 
    portale.homepage()
else:
    area_medica = Medical(st.session_state.db)
    area_medica.homepage()
