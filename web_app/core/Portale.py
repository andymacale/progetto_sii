from core.GestoreDB import GestoreDB
from dominio.Credenziali import Credenziali
from dominio.Medico import Medico
import streamlit as st
import datetime

class Portale:

    def __init__(self):
        self.db = GestoreDB()

    def homepage(self):
        st.title("Medical - Portale di accesso")
        tab_login, tab_registrazione = st.tabs(["Accedi", "Registrati"])

        with tab_login:
            self._login()

        #with tab_registrazione:
            #self._register()

    def _login(self):
        st.subheader("Accesso")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Accedi", type="primary"):
            utente = self.db.verifica_login(email, password)
            if utente:
                st.success(f"Bentornato {utente['nome']} {utente['cognome']}")
                st.session_state.utente_loggato = True
                st.session_state.dati_utente = utente
                st.rerun()
            else:
                st.error("Email o password errati!")
