from dominio.Medico import Medico
from datetime import date

class Paziente:

    def __init__(self, id: str, nome: str, cognome: str, peso: float, data_di_nascita: date, codice_fiscale: str , medico: Medico):
        self.id = id
        self.nome = nome
        self.cognome = cognome
        self.peso = peso
        self.data_di_nascita = data_di_nascita
        self.codice_fiscale = codice_fiscale
        self.medico = medico