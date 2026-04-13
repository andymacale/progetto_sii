from datetime import datetime
from abc import ABC, abstractmethod
from typing import Optional
from dominio.Medico import Medico
from dominio.Paziente import Paziente


class Visita(ABC):
    
    def __init__(self,  
                paziente: Paziente, 
                medico: Medico, 
                data_visita: datetime, 
                tipo: str,
                ):

        self.paziente = paziente
        self.medico = medico
        self.tipo = tipo
        self.data_visita = data_visita if data_visita is not None else datetime.now()
        
    @abstractmethod
    def get_tipo(self) -> str:
        pass