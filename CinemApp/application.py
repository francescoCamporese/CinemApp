# !/usr/bin/python3
# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy import *

# esecuzione del file inserimento per popolare il database con dei valori di default e import delle varie tabelle
import inserimento
from inserimento import persone, generi, film, sale, proiezioni, biglietti, engine

from flask import Flask
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask import make_response

from flask_login import LoginManager
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required
from flask_login import current_user
from flask_login import logout_user

import datetime
from datetime import timedelta



# esegui con export FLASK_APP=application.py; export FLASK_ENV=development; flask run
app = Flask(__name__)
app._static_folder = 'templates/static'

# configurazione flask-login
app.config['SECRET_KEY'] = 'ubersecret' # cookie firmato dall'app
login_manager = LoginManager()
login_manager.init_app(app) # associo il login_manager creato alla mia app

# gestione degli utenti
class Persona(UserMixin): # classe relativa al cliente/gestore che interagisce con l'app
    def __init__(self, idPersona, nome, cognome, email, password, conto, isGestore): # costruttore
        self.idPersona = idPersona
        self.nome = nome
        self.cognome = cognome
        self.email = email
        self.password = password
        self.conto = conto
        self.isGestore = isGestore

    def get_id(self):
        return self.idPersona

# trasforma un id utente univoco presente nel DB in un'instanza della classe Persona
@login_manager.user_loader
def load_user(persona_id):
    conn = engine.connect()
    rs = conn.execute(select([persone]).where(persone.c.idPersona == persona_id))
    persona = rs.fetchone()
    conn.close()
    return Persona(persona.idPersona, persona.nome, persona.cognome, persona.email, persona.password, persona.conto, persona.isGestore)

# quando l'app riceve una richiesta per la root eseguo la funzione home
@app.route('/')
def home():
    # current_user (dato da flask_login) identifica l'utente attuale
    # se l'utente e' gia' autenticato rimando alla route dell'area riservata
    if current_user.is_authenticated:
        return redirect(url_for('private'))
    else: # altrimenti ritorno il template index.html per l'autenticazione
        return render_template("index.html", cond = 0)

# area riservata
@app.route('/private')
@login_required # richiede autenticazione
def private():
    # se l'utente e' un gestore
    if current_user.isGestore == True:
        conn = engine.connect()
        # result contiene tutte le proiezioni e informazioni sulla sala e il film trasmesso
        result = conn.execute(select([sale.c.idSala,proiezioni.c.idProiezione,proiezioni.c.inizio,film.c.titolo,film.c.durata]).\
                              select_from(sale.join(proiezioni, sale.c.idSala == proiezioni.c.puntSala).join(film,proiezioni.c.puntFilm == film.c.idFilm)))
        listareg = []
        # per ognuno delle proiezioni controllo se essa e' in corso, se si la aggiungo alla listareg
        for i in result:
            inizio = i['inizio']
            # converto il valore in datetime per poterlo confrontare con un altro datetime
            inizio_dt = datetime.datetime.strptime(str(inizio), '%Y-%m-%d %H:%M:%S')
            # la proiezione per essere in corso deve avere una data di inizio minore rispetto all'ora attuale
            if inizio_dt < datetime.datetime.now():
                durata_mioFilm = i['durata']
                # controllo la fine della proiezione sommando la durata del film che viene trasmesso all'inzio della proiezione
                fine_mia_proiezione = inizio_dt + timedelta(minutes = durata_mioFilm)
                # se la fine della proiezione e' maggiore rispetto all'orario attuale e ha una data di inizio minore allora la proiezione e' in corso
                if fine_mia_proiezione > datetime.datetime.now():
                    listareg.append(i)
        # ritorno il template a cui passo il nome e cognome dell'utente corrente da stampare e la lista delle proiezioni in corso
        return render_template("benvenutogestore.html", nome = current_user.nome, cognome = current_user.cognome, lista = listareg)
    else:
        # l'utente non e' un gestore e lo rimando alla pagina benevenutoutente a cui passo nome, cognome e conto dell'utente corrente
        return render_template("benvenutoutente.html", nome = current_user.nome, cognome = current_user.cognome, conto = current_user.conto)

