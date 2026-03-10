import torch
import numpy as np

class DiagnosiIntegrata:

    def __init__(self, visiva, clinica, device='cuda'):
        """
            Sistema di Fusione della pipeline visiva (UNet e ResNet) e di XGBoost
        """
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.modello_visivo = visiva.to(self.device)
        self.modello_clinico = clinica
        self.classi = ["NEGATIVO", "A RISCHIO", "PRIMARIO", "METASTATICO"]

    def diagnosi(self, immagine, dati_clinici, peso_immagine=0.7, peso_clinica=0.3):
        """
            Esegue la fusione pesata: 
            Pr_finale = (Pr_immagine * peso_immagine) + (Pr_clinica * peso_clinica)
        """
        self.modello_visivo.eval()
        with torch.no_grad():
            img_tensor = immagine.to(self.device).unsqueeze(0) # batch size 1
            logits, maschera = self.modello_visivo(img_tensor)
            pr_immagine = torch.softmax(logits, dim=1).cpu().numpy()[0]
        pr_clinica = self.modello_clinico.predict(dati_clinici)
        pr_finale = (pr_immagine * peso_immagine) + (pr_clinica * peso_clinica)
        indice_predizione = np.argmax(pr_finale)
        return {
            "diagnosi": self.classi[indice_predizione],
            "confidenza": pr_finale[indice_predizione],
            "distribuzione": dict(zip(self.classi, pr_finale)),
            "maschera": maschera.cpu().numpy()[0][0]
        }