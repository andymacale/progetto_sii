import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from tqdm.auto import tqdm
from sklearn.metrics import f1_score, accuracy_score, recall_score
import xgboost as xgb
from sklearn.utils.class_weight import compute_sample_weight
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from src.features.RXToraceDataset import RXToraceDataset
from src.models.DiagnosiVisiva import DiagnosiVisiva
from src.models.DiagnosiClinica import DiagnosiClinica

# IMMAGINI #
EPOCHS = 30
BATCH_SIZE = 8
LEARNING_RATE = 5e-6
WEIGHT_DECAY = 1e-5
NUM_WORKER = 2
# CLINICI #
N_ESTIMATORS = 500
LR = 0.01
MAX_DEPTH = 6
VERBOSE = 100

def train_modello_visivo(train_set, validation_set, path, base_tf, aug_tf, pesi, device, use_aug=True, epochs=30):
    tag = "AUG" if use_aug else "NOAUG"
    print(f"\n--- TRAINING MODELLO VISIVO ({tag}) ---")
    checkpoint_path = f"last_checkpoint_{tag.lower()}.pth"
    best_model_path = f"best_model_vision_{tag.lower()}.pth"


    t_aug = aug_tf if use_aug else None
    train_ds = RXToraceDataset(train_set, path, base_tf, t_aug, True)
    val_ds = RXToraceDataset(validation_set, path, base_tf, False)

    # num_workers=4 sfrutta meglio le CPU degli Studio
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True, num_workers=4)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=4)

    model = DiagnosiVisiva().to(device)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    criterion = nn.CrossEntropyLoss(weight=pesi.to(device))
    
    # GradScaler non deprecato per precisione mista
    scaler = torch.amp.GradScaler('cuda') 
    
    best_f1 = 0.0
    start_epoch = 0
    history = {'loss': [], 'f1': [], 'acc': [], 'recall': []}

    if os.path.exists(checkpoint_path):
        print(f"Rilevato checkpoint esistente: {checkpoint_path}. Ripristino in corso...")
        checkpoint = torch.load(checkpoint_path)
        
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scaler.load_state_dict(checkpoint['scaler_state_dict'])
        
        start_epoch = checkpoint['epoch']
        best_f1 = checkpoint.get('best_f1', 0.0)
        history = checkpoint['history'] 
        
        print(f"Ripresa addestramento dall'epoca {start_epoch + 1}. Miglior F1 precedente: {best_f1:.4f}")

    # Logica di ripristino per gestire il timeout di 4 ore
    if os.path.exists(checkpoint_path):
        checkpoint = torch.load(checkpoint_path)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict']) # Corretto qui
        start_epoch = checkpoint['epoch']
        print(f"Ripresa addestramento dall'epoca {start_epoch}")

    for epoch in range(start_epoch, epochs):
        model.train()
        running_loss = 0.0
        loop = tqdm(train_loader, desc=f"Epoca {epoch+1}/{epochs}", leave=False)
        
        for img, lbl, mask in loop:
            img, lbl = img.to(device), lbl.to(device)
            optimizer.zero_grad() 

            # Autocast moderno per T4
            with torch.amp.autocast('cuda'):
                logits, _ = model(img)
                loss = criterion(logits, lbl)
            
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            loop.set_postfix(loss=loss.item())

        model.eval()
        all_p, all_l = [], []
        with torch.no_grad():
          for img, lbl, _ in val_loader:
            img, lbl = img.to(device), lbl.to(device)
            logits, _ = model(img)
            all_p.extend(torch.argmax(logits, dim=1).cpu().numpy())
            all_l.extend(lbl.cpu().numpy())

        e_loss = running_loss / len(train_loader)
        acc = accuracy_score(all_l, all_p)
        rec = recall_score(all_l, all_p, average='macro')
        f1 = f1_score(all_l, all_p, average='weighted')
        
        print(f"[{tag}] Ep {epoch+1}: Loss: {e_loss:.4f} | F1: {f1:.4f} | Acc: {acc:.4f} | Rec: {rec:.4f}")
        
        if f1 > best_f1:
           best_f1 = f1
           torch.save(model.state_dict(), f"best_f1_model_vision_{tag.lower()}.pth")
           print(f"Nuovo miglior modello {tag} salvato!")
        
        # Salvataggio persistente su Lightning AI
        torch.save({
            'epoch': epoch + 1,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'scaler_state_dict': scaler.state_dict(),
            'best_f1': best_f1,
            'history': history # Salviamo la history per non perdere i grafici
        }, checkpoint_path)
        print(f"Checkpoint epoca {epoch+1} salvato con successo.")
    
    return model, history

def train_modello_clinico(train_set, validation_set, features):
    """
        Addestramento di XGBoost
    """
    print(f"\n--- TRAINING MODELLO CLINICO ---")

    X_train, y_train = train_set[features], train_set['numero_severita']
    X_val, y_val = validation_set[features], validation_set['numero_severita']

    weights = compute_sample_weight('balanced', y_train)

    xgb_internal = xgb.XGBClassifier(
       n_estimators=N_ESTIMATORS, 
        learning_rate=LR, 
        max_depth=MAX_DEPTH, 
        objective='multi:softprob', 
        num_class=5, 
        random_state=42
    )

    xgb_internal.fit(X_train, y_train, sample_weight=weights, eval_set=[(X_val, y_val)], verbose=VERBOSE)
    diagnosi = DiagnosiClinica()
    diagnosi.model = xgb_internal
    diagnosi.model.save_model("xgb_medical_model.json")
    return diagnosi


