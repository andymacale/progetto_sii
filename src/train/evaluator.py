import torch
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from tqdm.auto import tqdm

class Evaluator:
    def __init__(self, nome_classi):
        self.classi = nome_classi
        # Palette per i colori del grafico di confidenza
        colori_base = ["#2ecc71", "#f1c40f", "#3498db", "#e67e22", "#e74c3c", "#9b59b6", "#34495e"]
        self.palette = {
            classe: colori_base[i % len(colori_base)] 
            for i, classe in enumerate(self.classi)
        }

    def evaluate_model(self, model, loader):
        """
        Esegue l'inferenza e restituisce un DataFrame pronto per il plot integrato.
        """
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        model.eval()
        
        reali, predizioni, confidenze_v = [], [], []
        
        print(f"Avvio valutazione su {device}...")
        with torch.no_grad():
            for batch in tqdm(loader):
                images = batch[0].to(device)
                labels = batch[1]
                
                outputs = model(images)
                
                # Gestione dell'output se è una tupla (es. ResNet con aux logits)
                if isinstance(outputs, tuple):
                    outputs = outputs[0]
                
                # Calcolo probabilità e confidenza visiva
                probs = torch.softmax(outputs, dim=1)
                conf_v, preds = torch.max(probs, dim=1)
                
                reali.extend(labels.numpy())
                predizioni.extend(preds.cpu().numpy())
                confidenze_v.extend(conf_v.cpu().numpy())
                
        # Creazione del DataFrame con mappatura nomi classi
        df = pd.DataFrame({
            'reale': [self.classi[r] for r in reali],
            'pred': [self.classi[p] for p in predizioni],
            'conf_v': confidenze_v,
            'conf_c': [0.5] * len(reali), # Placeholder per XGBoost (Scenario A)
            'corretta': np.array(reali) == np.array(predizioni)
        })
        return df

    def plot_scenario_performance(self, res_df, titolo, nome_file):
        """
        Genera Matrice di Confusione e Scatterplot Confidenza
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        fig.suptitle(f"Analisi performance integrata: {titolo}", fontsize=20, fontweight='bold', y=1.05)
        
        # 1. Matrice di Confusione
        confusione = confusion_matrix(res_df['reale'], res_df['pred'], labels=self.classi)
        sns.heatmap(confusione, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=self.classi, yticklabels=self.classi, ax=ax1,
                    cbar_kws={'label': 'Numero di Pazienti'})
        ax1.set_title('Matrice di Confusione', fontsize=16, pad=15)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Scatterplot Confidenza
        sns.scatterplot(
            data=res_df, x='conf_v', y='conf_c', 
            hue='reale', style='corretta', ax=ax2,
            palette=self.palette, markers={True: "o", False: "X"}, 
            s=120, alpha=0.7
        )
        ax2.axline((0, 0), slope=1, color='black', linestyle='--', alpha=0.4)
        ax2.set_title('Confidenza: Visione vs Clinica', fontsize=16, pad=15)
        ax2.set_xlabel('Confidenza Ramo Visivo (ResNet)', fontsize=12)
        ax2.set_ylabel('Confidenza Ramo Clinico (XGBoost)', fontsize=12)
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Classi")
        
        plt.tight_layout()
        plt.savefig(f"{nome_file}_performance.png", dpi=300, bbox_inches='tight')
        plt.show()

