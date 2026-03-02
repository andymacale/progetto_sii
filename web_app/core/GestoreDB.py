import psycopg2
import os
import bcrypt
from psycopg2.extras import RealDictCursor
from dominio.Medico import Medico
from dominio.Credenziali import Credenziali
from datetime import date
from dotenv import load_dotenv, find_dotenv
from core.costanti import CHIAVE
from dominio.Paziente import Paziente

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
                insert into medici(nome, cognome, codice_fiscale, data_di_nascita, sesso, credenziali_id)
                values (%s, %s, %s, %s, %s, (select id from nuovo))
                """

        valori = (
            medico.credenziali.email,
            medico.credenziali.password,
            medico.nome,
            medico.cognome,
            medico.codice_fiscale,
            medico.data_di_nascita,
            medico.sesso
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
            select m.nome, m.cognome, m.sesso, m.data_di_nascita, m.codice_fiscale, c.password
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
                    #return {"nome": record['nome'], "cognome": record['cognome'], "sesso": record['sesso'], "email": email}
                    nuove = Credenziali(email, password_criptata)
                    nuovo = Medico(nome=record['nome'], cognome=record['cognome'], codice_fiscale=record['codice_fiscale'],
                                   sesso=record['sesso'], data_di_nascita=record['data_di_nascita'], credenziali=nuove)
                    return nuovo
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

    def aggiorna_password(self, email: str, nuova: str) -> bool:
        """Sovrascrive la vecchia password con la nuova"""
        connessione = None
        cursore = None

        query = """
            update credenziali set password = %s where email = %s
            """
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (nuova, email))
            connessione.commit()
            return True
        except Exception as e:
            print(f"Errore durante l'aggiornamento password: {e}")
            if connessione:
                connessione.rollback()
            return False
        finally:
            # Chiudi la connessione se e' stata aperta
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()

    def get_segreto_2fa(self, email: str):
        """Recupera il segreto 2FA dell'utente"""
        query = "select segreto_2fa from credenziali where email=%s"
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (email,))
            risultato = cursore.fetchone()
            if not risultato:
                return None
            return risultato['segreto_2fa'] if isinstance(risultato, dict) else risultato[0]
        except Exception as e:
            print(f"Errore recupero 2FA: {e}")
            return None
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()

    def salva_segreto_2fa(self, email: str, segreto: str) -> bool:
        """Salva il segreto 2FA generato nel database"""
        query = "update credenziali set segreto_2fa = %s where email = %s"
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (segreto, email,))
            connessione.commit()
            return True
        except Exception as e:
            print(f"Errore salvataggio 2FA: {e}")
            return False
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()  

    def controlla_esistenza_utente(self, email: str) -> bool:
        query = "select 1 from credenziali where email = %s"
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (email,))
            return cursore.fetchone() is not None
        except: return False
        finally:
            if cursore: 
                cursore.close()
            if connessione:
                connessione.close()

    def reset_totale_account(self, email: str, nuovo_hash: str) -> bool:
        # Questa query fa due cose: cambia la password e CANCELLA il vecchio 2FA (lo mette a null)
        query = "update credenziali set password = %s, segreto_2fa = null where email = %s"
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (nuovo_hash, email))
            connessione.commit()
            return True
        except: return False
        finally:
            if cursore: 
                cursore.close()
            if connessione: 
                connessione.close()

    def get_numero_pazienti(self, email: str):
        """Restituisce il numero di pazienti"""
        query = """
                select count(p.id) as numero_pazienti
                from medici m
                join credenziali c on c.id = m.credenziali_id
                left join pazienti p on m.id = p.medico_id
                where c.email = %s
                """
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (email,))
            risultato = cursore.fetchone()
            return risultato[0] if risultato else 0
        except Exception as e: 
            print(f"Errore conteggio dei pazienti: {e}")
            return 0
        finally:
            if cursore: 
                cursore.close()
            if connessione:
                connessione.close()

    def inserisci_paziente(self, paziente: Paziente):
        query = """
                insert into pazienti(nome, cognome, codice_fiscale, data_di_nascita, peso, sesso, medico_id)
                values (%s, %s, %s, %s, %s, %s,
                (select m.id from medici m
                join credenziali c on c.id = m.credenziali_id
                where c.email = %s));
                """
        valori = (
            paziente.nome,
            paziente.cognome,
            paziente.codice_fiscale,
            paziente.data_di_nascita,
            paziente.peso,
            paziente.sesso,
            paziente.medico.credenziali.email
        )
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, valori)
            connessione.commit()
            print(f"Paziente {paziente.nome} {paziente.cognome} inserito con successo!")
            return True
        except psycopg2.IntegrityError as e:
            if connessione:
                connessione.rollback()
            print(f"Errore di integrita': {e}")
            return False
        except Exception as e:
            if connessione:
                connessione.rollback()
            return False
        finally:
            if cursore: 
                cursore.close()
            if connessione: 
                connessione.close()

    def get_preferenza_sessione(self, email):
        query = "select preferenza_sessione from credenziali where email = %s"
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (email,))
            risultato = cursore.fetchone()
            if risultato and risultato[0]:
                return risultato
            return "Sempre"
        except:
            return "Sempre"
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()

    def aggiorna_preferenza_sessione(self, email, nuova):
        query = "update credenziali set preferenza_sessione = %s where email = %s"
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (nuova, email,))
            connessione.commit()
            return True
        except Exception as e:
            print(f"Errore aggiornamento preferenza sessione: {e}")
            return False
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close() 

    def salva_token_sessione(self, email, token, scadenza):
        query = "update credenziali set token_sessione = %s, scadenza_token = %s where email = %s"
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (token, scadenza, email,))
            connessione.commit()
            return True
        except Exception as e:
            print(f"Errore salvataggio token sessione: {e}")
            return False
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()

    def elimina_token_sessione(self, email):
        query = "update credenziali set token_sessione = null, scadenza_token = null where email = %s"
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(query, (email,))
            connessione.commit()
            return True
        except Exception as e:
            print(f"Errore eliminazione preferenza sessione: {e}")
            return False
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()

    def verifica_token_sessione(self, token):
        query = """
                select m.nome, m.cognome, m.codice_fiscale, m.sesso, m.data_di_nascita,
                   c.email, c.password, c.scadenza_token
                from credenziali c
                join medici m on c.id = m.credenziali_id
                where c.token_sessione = %s
                """
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor(cursor_factory=RealDictCursor)
            cursore.execute(query, (token,))
            record = cursore.fetchone()
            if record:
                credenziali_medico = Credenziali(record['email'], record['password'])
                medico = Medico(nome=record['nome'], cognome=record['cognome'], 
                                codice_fiscale=record['codice_fiscale'], sesso=record['sesso'], 
                                data_di_nascita=record['data_di_nascita'], credenziali=credenziali_medico)
                return {
                    'medico': medico,
                    'scadenza': record['scadenza_token']
                }
            return None
        except:
            return None
        finally:
            if cursore:
                cursore.close()
            if connessione:
                connessione.close()
        

