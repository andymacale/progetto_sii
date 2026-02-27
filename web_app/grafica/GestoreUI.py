import streamlit as st
import os
from contextlib import contextmanager
from core.costanti import CHIAVE
import time

class GestoreUI:

    @staticmethod
    def carica_css(nome_file="stile.css"):
        """Carica il file CSS nell'app"""
        cartella_grafica = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cartella_grafica, nome_file)
        try:
            with open(path, "r", encoding=CHIAVE) as file:
                st.markdown(f"<style>{file.read()}</style>", unsafe_allow_html=True)
        except FileNotFoundError as e:
            st.error("Errore nel caricamento del CSS")

    @staticmethod
    @contextmanager
    def spinner_medico(messaggio="Elaborazione in corso"):
        """Genera uno spinner grafico durante i caricamenti medi"""
        placeholder = st.empty()
        cartella_grafica = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(cartella_grafica, "spinner.html")
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