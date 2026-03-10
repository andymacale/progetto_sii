import torch
import torch.nn as nn
from src.models.UNet import UNet
from src.models.ResNet import ResNet

class DiagnosiVisiva:
    
    def __init__(self):
        """
            Costruttore della UNet e della ResNet combinate in serie
        """
        super(DiagnosiVisiva, self).__init__()
        self.unet = UNet()
        self.resnet = ResNet(num_classi=4)

    def forward(self, x):
        """
            Esecuzione della pipeline:
            1) Caricamento dell'immagine alla UNet che restituisce una maschera
            2) Applicazione della maschera all'immagine originale, restituendo un'immagine pulita
            3) Classificazione dell'immagine pulita con la ResNet
        """
        mask = self.unet(x)
        x_clean = x * mask
        classification = self.resnet(x_clean)
        
        return classification, mask