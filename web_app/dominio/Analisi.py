from dominio.Immagine import Immagine
from dominio.Paziente import Paziente

class Analisi:

    def __init__(self, tipo: str, immagine: Immagine, paziente: Paziente):
        self.tipo = tipo
        self.immagine = immagine
        self.paziente = paziente
        self.esito = None
        self.diagnosi = None
        self.grado_tumore = None
        self.suggerimento_follow_up = None

    def importa_risultati(self, esito: str, diagnosi: str, grado: str, follow_up: str):
        self.esito = esito
        self.diagnosi = diagnosi
        self.grado_tumore = grado
        self.suggerimento_follow_up = follow_up