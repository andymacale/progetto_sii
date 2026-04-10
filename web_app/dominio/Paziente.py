from dominio.Medico import Medico
from datetime import date

class Paziente:

    def __init__(self, 
                 nome: str, 
                 cognome: str, 
                 altezza: int, 
                 sesso:str, 
                 data_di_nascita: date, 
                 codice_fiscale: str, 
                 bcpo: bool,
                 storia_oncologica: bool,
                 medico: Medico,
                 ):

        self.nome = nome
        self.cognome = cognome
        self.altezza = altezza
        self.data_di_nascita = data_di_nascita
        self.codice_fiscale = codice_fiscale
        self.sesso = sesso
        self.bcpo = bcpo
        self.storia_oncologica = storia_oncologica
        self.medico = medico