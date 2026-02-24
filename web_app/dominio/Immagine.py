class Immagine:
    
    def __init__(self, nome: str, parametri: dict, tipo: str, dati_grezzi=None):
        self.nome = nome
        self.parametri = parametri
        self.tipo = tipo
        self.dati_grezzi = dati_grezzi