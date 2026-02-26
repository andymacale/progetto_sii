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
from core.costanti import CHECK_CF, CHECK_EMAIL, CHECK_PASSWORD, CHIAVE
import pyotp
import qrcode
from io import BytesIO
from core.EmailService import EmailService

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
        if "mostra_popup_recupero" not in st.session_state:
            st.session_state.mostra_popup_recupero = False
        
        # Se l'interruttore è attivo, il Controller lancia il popup
        if st.session_state.mostra_popup_recupero:
            self._modal_recupero_account()
        # ----------------------------------

        st.subheader("Accesso")
        email = st.text_input("Email", key="login_email", on_change=forza_minuscolo_login)
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Accedi", type="primary"):
            email = email.strip().lower()
            if not re.fullmatch(CHECK_EMAIL, email) or not re.fullmatch(CHECK_PASSWORD, password):
                st.error("Email o password errati!")
            else:
                utente = self.db.verifica_login(email, password)
                if utente:
                    segreto = self.db.get_segreto_2fa(email)
                    if not segreto:
                        self._modalita_setup_2fa(utente)
                    else:
                        self._modalita_verifica_2fa(utente, segreto)
                else:
                    st.error("Email o password errati!")

        st.divider() # Linea estetica

        # Il tasto che attiva il sistema di controllo
        if st.button("Password dimenticata o 2FA perso?", type="secondary"):
            st.session_state.mostra_popup_recupero = True
            st.session_state.step_recupero = 1 # Reset dello step al primo click
            st.rerun()
            
    def _register(self):
        """Registrazione"""
        nome = st.text_input("Nome")
        cognome = st.text_input("Cognome")
        codice_fiscale = st.text_input("Codice fiscale", key="reg_cf", on_change=forza_maiuscolo)
        data_di_nascita = st.date_input("Data di nascita", min_value=date(1920, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
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
            forza = valuta_password(password)
            if forza == "Debole":
                st.error("La password deve essere di 8-16 caratteri con almeno una maiuscola ed un carattere speciale (@$!%*?&#-_)")
                return
            elif forza == "Media":
                st.warning("Password accettabile, ma ti consiglio di aggiungere un numero ed una minuscola per renderla più sicura")
            else:
                st.success("Password forte!")
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
                time.sleep(2)
                st.rerun()
            else:
                st.error("Errore durante la registrazione")

    @st.dialog("Configura l'Autenticazione a due fattori (Obbligatorio!)")
    def _modalita_setup_2fa(self, utente):
        email = utente['email']

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
                
            # Verifichiamo se il codice inserito corrisponde al segreto
            if totp.verify(codice_inserito):
                # SUCCESSO! Salviamo il segreto nel DB
                if self.db.salva_segreto_2fa(email, segreto):
                    st.success("Autenticazione 2FA configurata! Accesso in corso...")
                    # Puliamo la variabile temporanea
                    del st.session_state.temp_secret
                    
                    # Finalmente, diamo l'ok per il login!
                    st.session_state.utente_loggato = True
                    st.session_state.dati_utente = utente
                    time.sleep(2)
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
                
            # Generiamo l'oggetto TOTP usando il segreto salvato nel database
            totp = pyotp.TOTP(segreto_salvato)
            
            # Verifichiamo se il codice digitato è corretto in questo momento
            if totp.verify(codice_inserito):
                st.success("Codice corretto! Accesso in corso...")
                st.session_state.utente_loggato = True
                st.session_state.dati_utente = utente
                time.sleep(1)
                st.rerun()
            else:
                st.error("Codice errato o scaduto. Riprova.")

    @st.dialog("Recupero Account")
    def _modal_recupero_account(self):
        # 1. CONTROLLO USCITA: Se l'utente chiude il dialog con la "X" di Streamlit, 
        # dobbiamo resettare l'interruttore al prossimo giro.
        
        if st.session_state.step_recupero == 1:
            st.write("Step 1: Identificazione")
            email_input = st.text_input("Inserisci la tua email", key="rec_email")
            
            if st.button("Invia Codice di Verifica", use_container_width=True):
                email_p = email_input.strip().lower()
                if self.db.controlla_esistenza_utente(email_p):
                    # Generazione e Invio
                    otp = self.email_service.genera_otp()
                    if self.email_service.invia_otp(email_p, otp):
                        # AGGIORNAMENTO STATO (Il Controllo)
                        st.session_state.otp_inviato = otp
                        st.session_state.email_target = email_p
                        st.session_state.step_recupero = 2
                        st.rerun() # Forza il controller a passare allo step 2
                    else:
                        st.error("Errore tecnico nell'invio email.")
                else:
                    st.error("Email non trovata nel database.")

        elif st.session_state.step_recupero == 2:
            st.write("Step 2: Verifica e Reset")
            st.info(f"Codice inviato a: {st.session_state.email_target}")
            
            codice_inserito = st.text_input("Codice OTP (6 cifre)", max_chars=6)
            nuova_pass = st.text_input("Nuova Password", type="password")
            conferma_pass = st.text_input("Conferma Password", type="password")

            if st.button("Finalizza Reset", type="primary", use_container_width=True):
                # --- LOGICA DI CONTROLLO VALIDAZIONE ---
                if codice_inserito != st.session_state.otp_inviato:
                    st.error("Codice OTP non valido.")
                elif nuova_pass != conferma_pass:
                    st.error("Le password non coincidono.")
                elif not re.fullmatch(CHECK_PASSWORD, nuova_pass):
                    st.error("La password deve essere di 8-16 caratteri con almeno una maiuscola ed un carattere speciale (@$!%*?&#-_)")
                else:
                    # Esecuzione nel DB
                    hash_pw = bcrypt.hashpw(nuova_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    if self.db.reset_totale_account(st.session_state.email_target, hash_pw):
                        st.success("Account resettato con successo!")
                        
                        # RESET FINALE DEL SISTEMA DI CONTROLLO
                        st.session_state.mostra_popup_recupero = False
                        del st.session_state.step_recupero
                        del st.session_state.otp_inviato
                        
                        import time
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Errore nel salvataggio dei dati.")
            
            if st.button("Torna indietro"):
                st.session_state.step_recupero = 1
                st.rerun()