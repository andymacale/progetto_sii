import psycopg2
import os
from psycopg2.extras import RealDictCursor
from dominio.Medico import Medico
from dominio.Credenziali import Credenziali
from datetime import date
from dotenv import load_dotenv, find_dotenv


class GestoreDB:
    
    def __init__(self):
        """Parametri per collegarti al DBMS"""
        path = find_dotenv()
        load_dotenv(path)
        print(f"Path: {path}")
        
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
    
    def inserisci_medico(self, credenziali: Credenziali, medico: Medico):
        """Inserimento delle credenziali di un medico"""
        query = """
                with nuovo as (
	                insert into credenziali(email, password) values (%s, %s)
	                returning id 
                )
                insert into medici(nome, cognome, codice_fiscale, data_di_nascita, credenziali_id)
                values (%s, %s, %s, %s, (select id from nuovo))
                """

        valori = (
            medico.credenziali.email,
            medico.credenziali.password,
            medico.nome,
            medico.cognome,
            medico.codice_fiscale,
            medico.data_di_nascita
        )

        connessione = None

        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, valori)
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
            if connessione:
                cursore.close()
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
