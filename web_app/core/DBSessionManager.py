import streamlit as st
import psycopg2
from typing import Optional
from costanti.QuerySQL import QuerySQL

class DBSessionManager:

    @staticmethod
    def avvia_sessione(db, paziente, medico):
        """Avvia la transazione serializable"""
        if 'connessione_storico' in st.session_state:
            try:
                st.session_state.cursore_storico.execute(QuerySQL.TRANSAZIONE)
                return
            except:
                DBSessionManager.chiudi_sessione()
        
        try:
            connessione = db._get_connessione()
            connessione.set_session(isolation_level='serializable')
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.LOCK, (paziente.codice_fiscale, ))
            cursore.execute(QuerySQL.ANALISI_PAZIENTE, (paziente.codice_fiscale, ))
            st.session_state.connessione_storico = connessione
            st.session_state.cursore_storico = cursore
        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            st.error(f"Errore critico sessione clinica: {e}")

    @staticmethod
    def chiudi_sessione():
        """Chiude tutto e pulisce lo stato"""
        if 'connessione_storico' in st.session_state:
            try:
                st.session_state.connessione_storico.commit()
                st.session_state.cursore_storico.close()
                st.session_state.connessione_storico.close()
            except:
                pass
            
            del st.session_state.connessione_storico
            del st.session_state.cursore_storico