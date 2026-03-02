from enum import Enum

class PreferenzaSessione(Enum):
    SEMPRE = "Sempre"
    ORA = "Ora"
    GIORNO = "Giorno"
    SETTIMANA = "Settimana"
    MAI = "Mai"

    @property
    def etichetta_ui(self):
        etichette = {
            "Sempre": "Sempre (ad ogni reload)",
            "Ora": "Ogni ora",
            "Giorno": "Ogni giorno",
            "Settimana": "Ogni settimana",
            "Mai": "Mai (fino al log out)"
        }
        return etichette[self.value]

    @classmethod
    def get_valori_ui(cls):
        return [pref.etichetta_ui for pref in cls]
    
    @classmethod
    def da_etichetta(cls, etichetta):
        for pref in cls:
            if pref.etichetta_ui == etichetta:
                return pref
        return cls.SEMPRE