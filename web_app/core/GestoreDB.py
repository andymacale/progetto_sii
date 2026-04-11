import psycopg2
import os
import bcrypt
from psycopg2.extras import RealDictCursor
from dominio.Medico import Medico
from dominio.Credenziali import Credenziali
from datetime import date
from dotenv import load_dotenv, find_dotenv
from costanti.parametri import CHIAVE
from dominio.Paziente import Paziente
from costanti.QuerySQL import QuerySQL

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
            cursore.execute(QuerySQL.INSERISCI_MEDICO, valori)
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

        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor(cursor_factory=RealDictCursor)
            cursore.execute(QuerySQL.VERIFICA_LOGIN, (email,))
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
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.AGGIORNA_PASSWORD, (nuova, email))
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
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.RECUPERA_SEGRETO, (email,))
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
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.SALVA_SEGRETO, (segreto, email,))
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
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.ESISTE_UTENTE, (email,))
            return cursore.fetchone() is not None
        except: return False
        finally:
            if cursore: 
                cursore.close()
            if connessione:
                connessione.close()

    def reset_totale_account(self, email: str, nuovo_hash: str) -> bool:
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.RESET_ACCOUNT, (nuovo_hash, email))
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
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.NUM_PAZIENTI, (email,))
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

    def get_elenco_pazienti(self, email: str):
        """Restituisce l'elenco dei pazienti per data di ultima visita"""
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.VISUALIZZA_PAZIENTI, (email,))
            pazienti = cursore.fetchall()
            risultati = []
            for paziente in pazienti:
                risultati.append({
                    "id": paziente[0],
                    "codice fiscale": paziente[1],
                    "nome": paziente[2],
                    "cognome": paziente[3],
                    "ultima visita": paziente[4]
                })
            return risultati
        except Exception as e: 
            print(f"Errore visualizzazione dei pazienti: {e}")
            return 0
        finally:
            if cursore: 
                cursore.close()
            if connessione:
                connessione.close()

    def inserisci_paziente(self, paziente: Paziente):
        valori = (
            paziente.nome,
            paziente.cognome,
            paziente.codice_fiscale,
            paziente.data_di_nascita,
            paziente.altezza,
            paziente.sesso,
            paziente.bcpo,
            paziente.storia_oncologica,
            paziente.medico.credenziali.email
        )
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.INSERISCI_PAZIENTE, valori)
            connessione.commit()
            print(f"Paziente {paziente.nome} {paziente.cognome} inserito con successo!")
            return True
        except psycopg2.IntegrityError as e:
            if connessione:
                connessione.rollback()
            print(f"Errore di integrita': {e}")
            return False
        except Exception as e:
            print(f"Errore generico: {e}")
            if connessione:
                connessione.rollback()
            return False
        finally:
            if cursore: 
                cursore.close()
            if connessione: 
                connessione.close()

    def _get_paziente_by_id_and_medico(self, paziente_id: int, medico: Medico):
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor(cursor_factory=RealDictCursor)
            email_medico = medico.credenziali.email
            cursore.execute(QuerySQL.CHECK_PID, (paziente_id, email_medico))
            riga = cursore.fetchone()            
            if riga:
                return Paziente(
                        nome=riga['nome'],
                        cognome=riga['cognome'],
                        codice_fiscale=riga['codice_fiscale'],
                        sesso=riga['sesso'],
                        altezza=riga['altezza'],
                        bcpo=riga['bcpo'],
                        storia_oncologica=riga['storia_oncologica'],
                        data_di_nascita=riga['data_di_nascita'],
                        medico=medico
                    )
            return None
        except Exception as e:
            print(f"Errore nel recupero paziente: {e}")
            return None
        finally:
            if cursore: 
                cursore.close()
            if connessione: 
                connessione.close()

    def get_analisi_paziente(self, cursore_attivo):
        """Restituisce le visite effettuate da quel paziente"""
        try:
            cursore_attivo.execute(QuerySQL.VISUALIZZA_VISITE)
            analisi = cursore_attivo.fetchall()
            risultati = []
            for ris in analisi:
                risultati.append({
                    "data visita": ris[0],
                    "tipo": ris[1],
                    "emoglobina": ris[2],
                    "leucociti": ris[3],
                    "piastrine": ris[4],
                    "creatinina": ris[5],
                    "glicemia": ris[6],
                    "saturazione spo2": ris[7],
                    "ldh": ris[8],
                    "albumia": ris[9],
                    "peso": ris[10],
                    "altezza": ris[11],
                    "bcpo": ris[12],
                    "storia oncologica": ris[13]
                })
            return risultati
        except Exception as e: 
            print(f"Errore visualizzazione delle visite: {e}")
            return 0

    def get_preferenza_sessione(self, email):
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.GET_PREFERENZA, (email,))
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
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.AGGIORNA_PREFERENZA, (nuova, email,))
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
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.SALVA_SESSIONE, (token, scadenza, email,))
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
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor()
            cursore.execute(QuerySQL.ELIMINA_SESSIONE, (email,))
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
        connessione = None
        cursore = None
        try:
            connessione = self._get_connessione()
            cursore = connessione.cursor(cursor_factory=RealDictCursor)
            cursore.execute(QuerySQL.VERIFICA_SESSIONE, (token,))
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
        

