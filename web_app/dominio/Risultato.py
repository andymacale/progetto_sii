from typing import Optional
from dominio.Visita import Visita

class Risultato:

    def __init__(self, visita: Visita, tipo_ia: str, probabilita: float, esito: str,
                 shap: Optional[str] = None, grad_cam: Optional[bytes] = None):

        self.visita = visita
        self.tipo_ia = tipo_ia
        self.probabilita = probabilita
        self.esito = esito
        self.shap = shap
        self.grad_cam = grad_cam