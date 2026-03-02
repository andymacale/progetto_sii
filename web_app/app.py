import streamlit as st
from core.Portale import Portale
from core.Medical import Medical
from core.GestoreDB import GestoreDB
from grafica.GestoreUI import GestoreUI
from streamlit_local_storage import LocalStorage
import streamlit.components.v1 as components
import os
from datetime import datetime

# Grafica: carimento del file css
st.set_page_config(page_title="Medical", layout="centered")

GestoreUI.carica_css()

if 'db' not in st.session_state:
    st.session_state.db = GestoreDB()

local_storage = LocalStorage()

# ==========================================
# 1. SCRITTURA E CANCELLAZIONE (JS BLINDATO)
# ==========================================
if st.session_state.get("comando_salva_token"):
    token = st.session_state.comando_salva_token
    # NON mettiamo height=0 altrimenti Streamlit lo nasconde troppo!
    components.html(f"""
        <script>
            try {{
                window.parent.localStorage.setItem('auth_token', '{token}');
                console.log("[Medical App] Token salvato con successo nel browser!");
            }} catch (e) {{
                console.error("[Medical App] Errore salvataggio LocalStorage:", e);
            }}
        </script>
    """, height=0)
    # 💡 TRUCCO MAGICO: NON cancelliamo più il comando qui! 
    # Lasciandolo vivo, il browser rinfresca il token ad ogni re-render.

if st.session_state.get("comando_elimina_token"):
    components.html("""
        <script>
            window.parent.localStorage.removeItem('auth_token');
            console.log("🗑️ [Medical App] Token eliminato dal browser!");
        </script>
    """, height=0)
    st.session_state.comando_elimina_token = False
    # Puliamo l'interruttore di salvataggio
    if "comando_salva_token" in st.session_state:
        del st.session_state["comando_salva_token"]

# ==========================================
# 2. LETTURA DEL TOKEN (AUTO-LOGIN AL F5)
# ==========================================
if not st.session_state.get('utente_loggato', False):
    token_salvato = local_storage.getItem("auth_token")
    
    # Se il token c'è e non è una stringa buggata
    if token_salvato and token_salvato not in ["null", "undefined", ""]:
        dati_sessione = st.session_state.db.verifica_token_sessione(token_salvato)
        if dati_sessione:
            scadenza = dati_sessione['scadenza']
            medico = dati_sessione['medico']
            
            if scadenza is None or datetime.now() < scadenza:
                st.session_state.utente_loggato = True
                st.session_state.dati_utente = medico
                st.rerun() # 🔄 Entriamo!
            else:
                st.session_state.db.elimina_token_sessione(medico.credenziali.email)
                st.session_state.comando_elimina_token = True
                st.rerun()

# ==========================================
# 3. ROUTING DELLE PAGINE
# ==========================================
if not st.session_state.get('utente_loggato', False):
    portale = Portale() 
    portale.db = st.session_state.db 
    portale.homepage()
else:
    area_medica = Medical(st.session_state.db)
    area_medica.homepage()