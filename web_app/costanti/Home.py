import os

class Home:   
    MEDICAL_HOME = os.environ.get("MEDICAL_HOME")
    GRAFICA = os.path.join("grafica")
    DATASET = os.path.join("data")
    MODELLI = os.path.join(MEDICAL_HOME, "models_saved")
    
