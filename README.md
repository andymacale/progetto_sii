# Tecniche di Machine Learning e Computer Vision per l'analisi ed il suggerimento di follow-up clinici

Questo progetto di ricerca propone una pipeline avanzata di Deep Learning per l'automazione del processo diagnostico sui dati clinici.

## Stack
- **Linguaggio:** Python 3.12.3
- **Machine/Deep Learning:** LSTM + MLP
- **Informatica Teorica:** Uso delle espressioni regolari per la validazione
- **Frontend:** Streamlit (Interfaccia Medico-Paziente)
- **Dataset:** MIMIC-CXR potenziato con Tabu Search, Simulated Annealing e Algoritmi genetici
- **DBMS:** PostgreSQL

## Struttura del Repository
- `web_app/`: Codice dell'interfaccia utente Streamlit.
- `src/`: Core logic per l'estrazione delle feature e i modelli.
- `notebooks/`: Ricerca e addestramento (eseguiti su Google Colab).
- `data/`: (Escluso da Git) Cartelle locali per i dataset originali e processati.
