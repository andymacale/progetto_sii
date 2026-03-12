#!/bin/bash

# --- SETUP AMBIENTE TESI (LIGHTNING AI) ---

echo "1. Configurazione Credenziali Kaggle..."
# Crea la cartella nascosta nella home di sistema (~/)
mkdir -p ~/.kaggle
# Copia il file che vedo nella tua struttura (this_studio/kaggle.json)
cp ./kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json
echo "Kaggle configurato correttamente."

echo "2. Attivazione Git LFS..."
# Fondamentale per scaricare i modelli reali invece dei puntatori
git lfs install
echo "LFS pronto."

echo "3. Sincronizzazione Repository e Modelli..."
# Scarica eventuali modifiche al codice e i file .pth pesanti
git pull origin main
echo "Codice e modelli (.pth) aggiornati."

echo "4. Download Dataset da Kaggle..."
# Crea la cartella data (che è nel tuo .gitignore)
mkdir -p ./data
# Scarica e scompatta il dataset direttamente in data/
# Sostituisci 'username/dataset' con il path reale del tuo dataset su Kaggle
echo "Inizio download dataset..."
kaggle datasets download -d andreamacale/dataset -p ./data --unzip
echo "Dataset pronto in ./data/"

echo "5. Installazione Dipendenze Python..."
# Se hai un file requirements.txt, lo installa
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Librerie installate."
else
    echo "Nessun file requirements.txt trovato, salto questo passaggio."
fi

echo "--------------------------------------------------------"
echo "SETUP COMPLETATO CON SUCCESSO!"
echo "Ora puoi avviare i tuoi notebook o script di training."
echo "--------------------------------------------------------"