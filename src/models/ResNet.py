import torch.nn as nn
import torchvision.models as models

class ResNet(nn.Module):
    
    def __init__(self, num_classi=5):
        """
            Costruttore della rete neurale che classifica i quattro casi (NEGATIVO, A RISCHIO, PRIMARIO E METASTATICO)
        """
        super(ResNet, self).__init__()
        self.resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT) # definizione della resnet
        self.resnet.conv1 = nn.Conv2d(1, 64, kernel_size=7, stride=2, padding=3, bias=False) # selezione della convoluzione
        num_ftrs = self.resnet.fc.in_features
        self.resnet.fc = nn.Linear(num_ftrs, num_classi) # esecuzione

    def forward(self, x):
        """
            Esecuzione della rete neurale
        """
        return self.resnet(x)