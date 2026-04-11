#!/bin/bash

# 1. Identifichiamo i percorsi assoluti
DIR_SITO=$(cd "$(dirname "$0")" && pwd)
PATH_PROGETTO=$(cd "$DIR_SITO/.." && pwd)

echo "AVVIO SITO"
echo "Progetto: $PATH_PROGETTO"
echo "Cartella App: $DIR_SITO"
echo "File .env: $DIR_SITO/.env"

# 2. Controllo esistenza file critici
if [ ! -f "$DIR_SITO/.env" ]; then
    echo "ERRORE: Il file .env non esiste in $DIR_SITO"
    exit 1
fi

# 3. Lancio Docker DIRETTO (senza screen)
sudo docker run --gpus all -it --rm \
    --name tesi_sito \
    --ipc=host \
    --network=host \
    -e TZ=Europe/Rome \
    --env-file "$DIR_SITO/.env" \
    -v "$PATH_PROGETTO:/workspace" \
    -v "$HOME/.cache/pip_docker:/root/.cache/pip" \
    -w /workspace/web_app \
    -e PYTHONPATH=/workspace \
    -e MEDICAL_HOME=/workspace \
    nvcr.io/nvidia/pytorch:25.02-py3 \
    bash -c "pip install --cache-dir=/root/.cache/pip -r requirements.txt python-dotenv && streamlit run app.py --server.address 0.0.0.0"