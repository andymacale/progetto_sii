from core.GestoreDB import GestoreDB
from dominio.Credenziali import Credenziali
from dominio.Medico import Medico
import streamlit as st
from datetime import date
import time
import re
from email_validator import validate_email, EmailNotValidError
import bcrypt
import codicefiscale


CHECK_EMAIL = r"^[a-z0-9_.+-]+@[a-z0-9-]+\.[a-z0-9.-]+$"
CHECK_CF = r"^[A-Z]{6}[0-9]{2}[A-Z][0-9]{2}[A-Z][0-9]{3}[A-Z]$"
CHIAVE = 'utf-8'

def forza_maiuscolo():
    if "reg_cf" in st.session_state:
        st.session_state.reg_cf = st.session_state.reg_cf.upper()

def forza_minuscolo():
    if "reg_email" in st.session_state:
        st.session_state.reg_email = st.session_state.reg_email.lower()

def forza_minuscolo_login():
    if "login_email" in st.session_state:
        st.session_state.login_email = st.session_state.login_email.lower()

class Portale:

    def __init__(self):
        self.db = GestoreDB()

    def homepage(self):
        st.title("Medical - Portale di accesso")
        tab_login, tab_registrazione = st.tabs(["Accedi", "Registrati"])

        with tab_login:
            self._login()

        with tab_registrazione:
            self._register()

    def _login(self):
        """Login"""
        st.subheader("Accesso")
        email = st.text_input("Email", key="login_email", on_change=forza_minuscolo_login)
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Accedi", type="primary"):
            if not re.fullmatch(CHECK_EMAIL, email):
                st.error("Formato email non valido!")
            else:
                utente = self.db.verifica_login(email, password)
                if utente:
                    st.success(f"Bentornato {utente['nome']} {utente['cognome']}")
                    st.session_state.utente_loggato = True
                    st.session_state.dati_utente = utente
                    st.rerun()
                else:
                    st.error("Email o password errati!")

    def _register(self):
        """Registrazione"""
        nome = st.text_input("Nome")
        cognome = st.text_input("Cognome")
        codice_fiscale = st.text_input("Codice fiscale", key="reg_cf", on_change=forza_maiuscolo)
        data_di_nascita = st.date_input("Data di nascita", min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
        email = st.text_input("Email", key="reg_email", on_change=forza_maiuscolo)
        password = st.text_input("Password", type="password", key="reg_pass")
        conferma_password = st.text_input("Conferma Password", type="password", key="reg_pass_conf")
        if st.button("Registrati", type="primary", use_container_width=True):
            if not nome or not cognome or not codice_fiscale or not data_di_nascita or not email or not password:
                st.error("Tutti i campi sono obbligatori!")
                return
            if password != conferma_password:
                st.error("Le due password devono coincidere!")
                return
            if not re.fullmatch(CHECK_CF, codice_fiscale):
                st.error("Codice fiscale non valido (XXXXXX00X00X000X)!")
                return
            if not re.fullmatch(CHECK_EMAIL, email):
                st.error("Formato email non valido!")
                return
            if not codicefiscale.isvalid(codice_fiscale):
                st.error("Codice fiscale non valido: l'ultima lettera non corrisponde!")
                return
            try:
                info = validate_email(email, check_deliverability=True)
                email_validata = info.normalized
            except EmailNotValidError as e:
                st.error("Dominio email inesistente")
            
            password_bytes = password.encode(CHIAVE)
            sale = bcrypt.gensalt()
            password_criptata = bcrypt.hashpw(password_bytes, sale).decode(CHIAVE)
            credenziali_nuove = Credenziali(email=email_validata, password=password_criptata)
            medico_nuovo = Medico(nome=nome,
                                  cognome=cognome,
                                  codice_fiscale=codice_fiscale, 
                                  data_di_nascita=data_di_nascita,
                                  credenziali=credenziali_nuove)
            if self.db.inserisci_medico(medico_nuovo):
                st.success("Registrazione avvenuta con successo")
            else:
                st.error("Errore durante la registrazione")