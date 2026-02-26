import smtplib
import os
import random
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

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

        corpo = f"""
        <html>
            <body style="font-family: sans-serif; text-align: center;">
                <h2 style="color: #007BFF;">Sicurezza MedVision AI</h2>
                <p>Abbiamo ricevuto una richiesta di accesso o recupero per il tuo account.</p>
                <div style="background: #f4f4f4; padding: 20px; border-radius: 10px; display: inline-block;">
                    <span style="font-size: 32px; font-weight: bold; letter-spacing: 10px; color: #333;">{codice}</span>
                </div>
                <p style="margin-top: 20px; color: #777;">Il codice scadrà tra pochi minuti. Non condividerlo con nessuno.</p>
            </body>
        </html>
        """
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