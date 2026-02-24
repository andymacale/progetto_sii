from dominio.Medico import Medico

class Paziente:

    def __init__(self, id: str, nome: str, cognome: str, peso: float, eta: int, medico: Medico):
        self.id = id
        self.nome = nome
        self.cognome = cognome
        self.peso = peso
        self.eta = eta
        self.medico = medico