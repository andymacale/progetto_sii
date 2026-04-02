#!/bin/bash
echo "📓 Avvio JUPYTER (Cartella locale)..."

sudo docker run --gpus all -d --rm \
    --name tesi_notebook \
    --ipc=host \
    -p 8888:8888 \
    -v "$(pwd):/workspace" \
    nvcr.io/nvidia/pytorch:25.02-py3 \
    bash -c "pip install -r /workspace/requirements.txt && jupyter lab --ip=0.0.0.0 --allow-root --no-browser"

if [ $? -eq 0 ]; then
    echo "✅ Notebook partito in background!"
else
    echo "❌ Errore nell'avvio del Notebook."
fi