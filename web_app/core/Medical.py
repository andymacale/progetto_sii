import streamlit as st
import re
from datetime import date
import bcrypt
import time
from core.costanti import CHIAVE, CHECK_ETA, CHECK_PASSWORD
from grafica.GestoreUI import GestoreUI

class Medical:
    def __init__(self, db_gestore):
        self.db = db_gestore
        if "dati_utente" in st.session_state:
            self.utente_corrente = st.session_state.dati_utente

    def homepage(self):
        cognome = self.utente_corrente['cognome']
        email = self.utente_corrente['email']
        sesso = self.utente_corrente['sesso']
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
                if st.button("Cambia Password", use_container_width=True):
                    self._modalita_cambia_password() 
                if st.button("Esci", type="primary", use_container_width=True):
                    st.session_state.utente_loggato = False
                    st.session_state.dati_utente = None
                    st.rerun()

        st.divider()

        # # 4. Gestione della navigazione (Sidebar e Main Page)
        # if 'step_analisi' not in st.session_state:
        #     st.session_state['step_analisi'] = False
            
        # self._sidebar_header()
        
        # if not st.session_state['step_analisi']:
        #     self._sidebar_form_paziente()
        # else:
        #     self._pagina_principale_analisi()
        #     if st.sidebar.button("Torna indietro"):
        #         st.session_state['step_analisi'] = False
        #         st.rerun()


    def _modalita_nuovo_paziente(self):
        st.info("Work in progress")
    
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
                email = self.utente_corrente['email']
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


    def _sidebar_header(self):
        with st.sidebar:
            st.title("Sistema Diagnostico")
            st.info("Versione beta 1.0")

    def _sidebar_form_paziente(self):
        with st.sidebar:

            st.title("Inserimento dati paziente")

            etaCorretta = False
            dataCorretta = False
            
            # ETA' DEL PAZIENTE
            eta_input = st.text_input('Eta del paziente possibilmente maggiorenne (0-110)', placeholder='Es. 50')
            if eta_input:
                # Inserimeto del dato
                if re.fullmatch(CHECK_ETA, eta_input):
                    etaCorretta = True
                    eta_input = int(eta_input) # Sicuro e' intero: puoi effettuare la conversione
                    if eta_input < 18:
                        st.warning("ATTENZIONE: PAZIENTE PEDIATRICO!")
                else:
                    st.error("FORMATO ETA NON VALIDO: deve essere un intero tra 0 e 110!")
            st.divider()

            # SESSO DEL PAZIENTE
            sesso_input = st.toggle("Sesso: M (OFF) / F (ON)")
            if sesso_input:
                valore_sesso = "F"
            else:
                valore_sesso = "M"
            st.divider()

            posizione_input = st.toggle("Posizione: AP (OFF) / PA (ON)")
            if posizione_input:
                valore_pos = "PA"
            else:
                valore_pos = "AP"
            
            # POSIZIONE DEL PAZIENTE
            oggi = date.today()
            data_input = st.date_input("Data analisi", value=oggi, format="DD/MM/YYYY")
            if data_input > oggi:
                st.error("DATA NON VALIDA!")
            dataCorretta = True
            st.divider()
            if etaCorretta and dataCorretta:
                riepilogo = {"eta": eta_input,
                            "sesso": valore_sesso,
                            "posizione": valore_pos,
                            "data": str(data_input) }
                st.success("Dati corretti")
                st.write("Riepilogo:")
                st.json(riepilogo)
                if st.button("Invia dati", type="primary"):
                    st.session_state['dati_paziente'] = riepilogo
                    st.session_state['step_analisi'] = True # Flag per cambiare pagina/vista
                    st.rerun() # Ricarica la pagina per aggiornare la UI
            else:
                correggi = []
                if not etaCorretta and eta_input:
                    correggi.append("Eta")
                if not dataCorretta:
                    correggi. append("Data")
                stringaErrore = ", ".join(correggi)
                if len(correggi) > 0:
                    st.error("Rileggi i campi: " + stringaErrore)
                else:
                    st.error("Inserire l'età")
        

    # Funzione simulata di analisi (Main Page)
    def _pagina_principale_analisi(self):
        st.header("Analisi in Corso...")
        st.write("Dati ricevuti dalla sidebar:")
        # Recuperiamo i dati dalla memoria
        dati = st.session_state['dati_paziente']
        st.info(f"Paziente: {dati['sesso']}, {dati['eta']} anni. Vista: {dati['posizione']}")
        st.success("Ciao! I dati sono arrivati nel backend.")


