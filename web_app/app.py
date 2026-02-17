import streamlit as st
import re
from datetime import date

CHECK_ETA = r"^([1-9]|[1-9][0-9]|10[0-9]|110)$"


def sidebar_header():
    with st.sidebar:
        st.title("Sistema Diagnostico")
        st.info("Versione beta 1.0")

def sidebar_form_paziente():
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
        
def sidebar_prova():
    with st.sidebar:
        st.write("ciao!")

# Funzione simulata di analisi (Main Page)
def pagina_principale_analisi():
    st.header("Analisi in Corso...")
    st.write("Dati ricevuti dalla sidebar:")
    # Recuperiamo i dati dalla memoria
    dati = st.session_state['dati_paziente']
    st.info(f"Paziente: {dati['sesso']}, {dati['eta']} anni. Vista: {dati['posizione']}")
    st.success("Ciao! I dati sono arrivati nel backend.")

sidebar_header()
if 'step_analisi' not in st.session_state:
    st.session_state['step_analisi'] = False
if not st.session_state['step_analisi']:
    sidebar_form_paziente()
else:
    pagina_principale_analisi()
    if st.sidebar.button("Torna indietro"):
        st.session_state['step_analisi'] = False
        st.rerun()