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
from dominio.ValutazioneClinica import ValutazioneClinica
from dominio.Visita import Visita
from core.MotoreIA import MotoreIA
import uuid
import tempfile
import os
import subprocess



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
            if st.button("Home", type="primary", use_container_width=True):
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
        elif pagina == 'risultato_ia' and self.paziente_corrente:
            self._render_pagina_risultato_ia()
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
        st.subheader("Elenco pazienti")
        if numero_pazienti == 0:
            st.write("👤")
            st.caption("Nessuna paziente registrato")
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
            st.data_editor(
                df_stampa,
                column_config = {
                    "id": None,
                    "Apri": st.column_config.CheckboxColumn("Seleziona", default=False),
                    "codice fiscale": st.column_config.TextColumn("Codice Fiscale", disabled=True),
                    "nome": st.column_config.TextColumn("Nome", disabled=True),
                    "cognome": st.column_config.TextColumn("Cognome", disabled=True),
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
        st.subheader(f"Cartella Clinica: {self.paziente_corrente.nome} {self.paziente_corrente.cognome}")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Codice fiscale**: {self.paziente_corrente.codice_fiscale}")
            if self.paziente_corrente.sesso == 'F':
                st.write(f"**Sesso**: Femminile")
            else:
                st.write(f"**Sesso**: Maschile")
        with col2:
            st.write(f"**Data di nascita**: {self.paziente_corrente.data_di_nascita.strftime('%d/%m/%Y')}")
            st.write(f"**Altezza**: {self.paziente_corrente.altezza} cm")
        if self.paziente_corrente.bcpo:
            st.warning(f"Paziente affetto da Broncopneumopatia Cronica Ostuttiva")
        if self.paziente_corrente.storia_oncologica:
            st.write(f"Precedenti oncologici registrati")
        st.divider()
        visite = self.db.get_analisi_paziente(cursore_attivo=st.session_state.cursore_storico, 
                                                  paziente=self.paziente_corrente, 
                                                  medico=self.utente_corrente) 
        col_azione_1, col_azione_2 = st.columns(2)
        with col_azione_1:
            if st.button("Inserisci Nuova Analisi", use_container_width=True, type="primary"):
                self._modalita_nuova_analisi()
        with col_azione_2:
            if visite:
                if st.button("Processa Analisi", use_container_width=True, type="primary"):
                    self._modalita_processa_analisi()
            else:
                st.button("Processa Analisi", use_container_width=True, type="primary", disabled=True)
        st.divider()
        st.markdown("<br>", unsafe_allow_html=True)
        if "cursore_storico" in st.session_state:
            st.subheader("Elenco visite")
            if not visite:
                st.write("📂")
                st.caption("Nessuna visita registrata")
            else:
                df = self._visite_to_dataframe_ui(visite)
                st.data_editor(
                    df,
                    column_config = {
                        "data visita": st.column_config.DatetimeColumn(
                            "Ultima Visita",
                            format="DD/MM/YYYY HH:mm",
                            help="Data dell'ultimo incontro registrato",
                            disabled=True
                        ),
                        "tipo": st.column_config.TextColumn("Tipo", disabled=True),
                        "emoglobina": st.column_config.NumberColumn("Emoglobina", disabled=True),
                        "leucociti": st.column_config.NumberColumn("Leucociti", disabled=True),
                        "piastrine": st.column_config.NumberColumn("Piastrine", disabled=True),
                        "creatinina": st.column_config.NumberColumn("Creatinina", disabled=True),
                        "saturazione spo2": st.column_config.NumberColumn("SPO2", disabled=True),
                        "ldh": st.column_config.NumberColumn("LDH", disabled=True),
                        "albumia": st.column_config.NumberColumn("Albumia", disabled=True),
                        "peso": st.column_config.NumberColumn("Peso", format="%.1f", disabled=True),
                        "altezza": st.column_config.NumberColumn("Altezza", disabled=True),
                        "bcpo": st.column_config.CheckboxColumn(
                                                                "BCPO",
                                                                help="Paziente affetto da Broncopneumopatia Cronica Ostuttiva", 
                                                                disabled=True),
                        "storia oncologica": st.column_config.CheckboxColumn(
                                                                             "Storia oncologica",
                                                                             help="Precedenti oncologici registrati",
                                                                             disabled=True)
                        },
                    hide_index=True,
                    width='stretch',
                    key="tabella_visite"
                )

    @st.dialog("Inserisci Nuova Analisi")
    def _modalita_nuova_analisi(self):
        st.write(f"Paziente {self.paziente_corrente.codice_fiscale}")
        st.caption("I campi contrassegnati con $^*$ sono obbligatori")
        col1, col2 = st.columns(2)
        with col1:
            data_visita = st.date_input("Data Visita $^*$", value=datetime.now().date(), format="DD/MM/YYYY")
        with col2:
            ora_visita = st.time_input("Ora Visita $^*$", value=datetime.now().time())
            
        tipo_visita = st.selectbox("Tipo di Visita $^*$", ["Controllo di routine", "Visita specialistica", "Esami del sangue", "Urgenza"])
        peso = st.number_input("Peso (kg) *", min_value=1.0, max_value=300.0, value=None, step=0.1)
        
        if not peso:
            st.error("Peso è un campo obbligatorio!")
            return
        st.divider()
              
        emoglobina = st.number_input("Emoglobina (g/dL)", min_value=0.0, value=None, step=0.1)
        creatinina = st.number_input("Creatinina (mg/dL)", min_value=0.0, value=None, step=0.01)
        leucociti = st.number_input("Leucociti (mila/µL)", min_value=0.0, value=None, step=0.1)
        piastrine = st.number_input("Piastrine (mila/µL)", min_value=0, value=None, step=1)
        glicemia = st.number_input("Glicemia (mg/dL)", min_value=0, value=None, step=1)
        saturazione = st.number_input("SpO2 (%)", min_value=0, max_value=100, value=None, step=1)
        ldh = st.number_input("LDH (U/L)", min_value=0, value=None, step=1)
        albumina = st.number_input("Albumina (g/dL)", min_value=0.0, value=None, step=0.1)
        
        if st.button("Salva Analisi", type="primary", use_container_width=True):
            nuovo = ValutazioneClinica(
                    paziente=self.paziente_corrente,
                    medico=self.utente_corrente,
                    data_visita = datetime.combine(data_visita, ora_visita),
                    tipo=tipo_visita,
                    peso=peso,
                    emoglobina=emoglobina,
                    leucociti=leucociti,
                    piastrine=piastrine,
                    creatinina=creatinina,
                    glicemia=glicemia,
                    saturazione=saturazione,
                    ldh=ldh,
                    albumina=albumina
                    )
            
            with GestoreUI.spinner_medico("Salvataggio dell'analisi nel database ..."):
                time.sleep(1)
                successo = self.db.inserisci_visita(nuovo)
                
            if successo:
                st.success("Analisi salvata con successo!")
                time.sleep(1)
                self._reset_selezione_paziente()
                st.rerun()
            else:
                st.error("Errore nel salvataggio dell'analisi!")

    def _visite_to_dataframe_ui(self, lista_visite):
        """Metodo di servizio solo per l'estetica della UI"""
        dati = []
        for v in lista_visite:
            dati.append({
                "Ultima Visita": v.data_visita.strftime('%d/%m/%Y %H:%M'),
                "Tipo": v.tipo,
                "Emoglobina": v.emoglobina,
                "Leucociti": v.leucociti,
                "Piastrine": v.piastrine,
                "Creatinina": v.creatinina,
                "Glicemia": v.glicemia,
                "SPO2": v.saturazione,
                "LDH": v.ldh,
                "Albumina": v.albumina,
                "Peso": v.peso
            })
        return pd.DataFrame(dati)

    def _modalita_processa_analisi(self):
        config, modello, scaler = MotoreIA.carica_risorse()
        visite_paziente = self.db.get_analisi_paziente(paziente=self.paziente_corrente, 
                                                       medico=self.utente_corrente,
                                                       cursore_attivo=st.session_state.cursore_storico,
                                                       ordinamento="asc")
        
        with st.spinner("L'IA sta elaborando i dati temporali..."):
            t_seq, t_len, t_stat = MotoreIA.prepara_dati(visite_paziente, self.paziente_corrente, scaler, config)
            probabilita = MotoreIA.esegui_inferenza(modello, t_seq, t_len, t_stat)
            
            st.session_state.risultato_ia = {
                "prob": probabilita,
                "t_seq": t_seq,
                "t_len": t_len,
                "t_stat": t_stat,
                "modello": modello 
            }
            
            st.session_state.pagina_attiva = 'risultato_ia'
            st.rerun()


    def _render_pagina_risultato_ia(self):
        # Recupero dati dalla sessione
        res = st.session_state.get("risultato_ia")
        if not res:
            st.session_state.pagina_attiva = 'dettaglio_paziente'
            st.rerun()

        prob = res["prob"]
        
        if st.button("Torna alla Cartella Clinica"):
            st.session_state.pagina_attiva = 'dettaglio_paziente'
            st.rerun()

        st.title("Report Analisi Predittiva")
        st.caption(f"Paziente: {self.paziente_corrente.nome} {self.paziente_corrente.cognome} | CF: {self.paziente_corrente.codice_fiscale}")
        
        if prob > 0.70:
            colore, esito, nota = "red", "POSITIVO", "Rischio critico rilevato."
        elif 0.40 < prob <= 0.70:
            colore, esito, nota = "orange", "A RISCHIO", "Monitoraggio consigliato."
        else:
            colore, esito, nota = "green", "NEGATIVO", "Parametri stabili."

        st.markdown(f"""
            <div style="background-color: {colore}; padding: 30px; border-radius: 15px; text-align: center; color: white;">
                <h1 style="margin:0; font-size: 50px;">{esito}</h1>
                <h3 style="margin:0; opacity: 0.8;">Probabilità di rischio: {prob*100:.1f}%</h3>
            </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.subheader("Interpretazione dei parametri")
        temporal_cols = ['Emoglobina', 'Leucociti', 'Piastrine', 'Creatinina', 'Glicemia', 'BMI']
        fig = MotoreIA.calcola_shap_grafico(res["modello"], res["t_seq"], res["t_len"], res["t_stat"], feature_names=temporal_cols)
        if fig: st.pyplot(fig, width='content')
        st.divider()
        #st.button("Salva risultati", use_container_width=True, type="primary"):
        with GestoreUI.spinner_medico("Elaborazione dati e compilazione referto firmato..."):
            time.sleep(1.5)
            pdf_bytes = self._genera_pdf_latex(esito, prob, nota)
            if pdf_bytes:
                ora_attuale = datetime.now()
                timestamp_file = ora_attuale.strftime("%d-%m-%Y_%H-%M")
                st.download_button(
                                    label="Salva risultati",
                                    data=pdf_bytes,
                                    file_name=f"Referto_{self.paziente_corrente.codice_fiscale}_{timestamp_file}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True,
                                    type="primary")
            else:
                st.error("Errore nella generazione del file PDF")
    
            
    def _genera_pdf_latex(self, esito, prob, nota):
        with open("referto_template.tex", "r", encoding=CHIAVE) as f:
            template = f.read()

        nome_completo = f"{self.paziente_corrente.nome} {self.paziente_corrente.cognome}".replace("_", r"\_")
        
        mappa_colori = {"POSITIVO": "medred", "A RISCHIO": "medorange", "NEGATIVO": "medgreen"}
        colore_latex = mappa_colori.get(esito, "black")

        mappa_valori = {
            "{{NOME_COGNOME}}": nome_completo,
            "{{CODICE_FISCALE}}": self.paziente_corrente.codice_fiscale,
            "{{DATA_NASCITA}}": self.paziente_corrente.data_di_nascita.strftime('%d/%m/%Y'),
            "{{ALTEZZA}}": str(self.paziente_corrente.altezza),
            "{{COLORE}}": colore_latex,
            "{{ESITO}}": esito,
            "{{PROBABILITA}}": f"{prob*100:.1f}",
            "{{NOTA_CLINICA}}": nota,
            "{{UUID}}": str(uuid.uuid4())[:8].upper(),
            "{{COGNOME_MEDICO}}": self.utente_corrente.cognome
        }

        testo_finale = template
        for placeholder, valore in mappa_valori.items():
            testo_finale = testo_finale.replace(placeholder, valore)

        # 4. Compilazione in cartella temporanea
        with tempfile.TemporaryDirectory() as tmpdir:
            path_tex = os.path.join(tmpdir, "referto_generato.tex")
            with open(path_tex, "w", encoding="utf-8") as f:
                f.write(testo_finale)
            
            try:
                subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "referto_generato.tex"], 
                    cwd=tmpdir, 
                    stdout=subprocess.DEVNULL, 
                    check=True
                )
                
                path_pdf = os.path.join(tmpdir, "referto_generato.pdf")
                with open(path_pdf, "rb") as f:
                    return f.read() # Restituisce i byte pronti per il DB (bytea)
            except Exception as e:
                print(f"Errore pdflatex: {e}")
                return None
    

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