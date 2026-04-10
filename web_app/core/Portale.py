from core.GestoreDB import GestoreDB
from dominio.Credenziali import Credenziali
from dominio.Medico import Medico
import streamlit as st
from datetime import date, datetime, timedelta
import time
import re
from email_validator import validate_email, EmailNotValidError
import bcrypt
import codicefiscale
from costanti.parametri import CHECK_CF, CHECK_EMAIL, CHECK_PASSWORD, CHIAVE, RESET_TIMER
import pyotp
import qrcode
from io import BytesIO
from core.EmailService import EmailService
from grafica.GestoreUI import GestoreUI
import uuid
from dominio.PreferenzaSessione import PreferenzaSessione

def forza_maiuscolo():
    if "reg_cf" in st.session_state:
        st.session_state.reg_cf = st.session_state.reg_cf.upper()

def forza_minuscolo():
    if "reg_email" in st.session_state:
        st.session_state.reg_email = st.session_state.reg_email.lower()

def forza_minuscolo_login():
    if "login_email" in st.session_state:
        st.session_state.login_email = st.session_state.login_email.lower()

def valuta_password(pwd: str) -> str:
    """Valuta la password in Debole, Media, Forte"""
    if not re.fullmatch(CHECK_PASSWORD, pwd):
        return "Debole"
    ha_numeri = bool(re.search(r"[0-9]", pwd))
    ha_minuscole = bool(re.search(r"[a-z]", pwd))
    if len(pwd) >= 12 and ha_numeri and ha_minuscole:
        return "Forte"
    return "Media"


