# Tecniche di Machine Learning e Computer Vision per l'analisi ed il suggerimento di follow-up clinici

Questo progetto di ricerca propone una pipeline avanzata di Deep Learning per l'automazione del processo diagnostico su radiografie del torace, affrontando il problema della qualità del dato e della precisione della localizzazione tumorale.

## Visione del Progetto
Il sistema non si limita alla diagnosi, ma agisce come un assistente intelligente strutturato in tre fasi:

1. **Filtro Qualità (Gatekeeper):** Utilizzo di Random Forest e AdaBoost per scartare automaticamente immagini non diagnostiche (laterali, artefatti, rumore eccessivo) o applicare correzioni dinamiche (CLAHE).
2. **Segmentazione ROI (U-Net):** Isolamento dell'area polmonare per eliminare il rumore anatomico (clavicole, costole, tessuti molli esterni) e focalizzare l'analisi solo sui tessuti d'interesse.
3. **Diagnosi Tumorale (U-Net + NLP):** Identificazione di masse tumorali e validazione dei risultati tramite calcolo della Jaccard Similarity tra le mappe di attivazione dell'AI e i referti medici estratti dal dataset MIMIC-IV.

## Stack
- **Linguaggio:** Python 3.12.3
- **Decision Support System:** Boosting RandomForest-AdaBoost
- **Machine Learning:** PyTorch / U-Net
- **Computer Vision:** OpenCV (Pre-processing & Filtering)
- **Informatica Teorica:** Uso delle espressioni regolari per la validazione
- **Frontend:** Streamlit (Interfaccia Medico-Paziente)
- **Dataset:** MIMIC-CXR potenziato con Tabu Search, Simulated Annealing e Algoritmi genetici
- **DBMS:** PostgreSQL

## Struttura del Repository
- `web_app/`: Codice dell'interfaccia utente Streamlit.
- `src/`: Core logic per l'estrazione delle feature e i modelli.
- `notebooks/`: Ricerca e addestramento (eseguiti su Google Colab).
- `data/`: (Escluso da Git) Cartelle locali per i dataset originali e processati.