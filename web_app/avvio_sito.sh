#!/bin/bash
echo "🌐 Avvio STREAMLIT (Modulo Root: app.py)..."

# 1. Verifica che MEDICAL_HOME sia settata
if [ -z "$MEDICAL_HOME" ]; then
    echo "❌ ERRORE: MEDICAL_HOME non è definita."
    exit 1
fi

# 2. Avvio Docker
# -w "/workspace" dice a Docker di posizionarsi esattamente dove c'è app.py
# -e PYTHONPATH="/workspace" assicura che Python trovi tutte le tue sottocartelle
sudo docker run --gpus all -it --rm \
    --name tesi_sito \
    --ipc=host \
    --network="host" \
    --env-file "$MEDICAL_HOME/web_app/.env" \
    -v "$MEDICAL_HOME/web_app:/workspace" \
    -e MEDICAL_HOME="web_app/workspace" \
    -e PYTHONPATH="/workspace" \
    -w "/workspace" \
    nvcr.io/nvidia/pytorch:25.02-py3 \
    bash -c "pip install -r requirements.txt python-dotenv && streamlit run app.py --server.address 0.0.0.0"

# 3. Controllo Esito
if [ $? -eq 0 ]; then
    echo "✅ Sito avviato in background!"
    echo "📂 Workspace mappato su: $MEDICAL_HOME"
    echo "🔗 URL: http://localhost:8501"
    echo "📝 Log: sudo docker logs -f tesi_sito"
else
    echo "❌ Errore critico durante l'avvio del container."
fi