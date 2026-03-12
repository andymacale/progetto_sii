#!/bin/bash

# --- CONFIGURAZIONE GIT LFS PER TESI ---

echo "1. Installazione di git-lfs nel sistema (richiede password sudo)..."
sudo apt update && sudo apt install git-lfs -y

echo "2. Inizializzazione di Git LFS nel repository..."
git lfs install

echo "3. Tracciamento dei file di modelli (.pth)..."
# Questo comando crea/aggiorna il file .gitattributes
git lfs track "*.pth"

echo "4. Aggiunta dei file di configurazione LFS..."
git add .gitattributes

echo "5. Rimozione di eventuali modelli rimasti in cache standard (safe)..."
# A volte git prova a caricare i modelli come file normali anche se c'è LFS.
# Questo comando "pulisce" l'indice per forzare l'uso di LFS.
git rm --cached *.pth 2>/dev/null

echo "6. Aggiunta dei modelli reali..."
# Qui usiamo il percorso dei tuoi file visti nell'immagine
git add best_model_vision_aug.pth best_model_vision_noaug.pth

echo "7. Commit finale..."
git commit -m "Configurato Git LFS e aggiunti modelli pesanti (>100MB)"

echo "-------------------------------------------------------"
echo "SETUP COMPLETATO!"
echo "Ora puoi lanciare: git push origin main"
echo "Nota: Il primo push sarà lento perché deve caricare ~440MB."
echo "-------------------------------------------------------"