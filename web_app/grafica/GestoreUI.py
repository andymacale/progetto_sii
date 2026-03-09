import streamlit as st
import os
from contextlib import contextmanager
from costanti.parametri import CHIAVE
import streamlit.components.v1 as components
import time
from costanti.Home import Home


class GestoreUI:

    @staticmethod
    def carica_css(nome_file="stile.css"):
        """Carica il file CSS nell'app"""
        # cartella_grafica = os.path.dirname(os.path.abspath(__file__))
        # path = os.path.join(cartella_grafica, nome_file)
        path = os.path.join(Home.GRAFICA, nome_file)
        try:
            with open(path, "r", encoding=CHIAVE) as file:
                st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError as e:
            st.error("Errore nel caricamento del CSS")

    @staticmethod
    def carica_icona(nome_file="icona.png"):
        """Carica il file CSS nell'app"""
        return Home.GRAFICA

    @staticmethod
    @contextmanager
    def spinner_medico(messaggio="Elaborazione in corso"):
        """Genera uno spinner grafico durante i caricamenti medi"""
        placeholder = st.empty()
        path = os.path.join(Home.GRAFICA, "spinner.html")
        try:
            with open(path, "r", encoding=CHIAVE) as file:
                template_spinner = file.read()
            html = template_spinner.format(messaggio=messaggio)
        except FileNotFoundError as e:
            html = f"<div>{messaggio}</div>"
        placeholder.markdown(html, unsafe_allow_html=True)
        try:
            yield 
        finally:
            placeholder.empty()

    @staticmethod
    def esegui_js_salva_token(token):
        """Leggi il file salva_token.js e sostituisce il segnaposto con il token reale"""
        path = os.path.join(Home.GRAFICA, "salva_token.js")
        with open(path, "r", encoding=CHIAVE) as file_js:
            codice_js = file_js.read()
        codice_js = codice_js.replace("__TOKEN__", token)
        components.html(f"<script>{codice_js}</script>",height=0)

    @staticmethod
    def esegui_js_elimina_token():
        """Leggi il file elimina_token.js per l'eliminazione e lo esegue"""
        path = os.path.join(Home.GRAFICA, "elimina_token.js")
        with open(path, "r", encoding=CHIAVE) as file_js:
            codice_js = file_js.read()
        components.html(f"<script>{codice_js}</script>",height=0)