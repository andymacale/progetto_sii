class QuerySQL:
    
    INSERISCI_MEDICO = """
                        with nuovo as (
                            insert into credenziali(email, password) values (%s, %s)
                            returning id 
                        )
                        insert into medici(nome, cognome, codice_fiscale, data_di_nascita, sesso, credenziali_id)
                        values (%s, %s, %s, %s, %s, (select id from nuovo))
                        """
    
    VERIFICA_LOGIN = """
                        select m.nome, m.cognome, m.sesso, m.data_di_nascita, m.codice_fiscale, c.password
                        from medici m
                        join credenziali c on c.id = m.credenziali_id
                        where email = %s;
                    """

    AGGIORNA_PASSWORD = "update credenziali set password = %s where email = %s"

    RECUPERA_SEGRETO = "select segreto_2fa from credenziali where email=%s"

    SALVA_SEGRETO = "update credenziali set segreto_2fa = %s where email = %s"

    ESISTE_UTENTE = "select 1 from credenziali where email = %s"

    RESET_ACCOUNT =  "update credenziali set password = %s, segreto_2fa = null where email = %s"

    NUM_PAZIENTI =  """
                        select count(p.id) as numero_pazienti
                        from medici m
                        join credenziali c on c.id = m.credenziali_id
                        left join pazienti p on m.id = p.medico_id
                        where c.email = %s
                    """
    
    INSERISCI_PAZIENTE = """
                            insert into pazienti(nome, cognome, codice_fiscale, data_di_nascita, peso, sesso, medico_id)
                            values (%s, %s, %s, %s, %s, %s,
                            (select m.id from medici m
                            join credenziali c on c.id = m.credenziali_id
                            where c.email = %s));
                         """
    
    GET_PREFERENZA = "select preferenza_sessione from credenziali where email = %s"

    AGGIORNA_PREFERENZA = "update credenziali set preferenza_sessione = %s where email = %s"

    SALVA_SESSIONE = "update credenziali set token_sessione = %s, scadenza_token = %s where email = %s"

    ELIMINA_SESSIONE = "update credenziali set token_sessione = null, scadenza_token = null where email = %s"

    VERIFICA_SESSIONE = """
                            select m.nome, m.cognome, m.codice_fiscale, m.sesso, m.data_di_nascita,
                            c.email, c.password, c.scadenza_token
                            from credenziali c
                            join medici m on c.id = m.credenziali_id
                            where c.token_sessione = %s
                        """

