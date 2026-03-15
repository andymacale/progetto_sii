import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix

class Evaluator:

    def __init__(self, nome_classi):
        self.classi = nome_classi
        self.palette = {
            "NEGATIVO": "#2ecc71", 
            "A RISCHIO": "#f1c40f", 
            "TRAUMI": "#3498db",
            "PRIMARIO": "#e67e22", 
            "METASTATICO": "#e74c3c"
        }

    def plot_scenario_performance(self, res_df, titolo, nome_file):
        """
            Genera un unico pannello di matrice di confusione e scatterplot per uno scenario
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
        fig.suptitle(f"Analisi performance integrata: {titolo}", fontsize=20, fontweight='bold', y=1.05)
        confusione = confusion_matrix(res_df['reale'], res_df['pred'], labels=self.classi)
        sns.heatmap(confusione, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=self.classi, yticklabels=self.classi, ax=ax1,
                    cbar_kws={'label': 'Numero di Pazienti'})
        ax1.set_title('Matrice di Confusione', fontsize=16, pad=15)
        ax1.set_xlabel('Predizione Sistema Integrato', fontsize=12)
        ax1.set_ylabel('Ground Truth (Reale)', fontsize=12)
        ax1.tick_params(axis='x', rotation=45)
        sns.scatterplot(
            data=res_df, x='conf_v', y='conf_c', 
            hue='reale', style='corretta', ax=ax2,
            palette=self.palette, markers={True: "o", False: "X"}, 
            s=120, alpha=0.7
        )
        ax2.axline((0, 0), slope=1, color='black', linestyle='--', alpha=0.4, label='Equilibrio Visione/Clinica')
        ax2.set_title('Confidenza: Visione vs Clinica', fontsize=16, pad=15)
        ax2.set_xlabel('Confidenza Ramo Visivo (ResNet)', fontsize=12)
        ax2.set_ylabel('Confidenza Ramo Clinico (XGBoost)', fontsize=12)
        ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left', title="Classi e Correttezza")
        ax2.grid(True, linestyle=':', alpha=0.6)

        plt.tight_layout()
        plt.savefig(f"{nome_file}_performance.png", dpi=300, bbox_inches='tight')
        plt.show()

    def plot_training_history(self, history, titolo, nome_file):
        """
            Genera l'andamento delle metriche
        """
        metrics = ['loss', 'f1', 'acc', 'recall']
        metric_names = ['Loss (CrossEntropy)', 'F1-Score (Weighted)', 'Accuracy', 'Recall (Macro)']
        colors = ['#c0392b', '#2980b9', '#27ae60', '#f39c12']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f"Andamento Metriche - {titolo}", fontsize=18, fontweight='bold', y=0.98)
        axes = axes.flatten()
        
        epoche = range(1, len(history['loss']) + 1)
        
        for ind, (metric, name, color) in enumerate(zip(metrics, metric_names, colors)):
            axes[ind].plot(epoche, history[metric], label=name, color=color, marker='o', linewidth=2)
            axes[ind].set_title(f'Evoluzione {name}', fontsize=14)
            axes[ind].set_xlabel('Epoca')
            axes[ind].set_ylabel('Valore')
            axes[ind].grid(True, linestyle='--', alpha=0.7)
            
            final_val = history[metric][-1]
            axes[ind].annotate(f'{final_val:.4f}', 
                             xy=(epoche[-1], final_val), 
                             xytext=(5, 0), 
                             textcoords='offset points', 
                             fontsize=10, fontweight='bold')
            axes[ind].legend()

        plt.tight_layout(rect=[0, 0.03, 1, 0.95])
        plt.savefig(f"{nome_file}_history.png", dpi=300)
        plt.show()
