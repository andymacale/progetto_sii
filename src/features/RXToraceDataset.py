import os
import torch
from torch.utils.data import Dataset
from PIL import Image

class RXToraceDataset(Dataset):
    def __init__(self, dataframe, cartella, transform_base=None, transform_aug=None):
        """
            Inizializza il dataset:
            dataframe: il train set, validation set e test test filtrati
            cartella: la cartella dove sono memorizzate le immagini
            transform_base: le trasformazione di base (ridimensionamento, e normalizzazione ad un canale)
            transform_aug: le trasformazioni di augmentation (rotazione e traslazione)
        """
        self.df = dataframe.reset_index(drop=True)
        self.cartella = cartella
        self.base = transform_base
        self.aug = transform_aug

    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, index):
        nome = self.df.loc[index, 'path_immagine']
        path = os.path.join(self.cartella, nome)
        immagine = Image.open(path).convert('L') # conversione in scala di grigi
        label = self.df.loc[index, 'numero_severita'] # il target
        paziente_id = self.df.loc[index, 'subject_id']
        # Solo se il numero di severità è 2 ed è il training set si esegue l'augmentation
        if label == 2 and self.aug is not None:
            immagine = self.aug(immagine)
        elif self.base is not None:
            immagine = self.base(immagine)
        label_tensor = torch.tensor(label, dtype=torch.long)
        return immagine, label_tensor, paziente_id