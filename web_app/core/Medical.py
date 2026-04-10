import streamlit as st
import re
from datetime import date
import bcrypt
import time
from costanti.parametri import CHIAVE, CHECK_PASSWORD, CHECK_CF, CHECK_ETA
from grafica.GestoreUI import GestoreUI
import codicefiscale
from dominio.Paziente import Paziente
from dominio.PreferenzaSessione import PreferenzaSessione
import uuid
from datetime import datetime, timedelta
import pandas as pd
import math
from core.DBSessionManager import DBSessionManager
#from streamlit_local_storage import LocalStorage



def forza_maiuscolo_paziente():
    if "cf_paziente" in st.session_state:
        st.session_state.cf_paziente = st.session_state.cf_paziente.upper()

class Medical:

    def __init__(self, db_gestore):
        self.db = db_gestore
        self.utente_corrente = st.session_state.get("dati_utente")
        self.paziente_corrente = st.session_state.get("paziente_corrente")
        self.pagina_attiva = st.session_state.get("pagina_attiva", "dashboard")
        if self.utente_corrente:
            self.email = self.utente_corrente.credenziali.email
            self.cognome = self.utente_corrente.cognome
            self.sesso = self.utente_corrente.sesso
        else:
            self.email = None
            self.cognome = None
            self.sesso = None

        # Controllo sicurezza cross-medico
        if self.paziente_corrente and self.utente_corrente:
            email_p = self.paziente_corrente.medico.credenziali.email
            if email_p != self.email:
                self.paziente_corrente = None
                st.session_state.paziente_corrente = None
                st.session_state.pagina_attiva = 'dashboard'
                self.pagina_attiva = 'dashboard'
        
    
    def _render_sidebar(self):
        with st.sidebar:
            st.markdown(f"### {'Dott.ssa' if self.sesso == 'F' else 'Dott.'} {self.cognome}")
            st.caption(f"Loggato come: {self.email}")
            st.divider()
            
            # Navigazione rapida per forzare il reset
            if st.button("Home", use_container_width=True):
                st.session_state.pagina_attiva = 'dashboard'
                st.session_state.step_analisi = False
                st.query_params.clear()
                self._reset_selezione_paziente() 
                st.rerun()

            with st.expander("Impostazioni Account"):
                if st.button("Mantieni l'accesso", use_container_width=True):
                    self._modalita_accesso()
                if st.button("Cambia Password", use_container_width=True):
                    self._modalita_cambia_password()
            
            st.markdown("<br>"*10, unsafe_allow_html=True)
            if st.button("Esci", type="primary", use_container_width=True):
                self.db.elimina_token_sessione(self.email)
                st.session_state.clear()
                st.session_state.comando_elimina_token = True
                st.rerun()

    def main_render(self):
        self.paziente_corrente = st.session_state.get("paziente_corrente")
        pagina = st.session_state.get("pagina_attiva", "dashboard")
        self._render_sidebar()
        if "pid" in st.query_params:
            try:
                pid_url = int(st.query_params["pid"])
                if not self.paziente_corrente:
                    paziente = self.db._get_paziente_by_id_and_medico(pid_url, self.utente_corrente)
                    if paziente:
                        self.paziente_corrente = paziente
                        st.session_state.paziente_corrente = paziente
                        st.session_state.pagina_attiva = 'dettaglio_paziente'
                        pagina = 'dettaglio_paziente'
                        
                        DBSessionManager.avvia_sessione(self.db, paziente, self.utente_corrente)
                    else:
                        st.query_params.clear() 
            except Exception as e:
                print(f"Errore nel routing URL: {e}")
                st.query_params.clear()

        if pagina == 'dettaglio_paziente' and self.paziente_corrente:
            self._dettaglio_paziente()
        else:
            st.query_params.clear()
            st.session_state.pagina_attiva = 'dashboard'
            self._homepage()
      
    def _homepage(self):
        st.title(f"Bentornat{'a' if self.sesso == 'F' else 'o'} {self.cognome}")
        st.divider()

        col_metrica, col_azione = st.columns([1, 1])
        with col_metrica:
            numero_pazienti = self.db.get_numero_pazienti(self.email)
            st.metric("Pazienti in cura", value=numero_pazienti)
        
        with col_azione:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Aggiungi nuovo paziente", use_container_width=True, type="primary"):
                self._modalita_nuovo_paziente()

        st.divider()

        if numero_pazienti == 0:
            st.info("**Benvenuto nel tuo pannello di controllo.**")
            st.write("""
            Non risultano pazienti registrati a tuo nome. 
            Inizia aggiungendo il tuo primo paziente premendo il tasto **'Aggiungi nuovo paziente'** in alto.
            """)
            st.caption("Una volta aggiunto, potrai visualizzare qui lo storico delle tue attività.")
        else:
            pazienti = self.db.get_elenco_pazienti(self.email)
            df = pd.DataFrame(pazienti)
            df.insert(0, "Apri", False)
            df["ultima visita"] = df["ultima visita"].apply(
                                                            lambda x: x.strftime('%d/%m/%Y') 
                                                            if pd.notnull(x) and x != "None" else "-"
                                                            )
            if 'pagina_pazienti' not in st.session_state:
                st.session_state.pagina_pazienti = 1
            elementi_per_pagina = 10
            totale_pagine = math.ceil( len(df) / elementi_per_pagina ) if not df.empty else 1
            inizio = (st.session_state.pagina_pazienti - 1) * elementi_per_pagina
            fine = inizio + elementi_per_pagina
            df_stampa = df.iloc[inizio:fine].copy()
            if "tabella_pazienti" in st.session_state:
                stato_widget = st.session_state["tabella_pazienti"]
                modifiche = stato_widget.get("edited_rows", {})
                if modifiche:
                    for index_str, changes in modifiche.items():
                        if changes.get("Apri") is True:
                            indice_reale = int(index_str)
                            id_paziente_raw = df_stampa.iloc[indice_reale]["id"]
                            id_paziente = int(id_paziente_raw)
                            stato_widget["edited_rows"] = {}         
                            st.query_params["pid"] = str(id_paziente)
                            paziente_obj = self.db._get_paziente_by_id_and_medico(id_paziente, self.utente_corrente)
                            if paziente_obj:
                                self._seleziona_paziente(paziente_obj)
            st.subheader("Elenco pazienti")
            st.data_editor(
                df_stampa,
                column_config = {
                    "id": None,
                    "Apri": st.column_config.CheckboxColumn("Seleziona", default=False),
                    "codice fiscale": st.column_config.TextColumn("Codice Fiscale", disabled=True),
                    "nome": st.column_config.TextColumn("Nome", disabled=True),
                    "cognome": st.column_config.TextColumn("cognome", disabled=True),
                    "ultima visita": st.column_config.DateColumn(
                        "Ultima Visita",
                        format="DD/MM/YYYY",
                        help="Data dell'ultimo incontro registrato",
                        disabled=True
                    )
                    },
                hide_index=True,
                width='stretch',
                key="tabella_pazienti"
            )

    def _seleziona_paziente(self, paziente: Paziente):
        st.session_state.paziente_corrente = paziente
        st.session_state.pagina_attiva = 'dettaglio_paziente'
        self.paziente_corrente = paziente
        DBSessionManager.avvia_sessione(self.db, paziente, self.utente_corrente)
        st.rerun()
    
    def _dettaglio_paziente(self):
        st.divider()
        st.title(f"Cartella Clinica: {self.paziente_corrente.nome} {self.paziente_corrente.cognome}")
        st.warning("Work in progress!")

    def _reset_selezione_paziente(self):
        DBSessionManager.chiudi_sessione()
        st.session_state.paziente_corrente = None
        self.paziente_corrente = None

    @st.dialog("Mantieni l'accesso")
    def _modalita_accesso(self):
        codice_db = self.db.get_preferenza_sessione(self.email)
        
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
            self.db.aggiorna_preferenza_sessione(self.email, enum_scelto.value)
            
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
                self.db.salva_token_sessione(self.email, nuovo_token_sicuro, scadenza)
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
                if not self.db.verifica_login(self.email, vecchia):
                    st.error("La vecchia password e' errata!")
                    return
                nuova_bytes = nuova.encode(CHIAVE)
                sale = bcrypt.gensalt()
                nuova_hash = bcrypt.hashpw(nuova_bytes, sale).decode(CHIAVE)
                if self.db.aggiorna_password(self.email, nuova_hash):
                    st.success("Password aggiornata! Ricarico l'area medica...")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Errore durante il salvataggio della nuova password")

    @st.dialog("Aggiungi Paziente")
    def _modalita_nuovo_paziente(self):
        st.title("Inserimento dati paziente")

        nome = st.text_input("Nome").strip()
        cognome = st.text_input("cognome").strip()

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

        altezza = st.number_input("Altezza (cm)", min_value=1.0, max_value=300.0, value=170.0, step=0.5, format="%.1f")
        
        st.divider()
        col4, col5 = st.columns(2)
        with col4:
            sesso = st.toggle("sesso")
        if sesso:
            valore_sesso = "F"
        else:
            valore_sesso = "M"
        with col5:
            st.info(f"{valore_sesso}")
        
        bcpo = st.toggle("BCPO")
        storia = st.toggle("Precedenti oncologici")
            
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
            nuovo = Paziente(
                             nome=nome,
                             cognome=cognome, 
                             altezza=altezza, 
                             data_di_nascita=data_di_nascita, 
                             codice_fiscale=codice_fiscale,
                             sesso=valore_sesso,
                             bcpo=bcpo,
                             storia_oncologica=storia, 
                             medico=self.utente_corrente)
            
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

    def _render_modulo_analisi(self):
        """Metodo per la gestione delle analisi cliniche"""
        st.title("Nuova Analisi Clinica")
        
        # Recupero pazienti per il menu a tendina
        pazienti = self.db.get_pazienti_medico(self.email)
        
        if not pazienti:
            st.warning("Nessun paziente trovato. Aggiungine uno dalla Home.")
            return

        nomi_pazienti = {f"{p['cognome']} {p['nome']}": p for p in pazienti}
        scelta = st.selectbox("Seleziona paziente:", ["-"] + list(nomi_pazienti.keys()))

        if scelta != "-":
            paziente = nomi_pazienti[scelta]
            st.session_state.paziente_selezionato = paziente
            st.subheader(f"Inserimento dati per: {scelta}")
            
            # Qui andrà il tuo st.data_editor per i dati ematochimici
            st.info("Tabella temporanea in attesa di configurazione...")

    # Funzione simulata di analisi (Main Page)
    def _pagina_principale_analisi(self):
        st.header("Analisi in Corso...")
        st.write("Dati ricevuti dalla sidebar:")
        # Recuperiamo i dati dalla memoria
        dati = st.session_state['dati_paziente']
        st.info(f"Paziente: {dati['sesso']}, {dati['eta']} anni. Vista: {dati['posizione']}")
        st.success("Ciao! I dati sono arrivati nel backend.")


