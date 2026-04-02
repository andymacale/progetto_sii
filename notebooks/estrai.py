import os
import zipfile
import pandas as pd
import pydicom
import numpy as np
import torch
from PIL import Image
from io import BytesIO
from super_image import EdsrModel, ImageLoader

# --- CONFIGURAZIONE ---
ZIP_PATH = '/media/andy/Samsung/vinbigdata-chest-xray-abnormalities-detection.zip' 
CSV_PATH = '/home/andy/Documenti/Tesi-Magistrale/data/train.csv'        
OUTPUT_DIR = '/home/andy/Documenti/Tesi-Magistrale/data/RX_super'

# Forza l'uso della GPU (RTX 5060)
device = 'cuda' if torch.cuda.is_available() else 'cpu'
print(f"Sistema pronto. Utilizzo: {device}")

# 1. Carichiamo il modello EDSR direttamente in PyTorch
model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=2)
model.to(device)

def run_pytorch_processor():
    os.makedirs(os.path.join(OUTPUT_DIR, 'sani'), exist_ok=True)
    os.makedirs(os.path.join(OUTPUT_DIR, 'malati'), exist_ok=True)

    print("Analisi CSV...")
    df = pd.read_csv(CSV_PATH).drop_duplicates(subset=['image_id'])
    df_sani = df[df['class_name'] == 'No finding'].sample(n=2000, random_state=42)
    df_m = df[df['class_name'].isin(['Nodule/Mass', 'Lung Opacity', 'Pleural effusion'])]
    # Integrazione malati se < 2000... (stessa logica di prima)
    if len(df_m) < 2000:
        extra = df[(df['class_name'] != 'No finding') & (~df['class_name'].isin(['Nodule/Mass', 'Lung Opacity', 'Pleural effusion']))]
        df_m = pd.concat([df_m, extra.sample(n=2000-len(df_m), random_state=42)])
    df_malati = df_m.sample(n=2000, random_state=42)

    mappa_file = {f"train/{r['image_id']}.dicom": 'sani' for _, r in df_sani.iterrows()}
    mappa_file.update({f"train/{r['image_id']}.dicom": 'malati' for _, r in df_malati.iterrows()})
    lista_target = set(mappa_file.keys())

    print(f"Inizio elaborazione PyTorch su {device}...")

    with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
        for percorso_zip in zf.namelist():
            nome = percorso_zip.strip()
            if nome in lista_target:
                classe = mappa_file[nome]
                out_path = os.path.join(OUTPUT_DIR, classe, os.path.basename(nome).replace('.dicom', '.jp2'))

                if os.path.exists(out_path): continue

                try:
                    with zf.open(percorso_zip) as f:
                        dcm = pydicom.dcmread(BytesIO(f.read()))
                        img_array = dcm.pixel_array.astype(float)
                        img_array = (img_array - np.min(img_array)) / (np.max(img_array) - np.min(img_array) + 1e-7) * 255.0
                        img_uint8 = img_array.astype(np.uint8)
                        if getattr(dcm, 'PhotometricInterpretation', '') == "MONOCHROME1":
                            img_uint8 = 255 - img_uint8
                        
                        # Conversione per PyTorch Super Resolution
                        input_image = Image.fromarray(img_uint8).convert('RGB')
                        
                        # Esecuzione Super Resolution
                        inputs = ImageLoader.load_image(input_image)
                        inputs = inputs.to(device)
                        with torch.no_grad():
                            preds = model(inputs)
                        
                        # Salvataggio in JPEG 2000
                        ImageLoader.save_image(preds, out_path) # Super-image salva in PNG di default, ma noi forziamo .jp2 sotto
                        final_img = Image.open(out_path) # Ricarichiamo per conversione lossless
                        final_img.save(out_path, format='JPEG2000', quality_mode='dB', quality_vals=[0])
                        
                        print(f"🚀 Elaborato: {os.path.basename(out_path)}")
                        
                except Exception as e:
                    print(f"Errore su {nome}: {e}")

if __name__ == "__main__":
    run_pytorch_processor()