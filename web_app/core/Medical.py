import streamlit as st
import re
from datetime import date
import bcrypt
import time
from core.costanti import CHIAVE, CHECK_PASSWORD, CHECK_CF, CHECK_ETA
from grafica.GestoreUI import GestoreUI
import codicefiscale
from dominio.Paziente import Paziente
from dominio.PreferenzaSessione import PreferenzaSessione
import uuid
from datetime import datetime, timedelta
#from streamlit_local_storage import LocalStorage



def forza_maiuscolo_paziente():
    if "cf_paziente" in st.session_state:
        st.session_state.cf_paziente = st.session_state.cf_paziente.upper()

class Medical:
    def __init__(self, db_gestore):
        self.db = db_gestore
        #self.local_storage = LocalStorage()
        if "dati_utente" in st.session_state:
            self.utente_corrente = st.session_state.dati_utente

    def homepage(self):
        cognome = self.utente_corrente.cognome
        email = self.utente_corrente.credenziali.email
        sesso = self.utente_corrente.sesso
        numero_pazienti = self.db.get_numero_pazienti(email)

        if sesso == 'F':
            st.title(f"Bentornata Dott.ssa {cognome}")
        else:
            st.title(f"Bentornato Dott. {cognome}")
        
        st.divider()
        
        col_stat, col1, col2, col3 = st.columns([1, 1, 1, 1])

        with col_stat:
            st.metric("Pazienti in cura", value=numero_pazienti)
        with col1:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Aggiungi paziente", type="secondary", use_container_width=True):
                self._modalita_nuovo_paziente()
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Nuove analisi", type="secondary", use_container_width=True):
                st.session_state['step_analisi'] = True
                st.rerun()
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.popover("Menu Utente", use_container_width=True):
                if sesso == 'F':
                    st.title(f"**Dott.ssa {cognome}**")
                else:
                    st.title(f"**Dott. {cognome}**")
                st.write(f"*{email}*")
                st.divider()
                if st.button("Mantieni l'accesso", use_container_width=True):
                    self._modalita_accesso()
                if st.button("Cambia Password", use_container_width=True):
                    self._modalita_cambia_password() 
                if st.button("Esci", type="primary", use_container_width=True):
                    self.db.elimina_token_sessione(email)
                    st.session_state.clear()
                    st.session_state.comando_elimina_token = True
                    st.rerun()

        st.divider()

    @st.dialog("Mantieni l'accesso")
    def _modalita_accesso(self):
        email = self.utente_corrente.credenziali.email
        codice_db = self.db.get_preferenza_sessione(email)
        
        codice_pulito = "Sempre"
        if codice_db:
            testo = str(codice_db).strip()
            if "Mai" in testo: codice_pulito = "Mai"
            elif "Ora" in testo: codice_pulito = "Ora"
            elif "Giorno" in testo: codice_pulito = "Giorno"
            elif "Settimana" in testo: codice_pulito = "Settimana"

        try:
            pref_attuale = PreferenzaSessione(codice_pulito)
        except ValueError:
            pref_attuale = PreferenzaSessione.SEMPRE

        opzioni = PreferenzaSessione.get_valori_ui()
        scelto = st.selectbox("Richiedi il login:", options=opzioni, index=opzioni.index(pref_attuale.etichetta_ui))
        
        if st.button("Salva preferenza", use_container_width=True):
            enum_scelto = PreferenzaSessione.da_etichetta(scelto)
            self.db.aggiorna_preferenza_sessione(email, enum_scelto.value)
            
            if enum_scelto == PreferenzaSessione.SEMPRE:
                st.session_state.comando_elimina_token = True
            else:
                ora_attuale = datetime.now()
                if enum_scelto == PreferenzaSessione.ORA:
                    scadenza = ora_attuale + timedelta(hours=1)
                elif enum_scelto == PreferenzaSessione.GIORNO:
                    scadenza = ora_attuale + timedelta(days=1)
                elif enum_scelto == PreferenzaSessione.SETTIMANA:
                    scadenza = ora_attuale + timedelta(days=7)
                else: 
                    scadenza = None
                    
                nuovo_token_sicuro = str(uuid.uuid4())
                self.db.salva_token_sessione(email, nuovo_token_sicuro, scadenza)
                st.session_state.comando_salva_token = nuovo_token_sicuro
                
            st.success("Impostazione salvata")
            time.sleep(2)
            st.rerun()
    
    @st.dialog("Cambia Password")
    def _modalita_cambia_password(self):
        vecchia = st.text_input("Vecchia password", type="password")
        nuova = st.text_input("Nuova password", type="password")
        conferma = st.text_input("Conferma password", type="password")

        if st.button("Aggiorna", type="primary", use_container_width=True):
            if not vecchia or not nuova or not conferma:
                st.error("Tutti i campi sono obbligatori!")
                return
            if nuova != conferma:
                st.error("La nuova password e la conferma password devo coincidere!")
                return
            if not re.fullmatch(CHECK_PASSWORD, nuova):
                st.error("La password deve essere di 8-16 caratteri con almeno una maiuscola ed un carattere speciale (@$!%*?&#-_)")
                return
            with GestoreUI.spinner_medico("Cambio password in corso"):
                email = self.utente_corrente.credenziali.email
                if not self.db.verifica_login(email, vecchia):
                    st.error("La vecchia password e' errata!")
                    return
                nuova_bytes = nuova.encode(CHIAVE)
                sale = bcrypt.gensalt()
                nuova_hash = bcrypt.hashpw(nuova_bytes, sale).decode(CHIAVE)
                if self.db.aggiorna_password(email, nuova_hash):
                    st.success("Password aggiornata! Ricarico l'area medica...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Errore durante il salvataggio della nuova password")

    @st.dialog("Aggiungi Paziente")
    def _modalita_nuovo_paziente(self):
        st.title("Inserimento dati paziente")

        nome = st.text_input("Nome").strip()
        cognome = st.text_input("Cognome").strip()

        if not nome or not cognome:
            st.info("Tutti i campi sono obbligatori")
            return
        st.divider()

        etaCorretta = False
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            data_di_nascita = st.date_input("Data di nascita", min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            
        oggi = date.today()
        eta = oggi.year - data_di_nascita.year
        if (oggi.month, oggi.day) < (data_di_nascita.month, data_di_nascita.day):
            eta -= 1
            
        with col2:
            st.info(f"Età: {eta}")
            
        with col3:
            if not re.fullmatch(CHECK_ETA, str(eta)):
                st.error("L'età deve essere tra 0 e 110")
            else:
                etaCorretta = True
                if eta < 18:
                    st.warning("Paziente pediatrico")
                else:
                    st.success("✔")
        if not etaCorretta:
            return 

        st.divider()

        peso = st.number_input("Peso (kg)", min_value=2.0, max_value=300.0, value=70.0, step=0.5, format="%.1f")
        
        st.divider()
        col4, col5 = st.columns(2)
        with col4:
            sesso = st.toggle("Sesso")
        if sesso:
            valore_sesso = "F"
        else:
            valore_sesso = "M"
        with col5:
            st.info(f"{valore_sesso}")
            
        st.divider()

        cfCorretto = False
        codice_fiscale = st.text_input("Codice fiscale", key="cf_paziente", on_change=forza_maiuscolo_paziente)
        codice_fiscale = codice_fiscale.strip().upper()
        
        if codice_fiscale: 
            if not re.fullmatch(CHECK_CF, codice_fiscale):
                st.error("Codice fiscale non valido (XXXXXX00X00X000X)!")
            elif not codicefiscale.isvalid(codice_fiscale):
                st.error("Codice fiscale non valido: l'ultima lettera non corrisponde!")
            else:
                st.success("✔")
                cfCorretto = True

        if not cfCorretto:
            return

        st.divider()

        if st.button("Salva Paziente", type="primary", use_container_width=True):
            nuovo = Paziente(nome, cognome, peso, valore_sesso, data_di_nascita, codice_fiscale, self.utente_corrente)
            
            with GestoreUI.spinner_medico("Salvataggio del paziente nel database ..."):
                import time
                time.sleep(1)
                successo = self.db.inserisci_paziente(nuovo)
                
            if successo:
                st.success("Paziente salvato con successo!")
                if "cf_paziente" in st.session_state:
                    del st.session_state.cf_paziente
                time.sleep(1)
                st.rerun()
            else:
                st.error("Errore nel salvataggio del paziente!")




    # Funzione simulata di analisi (Main Page)
    def _pagina_principale_analisi(self):
        st.header("Analisi in Corso...")
        st.write("Dati ricevuti dalla sidebar:")
        # Recuperiamo i dati dalla memoria
        dati = st.session_state['dati_paziente']
        st.info(f"Paziente: {dati['sesso']}, {dati['eta']} anni. Vista: {dati['posizione']}")
        st.success("Ciao! I dati sono arrivati nel backend.")


