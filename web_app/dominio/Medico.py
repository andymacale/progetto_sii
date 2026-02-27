from dominio.Credenziali import Credenziali
from datetime import date

class Medico:

    def __init__(self, nome: str, cognome: str, codice_fiscale: str, data_di_nascita: date, sesso: str, credenziali: Credenziali):
        self.nome = nome
        self.cognome = cognome
        self.codice_fiscale = codice_fiscale
        self.data_di_nascita = data_di_nascita
        self.credenziali = credenziali
        self.sesso = sesso
    