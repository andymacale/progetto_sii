import os

class Home:   
    MEDICAL_HOME = os.environ.get("MEDICAL_HOME")
    GRAFICA = os.path.join(MEDICAL_HOME, "web_app", "grafica")
    DATASET = os.path.join(MEDICAL_HOME, "data")