# login
# post = login form con credenziali, get = rimanda alla homepage
@app.route('/login', methods = ['GET', 'POST'])
def login():
    # nel caso in cui la richiesta sia una POST devo controllare se l'utente e' presente o meno nel database
    if request.method == 'POST':
        conn = engine.connect()
        # controllo di chi e' la mail essendo UNIQUE il risultato sara' solo uno 
        rs = conn.execute(select([persone]).where(persone.c.email == (request.form['email']))) 
        rs = rs.fetchone()
        conn.close()
        if rs != None:
            real_password = rs['password']
            if request.form['pass'] == real_password: # accesso riuscito
                utente = persona_by_email(request.form['email']) # creo un'istanza della classe Persona
                login_user(utente) # chiamata a flask-login
                # rimanda all'area riservata
                return redirect(url_for('private'))
            else:
                # rimanda al form iniziale in quanto e' sbagliata la password inserita
                return render_template('index.html', cond = 3)
        else: # rimanda al form iniziale in quanto non esiste la mail inserita
            return render_template('index.html', cond = 3)
    else: # si tratta di una get
        return redirect(url_for('home'))

@app.route('/signup', methods = ['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # 1 account creato, 2 mail gia esistente
        # valori presi dal form 
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email']
        password = request.form['pass']
        conn = engine.connect()
        # controllo se la mail che viene inserita non sia gia' presente nel database
        rs = conn.execute(select([persone.c.email]).where(persone.c.email == email)).fetchone()
        # mail gia' presente torno alla pagina inziale con un messaggio di errore
        if rs != None:
            return render_template("index.html", cond = 2)
        else: # mail non presente posso effettuare l'inserimento in persone con i dati presi dal form
            conn.execute(persone.insert(), [
                         {'nome': nome, 'cognome': cognome, 'email': email, 'password': password, 'isGestore': False}])
            conn.close()
        # rimando alla pagina iniziale con un messaggio per segnalare il corretto inserimento
        return render_template("index.html", cond = 1)
    else: # si tratta di una get
        return render_template("signup.html")

# funzione che data una persona crea una nuova istanza della classe Persona
def persona_by_email(email):
    conn = engine.connect()
    # sulla base dell'email inserita seleziono le informazioni della persona e le uso per creare una nuova istanza della classe Persona
    rs = conn.execute(select([persone]).where(persone.c.email == email))
    user = rs.fetchone()
    conn.close()
    return Persona(user['idPersona'], user['nome'], user['cognome'], user['email'], user['password'], user['conto'], user['isGestore'])

# lista dei film
@app.route('/listafilm', methods = ['GET', 'POST'])
@login_required # richiede autenticazione
def listafilm():
    if current_user.isGestore == True: # la persona e' un gestore quindi puo' accedere alla route
        # condizione per vedere se il film inserito e' gia' presente nel DB o meno
        cond = True
        conn = engine.connect()
        if request.method == 'POST': # se il metodo e' di tipo POST
            # prendo i valori di titolo, genere e durata dal file HTML
            titolo = request.form['titoloFilm']
            genere = request.form.get('dropdownGenere')
            durata = request.form['durataFilm']
            collezione = conn.execute(select([film.c.titolo]).where(film.c.titolo == titolo)) # salvo in collezione tutti i titoli dei film
            singolo = collezione.fetchone()
            if singolo != None or len(titolo) == 0 or len(durata) == 0: # se il film inserito e' presente nella collezione oppure e' vuoto allora non va inserito, ragionamento analogo per la durata
                cond = False # cond viene a messo a false in modo da indicare al file HTML di stampare un messaggio di errore
            else:
                ins = film.insert() # se il film digitato non e' presente nel DB si puo' inserire
                # effettuo l'inserimento di una nuova tupla con i valori passati dal form
                conn.execute(ins, [{'titolo': titolo, 'genere': genere, 'durata': durata}])
        # insieme dei film presenti nel DB ordinati in ordine alfanumerico
        filmreg = conn.execute(select([film]).order_by(film.c.titolo.asc()))
        # insieme dei generi presenti nel DB ordinati in ordine alfanumerico
        generireg = conn.execute(select([generi]).order_by(generi.c.nomeGenere.asc()))
        conn.close()
        # viene ritornato file listafilm.html e vengono passsati filmreg e generireg per essere stampati insieme a una cond per indicare al file HTML la corretta esecuzione
        return render_template("listafilm.html", film = filmreg, generi = generireg, cond = cond)
    else: # la persona non e' gestore
        # viene rimandata a index.html nel caso in cui l'utente non sia gestore
        return render_template("index.html", cond = 0) 

# lista delle proiezioni
@app.route('/proiezioni', methods = ['GET', 'POST'])
@login_required # richiede autenticazione
def listProiezioni():
    if current_user.isGestore == True: # controllo se la persona e' gestore 
        cond = 0
        if request.method == 'POST': # nel caso di POST prendo dal form HTML tutti i valori inseriti
            ''' essendo un inserimento in cui bisogna controllare sia la proiezione precedente che quella successiva e' necessario
            che non avvengano modifiche al DB fino al termine dell inserimento stesso, quindi questa sezione viene racchiusa da una transazione
            con livello di isolamento SERIALIZABLE'''
            with engine.connect().execution_options(isolation_level="SERIALIZABLE") as conn:
                # prendo i valori dal form relativi alla proiezione da inserire 
                titoloFilm = request.form['titoloFilm']
                sala = request.form.get('dropdownSala')
                inizio = request.form['inizio']
                prezzo = request.form['prezzo']
                # inizia la transazione
                trans = conn.begin()
                try:
                    # controllo se il titolo preso dal form e' gia' presente o meno nel DB essendo UNIQUE
                    result = conn.execute(select([film.c.titolo, film.c.durata]).where(film.c.titolo == titoloFilm))
                    singolo = result.fetchone()# prendo l'unico risultato della query
                    inizio = inizio.replace("T", " ") + ":00" # per questioni di compatibilita' converto il formato del date di HTML in modo che sia confrontabile con datetime
                    inizio_dt = datetime.datetime.strptime(str(inizio), '%Y-%m-%d %H:%M:%S') # converto il formato in datetime
                    if inizio_dt < datetime.datetime.now(): # l'inizio della proiezione non puo' essere minore rispetto all orario attuale, se lo e' ritorno un errore impostando il cond a 2
                        cond = 2
                    else:   
                        # non e' possibile inserire una proiezione neanche se il titolo e' vuoto oppure il prezzo del biglietto e' vuoto e ritorno un errore attraverso un cond a 1
                        if singolo == None or len(prezzo) == 0: 
                            cond = 1
                        else:
                            # durata_mioFilm e' il valore della durata del film inserito nel form
                            durata_mioFilm = singolo['durata'] # e' in minuti
                            # calcolo la fine della proiezione attuale andando a sommare alla data di inizio scelta la durata del film stesso espressa in minuti
                            fine_mia_proiezione = inizio_dt + timedelta(minutes = durata_mioFilm)
                            ''' seleziono l'inizio della proiezione precedente a quella inserita e la durata del film ad esso associata, le informazioni si trovano su proiezioni e film quindi eseguo una join
                            tra le due tabelle, nel where controllo che la sala a cui fa riferimento deve essere la sala inserita nel form, in quanto deve essere la proiezione precedente nella stessa sala,
                            e prendo tutte quelle che hanno un inizio minore o uguale rispetto a quella inserita nel form, le ordino in ordine decrescente e prendo la prima in modo che sia la piu' vicina possibile
                            a quella inserita nel form'''
                            s = select([proiezioni.c.inizio, film.c.durata]).select_from(proiezioni.join(film, proiezioni.c.puntFilm == film.c.idFilm)).where(
                                and_(proiezioni.c.puntSala == sala, proiezioni.c.inizio <= inizio)).order_by(proiezioni.c.inizio.desc()).limit(1)
                            rs = conn.execute(s).fetchone()
                            fine_prima = None
                            if rs != None: # se c'e' una proiezione prima della mia sulla base della query precedente
                                # prendo l'inizio della proiezione precedente e la durata del film a esso associato
                                inizio_prima = rs['inizio']
                                inizio_prima_dt = datetime.datetime.strptime(str(inizio_prima), '%Y-%m-%d %H:%M:%S')
                                durata_prima = rs['durata']
                                # calcolo la fine della proiezione precedente trovata andando a sommare all'orario di inizio convertito in datetime la durata del film che essa trasmette espressa in minuti
                                fine_prima = inizio_prima_dt + timedelta(minutes = durata_prima)
                            '''seleziono  l inizio della proiezione successiva nella mia stessa sala inserita nel form, infatti nel where viene selezionata che puntSala deve essere uguale
                            alla sala inserita nel form e devono essere proiezioni il cui orario di inizio deve essere maggiore rispetto all orario inserito nel form, le ordino in maniera crescente e prendo la prima
                            in modo che la proiezione trovata sara' quella immediatamente dopo rispetto all orario del form'''
                            s = select([proiezioni.c.inizio]).where(and_(proiezioni.c.puntSala == sala, proiezioni.c.inizio >= inizio)).\
                                order_by(proiezioni.c.inizio.asc()).limit(1)
                            rs = conn.execute(s).fetchone()
                            inizio_dopo = None
                            if rs != None: # se c'e' una proiezione dopo della mia
                                # se la proiezione prima della mia finisce dopo l'inizio della mia do errore
                                inizio_dopo = rs['inizio']
                            if fine_prima != None: # se esiste una proiezione precedente alla mia
                                if inizio_dt < fine_prima: # la proiezione precedente deve finire prima dell'inizio della mia altrimenti do errore con cond a 2 
                                    cond = 2
                            if inizio_dopo != None: # se esiste una proiezione successiva alla mia
                                # la proiezione seguente deve iniziare dopo della fine della mia
                                # se qualcosa si sovrappone metto cond a 2 e non posso aggiungere la proiezione
                                if inizio_dopo < fine_mia_proiezione:
                                    cond = 2
                            if cond == 0: # posso andare avanti in quanto le condizioni di inserimento sono rispettate
                                # seleziono l'id del film inserito nel form per inserirlo nel DB
                                idFilm = conn.execute(select([film.c.idFilm]).where(film.c.titolo == titoloFilm)).fetchone()['idFilm']
                                ins = proiezioni.insert()
                                # inserisco in proiezioni una nuova proiezione con i valori presi dal form e l id appena calcolato
                                conn.execute(ins, [{'puntFilm': idFilm, 'puntSala': sala, 'inizio': inizio, 'prezzo':prezzo}])
                                # seleziono l'id della proiezione appena aggiunta in modo da poter inserire correttamente i biglietti per quella proiezione
                                puntProiezione = conn.execute(select([proiezioni.c.idProiezione]).where(and_(proiezioni.c.puntSala == sala, proiezioni.c.inizio == inizio))).fetchone()['idProiezione'] 
                                # seleziono i posti per riga e il numero di file della sala inserita nel form in modo da sapere quanti biglietti andare a creare
                                num = conn.execute(select([sale.c.nPostiPerRiga, sale.c.nFile]).where(sale.c.idSala == sala)).fetchone() 
                                # numero delle righe della sala 
                                n_righe = num['nFile']
                                # numero di colonne della sala
                                n_colonne = num['nPostiPerRiga']
                                riga = 0
                                # creo biglietti per ogni posto presente nella sala inserita nel form
                                while riga < n_righe:
                                    colonna = 0
                                    while colonna < n_colonne:
                                        # eseguo l'inserimento
                                        conn.execute(biglietti.insert(), [{'puntProiezione': puntProiezione, 'fila': riga, 'numero': colonna, 'presoDaPersona': None}])
                                        colonna = colonna + 1
                                    riga = riga + 1
                    # se tutto e' andato a buon fine posso andare a fare commit 
                    trans.commit()
                except: # nel caso di eccezione eseguo una rollback
                    trans.rollback()
                    raise
        conn = engine.connect()
        ''' seleziono le proiezioni con il titolo del film, la sala in cui avviene la proiezione, l'inizio della stessa e il costo, di tutte quelle che hannp una data di inizio maggiore rispetto alla data odierna
        e ordinta per titolo in ordine alfanumerico'''
        proiezionireg = conn.execute(select([film.c.titolo, proiezioni.c.puntSala, proiezioni.c.inizio, proiezioni.c.prezzo]).\
                                    select_from(proiezioni.join(film, proiezioni.c.puntFilm == film.c.idFilm)).where(proiezioni.c.inizio > select([func.now()])).\
                                    order_by(proiezioni.c.inizio, film.c.titolo.asc()))
        # seleziono tutte le sale presenti nel DB e le ordino in ordine crescente
        salereg = conn.execute(select([sale]).order_by(sale.c.idSala.asc()))
        conn.close()
        # ritorno proiezioni.html a cui passo proiezionireg e salereg in modo che possa stamparli e cond per indicare se l'aggiunta e' andata o meno a buon fine
        return render_template("proiezioni.html", proiezioni = proiezionireg, sale = salereg, cond = cond)
    else:
        # l'utente non e' gestore
        return render_template("index.html", cond = 0) # cond 0

# lista dei biglietti acquistati
@app.route('/acquistati')
@login_required # richiede l'autenticazione
def acquistati():
    conn = engine.connect()
    '''vengono selezionati il titolo della proiezione, l' inizio della stessa, la sala nella quale viene eseguita, la fila e il numero del biglietto e il prezzo dello stesso di tutti i biglietti
    che sono stati acquistati dall utente corrente ossia dove il campo presoDaPersona indica l id dell utente corrente, e che siano biglietti di proiezioni con un orario di inizio maggiore rispetto a quello attuale, in pratica
    eventuali biglietti scaduti non vengono fatti vedere, ed essi vengono ordinati secondo la data di inizio, il titolo del film,la sala, la fila ed il numero in ordine crescente'''
    bigliettireg = conn.execute(select([film.c.titolo, proiezioni.c.inizio, proiezioni.c.puntSala, biglietti.c.fila, biglietti.c.numero, proiezioni.c.prezzo]).\
                            select_from(proiezioni.join(biglietti, biglietti.c.puntProiezione == proiezioni.c.idProiezione).join(film, proiezioni.c.puntFilm == film.c.idFilm)).\
                            where(and_(biglietti.c.presoDaPersona == current_user.idPersona, proiezioni.c.inizio > select([func.now()]))).\
                            order_by(proiezioni.c.inizio, film.c.titolo, proiezioni.c.puntSala, biglietti.c.fila, biglietti.c.numero.asc()))
    conn.close()
    # ritorno ad acquistati.html bigliettireg che contiene il risultato della query in modo che possa stamparlo
    return render_template("acquistati.html", biglietti = bigliettireg)

# route biglietteria iniziale
@app.route('/biglietteria')
@login_required # e' richiesta l'autenticazione
def biglietteria():
    # viene ritornata una pagina iniziale di biglietteria con cond a 3 per indicare nessun errore
    return render_template("biglietteria.html", cond = 3)

# route a seguito di un cerca
@app.route('/biglietteria_cerca', methods = ['GET','POST'])
@login_required # e' richiesta l'autenticazione
def biglietteria_cerca():
    cond = 0 # di default a 0 indica se la query ha dato o meno risultati
    bigliettireg = None # di default indica i biglietti da stampare nel template HTML
    conn = engine.connect()
    if request.method == 'POST': # se la richesta e' una POST
            # prendo il valore del film cercato dal form
            single_film = request.form['filmCercato']
            ''' ritorno il titolo del film, l inizio della proiezione, la sala della proiezione, la fila, il numero e il prezzo di tutti i biglietti che fanno riferimento ad una proiezione il cui titolo
            del film che essi trasmettono comprende i caratteri che sono stati inseriti nella box relativa al tasto cerca, il cui inizio della proiezione sia successivo all oraio attuale in modo da non visualizzarer
            eventuali biglietti scaduti, ed ordinati secondo l ordine scritto all inizio del commento'''
            bigliettireg = conn.execute(select([film.c.titolo, proiezioni.c.inizio, proiezioni.c.puntSala, biglietti.c.fila, biglietti.c.numero, proiezioni.c.prezzo,biglietti.c.idBiglietto]).\
                                        select_from(proiezioni.join(film, film.c.idFilm == proiezioni.c.puntFilm).join(biglietti, biglietti.c.puntProiezione == proiezioni.c.idProiezione)).\
                                        where(and_(film.c.titolo.like("%" + single_film + "%"), biglietti.c.presoDaPersona == None, proiezioni.c.inizio > select([func.now()]))).\
                                        order_by(proiezioni.c.inizio, film.c.titolo, proiezioni.c.puntSala, biglietti.c.fila, biglietti.c.numero.asc())) # like non e' case sensitive
            # nel caso in cui non ci siano risultati dalla query eseguita ossia ha tornato 0 righe, allora stampo un messaggio attraverso il quale informo che non ci sono biglietti disponibili attraverso l'uso del cond a 1
            if bigliettireg.rowcount == 0:
                cond = 1
    conn.close()
    # ritorno biglietteria.html a cui passo bigliettireg per stampare i biglietti trovati e cond per indicare se ho trovato o meno biglietti
    return render_template("biglietteria.html", biglietti = bigliettireg, cond = cond)
 
# route a seguito dell'acquisto di un biglietto, prende un parametro idB che indica il biglietto comprato 
@app.route('/biglietteria_acquista/<idB>', methods = ['GET','POST'])
@login_required
def biglietteria_acquista(idB):
    cond = 0 # di default a 0
    bigliettireg = None
    if request.method == 'POST': # se la richiesta e' una POST
        '''l acquisto di un biglietto deve essere eseguito in mutua esclusione in quanto e' necessario che non vengano invalidate le tabelle da parte di un altro
        utente e nel caso in cui dovessi avvenire un eccezione e' necessario che venga fatta una rollback per non avere ipotetiche incosistenze come un biglietto assegnato
        a un utente ma non un effettiva modifica del suo conto'''
        with engine.connect().execution_options(isolation_level="SERIALIZABLE") as conn:
            # inizia la transazione
            trans = conn.begin()
            try:
                # seleziono le informazioni del biglietto con id uguale al valore preso dal template HTML
                biglietto = conn.execute(select([biglietti]).where(biglietti.c.idBiglietto == idB)).fetchone()
                # seleziono il prezzo della proiezione a cui il biglietto fa riferimento
                prezzo = conn.execute(select([proiezioni.c.prezzo]).select_from(proiezioni.join(biglietti, proiezioni.c.idProiezione == biglietto['puntProiezione']))).fetchone()['prezzo']
                # seleziono il conto dell' utente collegato in questo momento
                conto = conn.execute(select([persone.c.conto]).where(persone.c.idPersona == current_user.idPersona)).fetchone()['conto']
                # verifico il nuovo conto dell'utente
                nuovoConto = conto - prezzo
                # se il conto a seguito dell'acquisto e' maggiore o uguale a 0 significa che l'utente aveva abbastanza soldi per effettuare l'acquisto
                if nuovoConto >= 0:
                    # modifico la tabella persone andando ad aggiornare il conto dell'utente corrente con il nuovoConto appena calcolato
                    conn.execute(persone.update().values(conto = nuovoConto).where(persone.c.idPersona == current_user.idPersona))
                    # rendo il biglietto occupato
                    conn.execute(biglietti.update().values(presoDaPersona = current_user.idPersona).where(biglietti.c.idBiglietto == idB))
                    # posso fare commit
                    trans.commit()
                    # rimando alla funzione acquistati per visualizzare il corretto acquisto
                    return redirect(url_for('acquistati'))
                else:
                    # posso fare commit
                    trans.commit()
                    # ritorno biglietteria e passo cond a 2 per indicare il fatto che l'utente non avesse abbastanza soldi
                    return render_template("biglietteria.html", biglietti = bigliettireg, cond = 2)
            except:
                # nel caso di eccezione faccio una rollback
                trans.rollback()
                raise
            conn.close()
    # nel caso di una get ritorno bigliettireg a None ossia non stampa niente e cond a 0 per indicare nessun errore
    return render_template("biglietteria.html", biglietti = bigliettireg, cond = cond)

# statistiche relative ai film e proiezioni
@app.route('/statistiche', methods = ['GET','POST'])
@login_required # richiede autenticazione
def statistiche():
    # se l utente collegato e' un gestore
    if current_user.isGestore == True:
        cond = 0 # valore usato per segnalare eventuali errori
        stat = 1 # valore usato per indicare se la ricerca ha prodotto o meno risultati 
        conn = engine.connect()
        # viene stampata la somma del prezzo di tutti i biglietti venduti ossia che hanno la FK presoDaPersona diverso da None, ossia il totale dei ricavi del cinema
        incassireg = conn.execute(select([func.sum(proiezioni.c.prezzo).label('somma')]).select_from(proiezioni.join(biglietti, biglietti.c.puntProiezione == proiezioni.c.idProiezione)).\
                                        where(biglietti.c.presoDaPersona != None)).fetchone()['somma'] 
        # se il metodo e' una POST ossia l utente ha premuto il tasto cerca
        if request.method == 'POST':
            cond = 1 # indico che il metodo e' una POST
            # acquisisco il valore scritto nel form
            single_film = request.form['filmCercato']
            # seleziono l id di tutti i film che hanno nel titolo una parte della stringa inserita dall utente nel cerca
            filmreg = conn.execute(select([film.c.idFilm]).where(film.c.titolo.like("%" + single_film + "%")))
            # inizializzo listareg a vuota che conterra' tutti film che contengono la stringa inserita
            listareg = []
            # per ogni idFilm tornato dalla query
            for i in filmreg:
                # per ogni film, se esso ha delle proiezioni ed esistono dei biglietti venduti ossia presoDaPersona != None, ritorno la somma del prezzo di tutti i biglietti venduti
                result = conn.execute(select([func.sum(proiezioni.c.prezzo).label('sommaIncassi'), film.c.titolo]).\
                                            select_from(proiezioni.join(biglietti, biglietti.c.puntProiezione == proiezioni.c.idProiezione).join(film, film.c.idFilm == proiezioni.c.puntFilm)).\
                                                where(and_(proiezioni.c.puntFilm == i['idFilm'], biglietti.c.presoDaPersona != None)).group_by(film.c.titolo))
                # controllo se la query ha tornato o meno risultati
                temp = result.fetchone()
                if temp != None:
                    # se si metto lo stat a 0 ossia indico che ci sono risultati da stampare e inserisco l'elemento nella lista da passare al template in modo che stampi i risultati calcolati
                    stat = 0
                    listareg.append(temp)
            conn.close()
            # ritorno il template statistiche.html passando la lista dei valori stampati con listareg, gli incassi totali con incassireg e cond e stat per indicare errori e se ci sono risultati o meno
            return render_template('statistiche.html', lista = listareg, incassi = incassireg, cond = cond, stat = stat)
        # nel caso di una get    
        else:   
            # conto il numero di biglietti venduti e gli incassi fatti realizzare dalle ultime 10 proiezioni dalla piu' recente alla meno per tutte quelle proiezioni per le quali e' stato venduto almeno un biglietto           
            primi_diecireg = conn.execute(select([func.count(biglietti.c.idBiglietto).label('nBiglietti'), func.sum(proiezioni.c.prezzo).label('ricavo'), film.c.titolo, proiezioni.c.inizio, proiezioni.c.puntSala]).\
                                        select_from(proiezioni.join(biglietti, biglietti.c.puntProiezione == proiezioni.c.idProiezione).join(film, film.c.idFilm == proiezioni.c.puntFilm)).\
                                        where(biglietti.c.presoDaPersona != None).group_by(proiezioni.c.idProiezione).order_by(proiezioni.c.inizio.desc()).limit(10))
            conn.close()
            # ritorno il template statistiche.html a cui passo incassireg che e' il totale degli incassi e primi_diecireg che sono i risultati relativi alla query precedente e cond per segnalare evenutali errori
            return render_template('statistiche.html', incassi = incassireg, primi_dieci = primi_diecireg, cond = cond)
    else:
        # nel caso in cui l utente non e' gestore
        return render_template('index.html', cond = 0)
# per gestire il logout
@app.route('/logout', methods = ['GET', 'POST'])
@login_required # richiede autenticazione
def logout():
    logout_user() # chiamata a flask-login 
    return redirect(url_for('home')) # rimandiamo alla funzione della home
