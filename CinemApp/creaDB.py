import sqlalchemy
from sqlalchemy import *

# creo l'engine passando il dialect+driver mysql+pymysql in quanto il DBMS utilizzato e' MySql
engine = create_engine('mysql+pymysql://root@localhost', echo=True) # nella parte root e' necessario utilizzare il proprio username seguito da :password se e' presente una password
# il DB viene si chiama cinema e viene creato solamente se non e' gia' presente attraverso l'istruzione nella riga successiva
engine.execute("CREATE DATABASE IF NOT EXISTS cinema")
# viene specificato l'uso di cinema come DB
engine.execute("USE cinema")
# viene creato l'oggetto container MetaData
metadata = MetaData()

# creazione della tabella persone che rappresenta i clienti o gestori 
persone = Table('persone', metadata,
		Column('idPersona', Integer, primary_key=True),
		Column('nome', VARCHAR(50), nullable=False),
		Column('cognome', VARCHAR(50), nullable=False),
		Column('email', VARCHAR(50), nullable=False),
		Column('password', VARCHAR(50), nullable=False),
		Column('conto', Integer, default=50),
		Column('isGestore', Boolean, nullable=False),
		UniqueConstraint('email'),
		)

# creazione della tabella generi che rappresenta i possibili generi usabili per i film
generi = Table('generi', metadata,
		Column('nomeGenere', VARCHAR(50), primary_key=True)
		)

# creazione della tabella film che contiene tutti i film del cinema
film = Table('film', metadata,
		Column('idFilm', Integer, primary_key=True),
		Column('titolo', VARCHAR(50), nullable=False),
		Column('genere', VARCHAR(50), ForeignKey('generi.nomeGenere'), nullable=False),
		Column('durata', Integer, nullable=False),
		CheckConstraint('durata > 0', name='checkDurata'),
		UniqueConstraint('titolo')
		)

# creazione della tabella sale che contiene l'insieme delle sale del cinema
sale = Table('sale', metadata,
		Column('idSala', Integer, primary_key=True),
		Column('nFile', Integer, nullable=False),
		Column('nPostiPerRiga', Integer, nullable=False),
		CheckConstraint('nFile > 0', name='checkFile'),
		CheckConstraint('nPostiPerRiga > 0', name='checkPostiPerRiga')
		)

# creazione della tabella proiezioni per l'insieme delle proiezioni del cinema
proiezioni = Table('proiezioni', metadata,
		Column('idProiezione', Integer, primary_key=True),
		Column('puntFilm', Integer, ForeignKey('film.idFilm'), nullable=False),
		Column('puntSala', Integer, ForeignKey('sale.idSala'), nullable=False),
		Column('prezzo',Integer, nullable=False),
		Column('inizio', DateTime, nullable=False),
		CheckConstraint('prezzo > 0', name='checkPrezzo')
		)

# creazione della tabella biglietti per rappresentare i biglietti associati alle varie proiezioni
biglietti = Table('biglietti', metadata,
		Column('idBiglietto', Integer, primary_key=True),
		Column('puntProiezione', Integer, ForeignKey('proiezioni.idProiezione'), nullable=False),
		Column('fila', Integer, nullable=False),
		Column('numero', Integer, nullable=False),#numero del posto nella fila
		Column('presoDaPersona', Integer, ForeignKey('persone.idPersona'), nullable=True),
		CheckConstraint('fila >= 0', name='checkFila'),
		CheckConstraint('numero >= 0', name='checkNumero')
		)
# indice nei confronti dell'attributo puntFilm della tabella proiezioni
Index('puntFilm', proiezioni.c.puntFilm)
# indice nei confronti dell'attributo idProiezione della tabella proiezioni
Index('proiezione', proiezioni.c.idProiezione)

metadata.create_all(engine) # crea lo schema del BD