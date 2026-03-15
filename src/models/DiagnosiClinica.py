import xgboost as xgb
import shap
import numpy as np
import pandas as pd

class DiagnosiClinica:

    def __init__(self, model_path=None):
        """
            Costruttore del modello XGBoost
        """
        self.model = xgb.XGBClassifier()
        if model_path:
            self.model.load_model(model_path)
        self.features = ['gender', 'anchor_age', 'ViewPosition', 'los', 'admission_type']
    
    def predict(self, dati_pazienti):
        """
            Per ogni DataFrame, restituisce una probabilità per le 4 classi
        """
        dati = dati_pazienti[self.features]
        probabilita = self.model.predict_proba(dati)
        return probabilita[0]
    
    def get_xia(self, dati_paziente):
        """
            XIA con SHAPE
        """
        explainer = shap.TreeExplainer(self.model)
        values = explainer.shap_values(dati_paziente[self.features])
        return values, explainer.expected_value