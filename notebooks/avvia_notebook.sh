#!/bin/bash
echo "📓 Avvio JUPYTER (Cache + No-Password)..."

# 1. Creiamo la cartella della cache per velocizzare i prossimi avvii
mkdir -p "$HOME/.cache/pip_docker"

# 2. Lancio Docker in modalità interattiva
sudo docker run --gpus all -it --rm \
    --name tesi_notebook \
    --ipc=host \
    -p 8888:8888 \
    -v "$(pwd):/workspace" \
    -v "$HOME/.cache/pip_docker:/root/.cache/pip" \
    nvcr.io/nvidia/pytorch:25.02-py3 \
    bash -c "
        pip install --cache-dir=/root/.cache/pip -r /workspace/notebooks/requirements.txt ipykernel && \
        python3 -m ipykernel install --user --name tesi_kernel --display-name 'Python 3 (Tesi Docker)' && \
        jupyter lab --ip=0.0.0.0 --allow-root --no-browser --ServerApp.token='' --ServerApp.password=''
    "

echo "✅ Sessione Notebook terminata."