class Portale:

    def __init__(self):
        self.db = GestoreDB()
        self.email_service = EmailService()

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
            email = email.strip().lower()
            if not re.fullmatch(CHECK_EMAIL, email) or not re.fullmatch(CHECK_PASSWORD, password):
                st.error("Email o password errati!")
            else:
                with GestoreUI.spinner_medico("Verifica credenziali"):
                    time.sleep(1.2)
                    utente = self.db.verifica_login(email, password)
                if utente:
                    segreto = self.db.get_segreto_2fa(email)
                    if not segreto:
                        self._modalita_setup_2fa(utente)
                    else:
                        self._modalita_verifica_2fa(utente, segreto)
                else:
                    st.error("Email o password errati!")

        st.divider()

        if "mostra_popup_recupero" not in st.session_state:
            st.session_state.mostra_popup_recupero = False

        if st.button("Password dimenticata o 2FA perso?", type="secondary", use_container_width=True):
            st.session_state.mostra_popup_recupero = True
            st.session_state.step_recupero = 1 
            st.rerun()

        if st.session_state.mostra_popup_recupero:
            self._modal_recupero_account()

    def _gestione_post_login(self, utente):
        """Gestisce il successo del login e la persistenza della sessione"""
        st.session_state.utente_loggato = True
        st.session_state.dati_utente = utente

        # 1. Recupero la preferenza dal DB
        codice_db = self.db.get_preferenza_sessione(utente.credenziali.email)

        # 2. Pulizia della stringa prima di passarla all'Enum
        codice_pulito = "Sempre"
        if codice_db:
            testo = str(codice_db).strip()
            if "Mai" in testo: codice_pulito = "Mai"
            elif "Ora" in testo: codice_pulito = "Ora"
            elif "Giorno" in testo: codice_pulito = "Giorno"
            elif "Settimana" in testo: codice_pulito = "Settimana"

        try:
            preferenza = PreferenzaSessione(codice_pulito)
        except ValueError:
            preferenza = PreferenzaSessione.SEMPRE

        # 3. Impostazione scadenza e token
        if preferenza == PreferenzaSessione.SEMPRE:
            st.session_state.comando_elimina_token = True
        else:
            ora_attuale = datetime.now()
            if preferenza == PreferenzaSessione.ORA:
                scadenza = ora_attuale + timedelta(hours=1)
            elif preferenza == PreferenzaSessione.GIORNO:
                scadenza = ora_attuale + timedelta(days=1)
            elif preferenza == PreferenzaSessione.SETTIMANA:
                scadenza = ora_attuale + timedelta(days=7)
            else:
                scadenza = None
        
            token_sicuro = str(uuid.uuid4())
            self.db.salva_token_sessione(utente.credenziali.email, token_sicuro, scadenza)
            st.session_state.comando_salva_token = token_sicuro

            
    def _register(self):
        """Registrazione"""
        nome = st.text_input("Nome")
        cognome = st.text_input("Cognome")
        codice_fiscale = st.text_input("Codice fiscale", key="reg_cf", on_change=forza_maiuscolo)
        data_di_nascita = st.date_input("Data di nascita", min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
        col1, col2 = st.columns(2)
        with col1:
            sesso_input = st.toggle("Sesso")
        if sesso_input:
            valore_sesso = "F"
        else:
            valore_sesso = "M"
        with col2:
            st.info(valore_sesso)
        st.divider()
        email = st.text_input("Email", key="reg_email", on_change=forza_minuscolo)
        password = st.text_input("Password", type="password", key="reg_pass")
        conferma_password = st.text_input("Conferma Password", type="password", key="reg_pass_conf")
        
        if st.button("Registrati", type="primary", use_container_width=True):
            if not nome or not cognome or not codice_fiscale or not data_di_nascita or not email or not password:
                st.error("Tutti i campi sono obbligatori!")
                return
            email = email.strip().lower()
            codice_fiscale = codice_fiscale.strip().upper()
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
                return
                
            forza = valuta_password(password)
            if forza == "Debole":
                st.error("La password deve essere di 8-16 caratteri con almeno una maiuscola ed un carattere speciale (@$!%*?&#-_)")
                return
            elif forza == "Media":
                st.warning("Password accettabile, ma ti consiglio di aggiungere un numero ed una minuscola per renderla più sicura")
            else:
                st.success("Password forte!")
                
            with GestoreUI.spinner_medico("Registrazione del profilo: "):
                time.sleep(1.2)
                password_bytes = password.encode(CHIAVE)
                sale = bcrypt.gensalt()
                password_criptata = bcrypt.hashpw(password_bytes, sale).decode(CHIAVE)
                credenziali_nuove = Credenziali(email=email_validata, password=password_criptata)
                medico_nuovo = Medico(nome=nome,
                                cognome=cognome,
                                codice_fiscale=codice_fiscale, 
                                data_di_nascita=data_di_nascita,
                                sesso=valore_sesso,
                                credenziali=credenziali_nuove)
                successo = self.db.inserisci_medico(medico_nuovo)
                
            if successo:
                st.success("Registrazione avvenuta con successo!")
            else:
                st.error("Errore durante la registrazione: email o codice fiscale già registrato!")

    @st.dialog("Configura l'Autenticazione a due fattori (Obbligatorio!)")
    def _modalita_setup_2fa(self, utente):
        email = utente.credenziali.email

        if "temp_secret" not in st.session_state:
            st.session_state.temp_secret = pyotp.random_base32()
        segreto = st.session_state.temp_secret
        totp = pyotp.TOTP(segreto)
        uri = totp.provisioning_uri(name=email, issuer_name="MedVision AI")
        
        qr = qrcode.make(uri)
        buf = BytesIO()
        qr.save(buf, format="PNG")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(buf.getvalue(), caption="Inquadra con l'App")
            
        st.divider()
        st.write("Dopo aver inquadrato il codice, inserisci qui sotto i **6 numeri** che vedi sull'App per confermare l'attivazione.")
        
        codice_inserito = st.text_input("Codice a 6 cifre", max_chars=6)
        
        if st.button("Verifica e Attiva", type="primary", use_container_width=True):
            if len(codice_inserito) != 6 or not codice_inserito.isdigit():
                st.error("Il codice deve essere di 6 numeri.")
                return
                
            if totp.verify(codice_inserito):
                if self.db.salva_segreto_2fa(email, segreto):
                    st.success("Autenticazione 2FA configurata! Accesso in corso...")
                    del st.session_state.temp_secret
                    
                    self._gestione_post_login(utente)
                    time.sleep(1.5) # Ritardo vitale per il salvataggio JS
                    st.rerun()
                else:
                    st.error("Errore durante il salvataggio nel database!")
            else:
                st.error("Codice errato o scaduto. Riprova.")

    @st.dialog("Autenticazione a due fattori")
    def _modalita_verifica_2fa(self, utente, segreto_salvato):
        st.write("Inserisci il codice a 6 cifre dall'app Google Authenticator.")
        
        codice_inserito = st.text_input("Codice 2FA", max_chars=6, key="input_2fa")
        
        if st.button("Verifica", type="primary", use_container_width=True):
            if len(codice_inserito) != 6 or not codice_inserito.isdigit():
                st.error("Il codice deve essere di 6 numeri!")
                return
                
            totp = pyotp.TOTP(segreto_salvato)
            
            if totp.verify(codice_inserito):
                st.success("Codice corretto! Accesso in corso...")
                self._gestione_post_login(utente)
                time.sleep(1.5) # Ritardo vitale per il salvataggio JS
                st.rerun()
            else:
                st.error("Codice errato o scaduto. Riprova.")

    @st.dialog("Recupero Account")
    def _modal_recupero_account(self):
        if "step_recupero" not in st.session_state:
            st.session_state.step_recupero = 1

        def reset_e_chiudi():
            st.session_state.mostra_popup_recupero = False
            if "step_recupero" in st.session_state: del st.session_state.step_recupero
            if "otp_inviato" in st.session_state: del st.session_state.otp_inviato
            if "email_target" in st.session_state: del st.session_state.email_target
            if "tempo_invio_otp" in st.session_state: del st.session_state.tempo_invio_otp
            st.rerun()

        # STEP 1
        if st.session_state.step_recupero == 1:
            st.write("Inserisci l'email per ricevere il codice.")
            email_rec = st.text_input("Email", key="email_rec_input")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Annulla", use_container_width=True):
                    reset_e_chiudi()
            with col2:
                if st.button("Invia OTP", type="primary", use_container_width=True):
                    email_f = email_rec.strip().lower()
                    if self.db.controlla_esistenza_utente(email_f):
                        with GestoreUI.spinner_medico("Invio dell'email in corso"):
                            otp = self.email_service.genera_otp()
                            inviata = self.email_service.invia_otp(email_f, otp)
                            time.sleep(0.5)
                        if inviata:
                            st.session_state.otp_inviato = otp
                            st.session_state.email_target = email_f
                            st.session_state.step_recupero = 2
                            st.session_state.tempo_invio_otp = time.time()
                            st.rerun()
                        else:
                            st.error("Errore invio email.")
                    else:
                        st.error("Email non trovata.")

        # STEP 2
        elif st.session_state.step_recupero == 2:
            st.info(f"Codice inviato a: {st.session_state.email_target}")
            tempo_trascorso = time.time() - st.session_state.tempo_invio_otp
            rimanenti = RESET_TIMER - int(tempo_trascorso)
            codice_u = st.text_input("Codice OTP", max_chars=6)
            n_pass = st.text_input("Nuova Password", type="password")
            c_pass = st.text_input("Conferma Password", type="password")

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Annulla", use_container_width=True):
                    reset_e_chiudi()
            with col2:
                if rimanenti > 0:
                    st.button(f"Attendi {rimanenti} s", disabled=True, use_container_width=True)
                    time.sleep(1)
                    st.rerun()
                else:
                    if st.button("Reinvia OTP", use_container_width=True):
                        with GestoreUI.spinner_medico("Nuovo invio in corso..."):
                            nuovo_otp = self.email_service.genera_otp()
                            esito = self.email_service.invia_otp(st.session_state.email_target, nuovo_otp)
                        if esito:
                            st.session_state.otp_inviato = nuovo_otp
                            st.session_state.tempo_invio_otp = time.time() 
                            st.success("Nuovo codice inviato!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Errore durante il reinvio!")
            with col3:
                if st.button("Reset Account", type="primary", use_container_width=True):
                    if codice_u != st.session_state.otp_inviato:
                        st.error("OTP errato.")
                    elif n_pass != c_pass:
                        st.error("Le password non coincidono.")
                    elif not re.fullmatch(CHECK_PASSWORD, n_pass):
                        st.error("Password troppo debole.")
                    else:
                        with GestoreUI.spinner_medico("Reset della password in corso"):
                            time.sleep(1.5)
                            hash_n = bcrypt.hashpw(n_pass.encode(CHIAVE), bcrypt.gensalt()).decode(CHIAVE)
                            successo = self.db.reset_totale_account(st.session_state.email_target, hash_n)
                        if successo:
                            st.success("Reset effettuato!")
                            time.sleep(1)
                            reset_e_chiudi()