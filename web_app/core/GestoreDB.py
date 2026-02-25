import psycopg2
import os
import bcrypt
from psycopg2.extras import RealDictCursor
from dominio.Medico import Medico
from dominio.Credenziali import Credenziali
from datetime import date
from dotenv import load_dotenv, find_dotenv

CHIAVE = 'utf-8'

class GestoreDB:
    
    def __init__(self):
        """Parametri per collegarti al DBMS"""
        path = find_dotenv()
        load_dotenv(path)
        
        self.parametri = {
            "host": os.getenv("DB_HOST", "localhost"),
            "dbname": os.getenv("DB_NAME", "medical"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD")
        }

        if not self.parametri["password"]:
            print("Errore nel caricamento della password")

    def _get_connessione(self):
        """Apertura della connessione, solo quando devo interrogare il DB"""
        return psycopg2.connect(**self.parametri)
    
    def inserisci_medico(self, medico: Medico):
        """Inserimento delle credenziali di un medico"""
        query = """
                with nuovo as (
	                insert into credenziali(email, password) values (%s, %s)
	                returning id 
                )
                insert into medici(nome, cognome, codice_fiscale, data_di_nascita, credenziali_id)
                values (%s, %s, %s, %s, (select id from nuovo))
                """

        password_bytes = medico.credenziali.password.encode(CHIAVE)
        sale = bcrypt.gensalt() # Genera un "salt" casuale per sicurezza extra
        password = bcrypt.hashpw(password_bytes, sale).decode(CHIAVE)
        
        valori = (
            medico.credenziali.email,
            password,
            medico.nome,
            medico.cognome,
            medico.codice_fiscale,
            medico.data_di_nascita
        )

        connessione = None
        cursore = None

        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, valori)
            connessione.commit()
            print(f"Medico {medico.nome} {medico.cognome} inserito con successo!")
            return True
        except psycopg2.IntegrityError as e:
            if connessione:
                connessione.rollback()
            print(f"Errore di integrita': {e}")
            return False
        except Exception as e:
            if connessione:
                connessione.rollback()
            print(f"Errore generico: {e}")
            return False
        finally:
            # Chiudi la connessione se e' stata aperta
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()

    def verifica_login(self, email: str, password_inserita: str):
        """Verifica del login"""
        connessione = None
        cursore = None

        query = """
            select m.nome, m.cognome, c.password
            from medici m
            join credenziali c on c.id = m.credenziali_id
            where email = %s;
            """

        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor(cursor_factory=RealDictCursor)
            cursore.execute(query, (email,))
            record = cursore.fetchone()
            if record:
                password_criptata = record['password'].encode(CHIAVE)
                if bcrypt.checkpw(password_inserita.encode(CHIAVE), password_criptata):
                    return {"nome": record['nome'], "cognome": record['cognome'], "email": email}
            return None
        except Exception as e:
            print(f"Errore durante il login: {e}")
            return None
        finally:
            # Chiudi la connessione se e' stata aperta
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()


if __name__ == "__main__":
    """Test di apertura della connessione"""
    print("Tentativo di connessione al database in corso...")
    test = GestoreDB()
    try:
        test_connessione = test._get_connessione()
        print("ACCESSO GARANTITO!")
        test_connessione.close()
    except Exception as e:
        print("ACCESSO NEGATO!")
        print(e)

    credenziali_finte = Credenziali(
        email="dott.mario.rossi@ospedale.it", 
        password="password_sicura_123"
    )
    
    import datetime
    # Creiamo un oggetto Medico finto e gli passiamo le credenziali
    medico_finto = Medico(
        nome="Mario",
        cognome="Rossi",
        codice_fiscale="RSSMRA80A01H501Z",
        data_di_nascita=datetime.date(1980, 1, 1), # Anno, Mese, Giorno
        credenziali=credenziali_finte
    )
    
    esito = test.inserisci_medico(medico_finto)
    
    if esito:
        print("Credenziali inserite")