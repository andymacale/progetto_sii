#!/bin/bash

# 1. Identifichiamo i percorsi assoluti
DIR_SITO=$(cd "$(dirname "$0")" && pwd)
PATH_PROGETTO=$(cd "$DIR_SITO/.." && pwd)

echo "AVVIO SITO CON COMPILATORE LATEX"
echo "Progetto: $PATH_PROGETTO"
echo "Cartella App: $DIR_SITO"

# 2. Controllo esistenza file critici
if [ ! -f "$DIR_SITO/.env" ]; then
    echo "ERRORE: Il file .env non esiste in $DIR_SITO"
    exit 1
fi

# 3. Lancio Docker con installazione dipendenze di sistema (LaTeX)
# Nota: abbiamo aggiunto 'apt-get update' e l'installazione di texlive
sudo docker run --gpus all -it --rm \
    --name tesi_sito \
    --ipc=host \
    --network=host \
    -e TZ=Europe/Rome \
    --env-file "$DIR_SITO/.env" \
    -v "$PATH_PROGETTO:/workspace" \
    -w /workspace/web_app \
    -e PYTHONPATH=/workspace \
    -e MEDICAL_HOME=/workspace \
    tesi_ia_immagine \
    bash -c "streamlit run app.py --server.address 0.0.0.0"