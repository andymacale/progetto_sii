from typing import Optional
from dominio.Medico import Medico
from dominio.Paziente import Paziente
from dominio.Visita import Visita
from datetime import datetime

class ValutazioneClinica(Visita):

    def __init__(self,
                 paziente: Paziente,
                 medico: Medico,
                 data_visita: datetime, 
                 tipo: str,
                 peso: float,
                 emoglobina: Optional[float] = None,
                 leucociti: Optional[float] = None,
                 piastrine: Optional[float] = None,
                 creatinina: Optional[float] = None,
                 glicemia: Optional[float] = None,
                 saturazione: Optional[float] = None,
                 ldh: Optional[float] = None,
                 albumina: Optional[float] = None
                 ):
        
        super().__init__(paziente=paziente, medico=medico, data_visita=data_visita, tipo=tipo)
        self.peso = peso
        self.emoglobina = emoglobina
        self.leucociti = leucociti
        self.piastrine = piastrine
        self.creatinina = creatinina
        self.glicemia = glicemia
        self.saturazione = saturazione
        self.ldh = ldh
        self.albumina = albumina

    def get_tipo(self) -> str:
        return "clinica"
