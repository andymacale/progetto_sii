from dominio.Medico import Medico
from datetime import date

class Paziente:

    def __init__(self, 
                 nome: str, 
                 cognome: str, 
                 peso: float, 
                 sesso:str, 
                 data_di_nascita: date, 
                 codice_fiscale: str, 
                 altezza: int,
                 medico: Medico,
                 bcpo = False,
                 storia_oncologica = False):

        self.nome = nome
        self.cognome = cognome
        self.peso = peso
        self.data_di_nascita = data_di_nascita
        self.codice_fiscale = codice_fiscale
        self.sesso = sesso
        self.altezza = altezza
        self.bcpo = bcpo
        self.storia_oncologica = storia_oncologica
        self.medico = medico