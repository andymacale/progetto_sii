from datetime import datetime
from dominio.ValutazioneClinica import ValutazioneClinica
from typing import Optional

class Referto:

    def __init__(self, 
                 documento: bytes, 
                 clinica: ValutazioneClinica,
                 risultato_clinico: Optional[Risultato] = None,
                 data_referto: Optional[datetime] = None, 
                 note: Optional[datetime] = None):

        self.documento = documento
        self.clinica = clinica
        self.data_referto = data_referto if data_referto is not None else datetime.now()
        self.note = note
        self.risultato_clinico = risultato_clinico