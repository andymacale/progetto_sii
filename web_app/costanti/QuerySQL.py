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

    VISUALIZZA_PAZIENTI = """
                            select p.id, p.codice_fiscale, p.nome, p.cognome, max(v.data_visita::date) as ultima_visita
                            from pazienti p
                            left join visite v on v.paziente_id = p.id
                            join medici m on m.id = p.medico_id
                            join credenziali c on m.credenziali_id = c.id
                            where c.email = %s
                            group by p.id, p.nome, p.cognome
                            order by ultima_visita desc nulls last
                          """
    
    INSERISCI_PAZIENTE = """
                            insert into pazienti(nome, cognome, codice_fiscale, data_di_nascita, altezza, sesso, bcpo, storia_oncologica, medico_id)
                            values (%s, %s, %s, %s, %s, %s, %s, %s,
                            (select m.id from medici m
                            join credenziali c on c.id = m.credenziali_id
                            where c.email = %s));
                         """

    TRANSAZIONE = "select 1"

    LOCK = """
            select 1
            from pazienti
            where codice_fiscale = %s for share
           """

    ANALISI_PAZIENTE = """
                        drop table if exists temp_analisi_paziente;
                        create temporary table temp_analisi_paziente as
                        select v.data_visita,
                               v.tipo,
                               vc.emoglobina,
                               vc.leucociti,
                               vc.piastrine,
                               vc.creatinina,
                               vc.glicemia,
                               vc.saturazione_spo2,
                               vc.ldh,
                               vc.albumia,
                               vc.peso,
                               p.altezza,
                               p.bcpo,
                               p.storia_oncologica    
                        from visite v
                        join visite_cliniche vc on v.id = vc.visita_id
                        join pazienti p on v.paziente_id = p.id
                        where p.codice_fiscale = %s
                       """

    VISUALIZZA_VISITE = """
                            select  data_visita,
                                    tipo,
                                    emoglobina,
                                    leucociti,
                                    piastrine,
                                    creatinina,
                                    glicemia,
                                    saturazione_spo2,
                                    ldh,
                                    albumia,
                                    peso,
                                    altezza,
                                    bcpo,
                                    storia_oncologica
                            from temp_analisi_paziente
                        """

    CHECK_PID = """
                    select p.*
                    from pazienti p
                    join medici m on p.medico_id = m.id
                    join credenziali c on c.id = m.credenziali_id
                    where p.id = %s and c.email = %s
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

