import smtplib
import os
import random
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from core.costanti import CHIAVE

load_dotenv()

class EmailService:
    def __init__(self):
        self.mittente = os.getenv("EMAIL_SISTEMA")
        self.password = os.getenv("PASSWORD_APP_EMAIL")
        self.server_smtp = "smtp.gmail.com"
        self.porta = 587

    def genera_otp(self):
        return str(random.randint(100000, 999999))

    def invia_otp(self, destinatario, codice):
        if not self.mittente or not self.password:
            print("Errore: Credenziali email mancanti nel file .env")
            return False

        msg = MIMEMultipart()
        msg['From'] = self.mittente
        msg['To'] = destinatario
        msg['Subject'] = f"{codice} è il tuo codice di verifica MedVision"

        try:
            cartella_core = os.path.dirname(os.path.abspath(__file__))
            cartella_root = os.path.dirname(cartella_core)
            path = os.path.join(cartella_root, "grafica", "email.html")
            with open(path, "r", encoding=CHIAVE) as file:
                template_html = file.read()
            corpo = template_html.format(codice=codice)
        except Exception as e:
            print("Errore nel caricamento dell'HTML")
            corpo = f"Il tuo codice è: {codice}"

        msg.attach(MIMEText(corpo, 'html'))

        try:
            server = smtplib.SMTP(self.server_smtp, self.porta)
            server.starttls()
            server.login(self.mittente, self.password)
            server.send_message(msg)
            server.quit()
            return True
        except Exception as e:
            print(f"Errore invio email: {e}")
            return False