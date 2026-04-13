import os
import sys
import torch
import joblib
import json
import numpy as np
import streamlit as st
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd

cartella_corrente = os.path.dirname(os.path.abspath(__file__))         
cartella_app = os.path.abspath(os.path.join(cartella_corrente, ".."))   
cartella_radice = os.path.abspath(os.path.join(cartella_app, ".."))     

if cartella_radice not in sys.path:
    sys.path.insert(0, cartella_radice) 
if cartella_app not in sys.path:
    sys.path.insert(0, cartella_app)

from costanti.Home import Home
from dominio.Paziente import Paziente
from dominio.Visita import Visita
from dominio.ValutazioneClinica import ValutazioneClinica
from models_saved.Mimic_LSTM import Mimic_LSTM

class MotoreIA:

    @staticmethod
    @st.cache_resource
    def carica_risorse():
        """Carica i modelli di IA"""
        try:
            percorso_config = os.path.join(Home.MODELLI, "model_config_v2.json")
            percorso_scaler = os.path.join(Home.MODELLI, "scaler_sequences.joblib")
            percorso_pesi = os.path.join(Home.MODELLI, "mimic_lstm_model_final_055.pth")
            
            if os.path.exists(percorso_config):
                with open(percorso_config, "r") as file:
                    config = json.load(file)
            else:
                config = {"sequence_length": 5, "seq_input_size": 12, "static_input_size": 6, "hidden_size": 64}
                
            seq_dim = config.get("seq_input_size", 12)
            stat_dim = config.get("static_input_size", 6)
            hid_dim = config.get("hidden_size", 64)
            
            modello = Mimic_LSTM(
                seq_input_size=seq_dim, 
                static_input_size=stat_dim, 
                hidden_size=hid_dim
            )
            
            if os.path.exists(percorso_pesi):
                modello.load_state_dict(torch.load(percorso_pesi, map_location=torch.device('cpu')))
                modello.eval()
            else:
                raise FileNotFoundError(f"File pesi non trovato: {percorso_pesi}")
            
            if os.path.exists(percorso_scaler):
                scaler_obj = joblib.load(percorso_scaler)
            else:
                raise FileNotFoundError(f"File scaler non trovato: {percorso_scaler}")
            
            return config, modello, scaler_obj
            
        except Exception as e:
            print(f"Errore critico caricamento IA: {e}")
            return None, None, None

    @staticmethod
    def prepara_dati(visite: list, paziente: Paziente, scaler_seq, config):
        """Trasforma gli oggetti con quelli compatibili con il modello IA"""
        seq_dim = config.get("seq_input_size", 12)
        stat_dim = config.get("static_input_size", 6)
        max_seq_len = config.get("sequence_length", 5)

        oggi = datetime.today()
        data_di_nascita = paziente.data_di_nascita
        eta_attuale = oggi.year - data_di_nascita.year
        if (oggi.month, oggi.day) < (data_di_nascita.month, data_di_nascita.day):
            eta_attuale -= 1
        
        valori_spo2 = [float(val.saturazione) for val in visite if val.saturazione and val.saturazione > 0]
        valori_ldh = [float(val.ldh) for val in visite if val.ldh and val.ldh > 0]
        valori_alb = [float(val.albumina) for val in visite if val.albumina and val.albumina > 0]

        avg_spo2 = sum(valori_spo2) / float(len(valori_spo2)) if valori_spo2 else 98.0
        avg_ldh = sum(valori_ldh) / float(len(valori_ldh)) if valori_ldh else 200.0
        avg_alb =sum(valori_alb) / float(len(valori_alb)) if valori_alb else 4.0

        dati_statici = [
            1.0 if paziente.bcpo else 0.0,
            1.0 if paziente.storia_oncologica else 0.0,
            avg_spo2,
            avg_ldh,
            avg_alb,
            float(eta_attuale)
        ][:stat_dim] 

        tensor_static = torch.tensor(dati_statici, dtype=torch.float32).unsqueeze(0)

        dati_per_scaler = []
        maschere_seq = []

        for visita in visite:

            altezza_m = float(paziente.altezza / 100.0) if paziente.altezza and paziente.altezza > 0 else 1.75
            bmi = float(visita.peso) / (altezza_m ** 2) if visita.peso else 25.0

            campi_clinici = [
                    float(visita.emoglobina) if visita.emoglobina else 0.0,
                    float(visita.leucociti) if visita.leucociti else 0.0,
                    float(visita.piastrine) if visita.piastrine else 0.0,
                    float(visita.creatinina) if visita.creatinina else 0.0,
                    float(visita.glicemia) if visita.glicemia else 0.0,
                    float(bmi)
            ]

            maschere_riga = [1.0 if x > 0 else 0.0 for x in campi_clinici]
            maschere_seq.append(maschere_riga)

            riga_10_colonne = campi_clinici + dati_statici[:4]
            dati_per_scaler.append(riga_10_colonne)

        dati_input_np = np.array(dati_per_scaler)
        nomi_colonne_training = scaler_seq.feature_names_in_ 
        df_per_scaler = pd.DataFrame(dati_input_np, columns=nomi_colonne_training)

        dati_scalati_10 = scaler_seq.transform(df_per_scaler)

        valori_temporali_scalati = dati_scalati_10[:, :6]
        dati_finali_12 = np.hstack((valori_temporali_scalati, np.array(maschere_seq)))

        
        lunghezza_effettiva = min(len(dati_finali_12), max_seq_len)
        tensor_lengths = torch.tensor([lunghezza_effettiva], dtype=torch.int64)

        if len(dati_finali_12) < max_seq_len:
            # Post-padding con zeri
            padding = np.zeros((max_seq_len - len(dati_finali_12), seq_dim))
            sequenza_finale = np.vstack((dati_finali_12, padding))
        else:
            # Truncating (prendiamo le ultime N visite)
            sequenza_finale = dati_finali_12[-max_seq_len:]

        # Tensore finale pronto per il modello
        tensor_seq = torch.tensor(sequenza_finale, dtype=torch.float32).unsqueeze(0) 

        return tensor_seq, tensor_lengths, tensor_static

    @staticmethod
    def esegui_inferenza(modello, tensor_seq, tensor_lengths, tensor_static):
        """
            Esegue la predizione in avanti (Forward Pass).
            Restituisce la probabilità (0-100%) e la classe predetta.
        """
        try:
            with torch.no_grad():
                output_raw = modello(tensor_seq, tensor_lengths, tensor_static)
                probabilita = torch.sigmoid(output_raw).item()
                
            return probabilita
        except Exception as e:
            print(f"Errore durante l'inferenza: {e}")
            return None

    @staticmethod
    def calcola_shap_grafico(modello, tensor_seq, tensor_lengths, tensor_static, feature_names):
        """
        Genera un grafico a barre per l'interpretabilità dei parametri clinici.
        """
        try:
            indice_ultima = tensor_lengths.item() - 1
            
            valori_da_mostrare = tensor_seq[0, indice_ultima, :6].numpy() 

            
            fig, ax = plt.subplots(figsize=(5, 3))
            y_pos = np.arange(len(feature_names))
            
            ax.barh(y_pos, valori_da_mostrare, align='center', color='skyblue', edgecolor='navy')
            
            ax.set_yticks(y_pos, labels=feature_names)
            ax.invert_yaxis()  
            ax.set_xlabel('Impatto relativo (Valore Scalato)')
            ax.set_title("Contributo Parametri Ultima Visita")
            
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Errore generazione grafico: {e}")
            return None




if __name__ == "__main__":
    config, modello, scaler_seq = MotoreIA.carica_risorse()

    if modello:
        print("Risorse caricate. Test inferenza dummy in corso...")
        
        # Test shape prese dal config JSON
        s_dim = config.get("seq_input_size", 12)
        st_dim = config.get("static_input_size", 6)
        
        t_seq = torch.rand(1, 5, s_dim, dtype=torch.float32)
        t_len = torch.tensor([5], dtype=torch.int64)
        t_stat = torch.rand(1, st_dim, dtype=torch.float32)
        
        prob = MotoreIA.esegui_inferenza(modello, t_seq, t_len, t_stat)
        
        if prob is not None:
            print(f"TEST 100% SUPERATO! Probabilità calcolata: {prob*100:.2f}%")
        else:
            print("Errore in fase di inferenza.")
    else:
       print("Errore in fase di caricamento delle risorse.") 