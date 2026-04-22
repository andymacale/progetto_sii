# Progetto Sistemi Intelligenti Per Internet

Questo progetto di ricerca propone una pipeline avanzata di Deep Learning per l'automazione del processo diagnostico su radiografie del torace, affrontando il problema della qualità del dato e della precisione della localizzazione tumorale.

## Stack
- **Linguaggio:** Python 3.12.3
- **Machine Learning:** LSTM / MLP
- **Informatica Teorica:** Uso delle espressioni regolari per la validazione
- **Frontend:** Streamlit (Interfaccia Medico-Paziente)
- **Dataset:** MIMIC-IV
- **DBMS:** PostgreSQL

## Struttura del Repository
- `web_app/`: Codice dell'interfaccia utente Streamlit.
- `src/`: Core logic per l'estrazione delle feature e i modelli.
- `notebooks/`: Ricerca e addestramento.
- `data/`: (Escluso da Git) Cartelle locali per i dataset originali e processati.
- `relazione/`: Relazione stampata.