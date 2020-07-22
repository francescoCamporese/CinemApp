import sqlalchemy
from sqlalchemy import *
# eseguo il file creaDB 
import creaDB
# importo le varie tabelle create
from creaDB import persone,generi,film,sale,proiezioni,biglietti,engine

engine = create_engine('mysql+pymysql://root@localhost/cinema', echo=True)
metadata = MetaData()

conn = engine.connect()#per erogare comandi tramite conn.

# conto il numero di persone presenti nel DB
s= select([func.count(persone.c.idPersona).label('conto')])
result=conn.execute(s)
result=result.fetchone()
# se non sono presenti persone eseguo degli inserimenti
if result['conto'] == 0:
	personeIns = persone.insert()
	conn.execute(personeIns,
		[
			{'nome': 'Stefano', 'cognome': 'Calzavara', 'email': 'stefano.calzavara@gmail.com', 'password': 'Admin_123', 'isGestore': True},
			{'nome': 'Francesco', 'cognome': 'Camporese', 'email': 'francesco.camporese99@gmail.com', 'password': 'User_456', 'isGestore': False}
		])
			
# conto il numero di generi presenti nel DB 
s= select([func.count(generi.c.nomeGenere).label('conto')])
result=conn.execute(s)
result=result.fetchone()
# se non sono presenti generi eseguo degli inserimenti
if result['conto'] == 0:
	generiIns = generi.insert()
	conn.execute(generiIns,
		[
			{'nomeGenere': 'animazione'},
			{'nomeGenere': 'azione'},
			{'nomeGenere': 'drammatico'},
			{'nomeGenere': 'horror'},
			{'nomeGenere': 'storia'}
		])

# conto il numero di film presenti nel DB 
s= select([func.count(film.c.idFilm).label('conto')])
result=conn.execute(s)
result=result.fetchone()
# se non sono presenti film eseguo degli inserimenti
if result['conto'] == 0:
	filmIns = film.insert()
	conn.execute(filmIns,
		[
			{'titolo': 'Avengers: Endgame', 'genere': 'azione', 'durata': '181'},
			{'titolo': 'Fast and Furious', 'genere': 'azione', 'durata': '106'},
			{'titolo': 'Joker', 'genere': 'azione', 'durata': '123'},
			{'titolo': 'Terminator', 'genere': 'azione', 'durata': '107'},
			{'titolo': 'Inside Out', 'genere': 'animazione', 'durata': '94'},
			{'titolo': 'Up', 'genere' :'animazione', 'durata': '96'},
			{'titolo': 'Wall-E', 'genere': 'animazione', 'durata': '98'},
			{'titolo': 'Philadelphia', 'genere': 'drammatico', 'durata': '121'},
			{'titolo': 'The Irishman', 'genere': 'drammatico', 'durata': '209'},
			{'titolo': 'Cattive acque', 'genere': 'storia', 'durata': '126'},
			{'titolo': 'Il discorso del re', 'genere': 'storia', 'durata': '118'},
			{'titolo': 'Via col vento', 'genere': 'storia', 'durata': '238'}
		])

# conto il numero di sale presenti nel DB 
s= select([func.count(sale.c.idSala).label('conto')])
result=conn.execute(s)
result=result.fetchone()
# se non sono presenti sale eseguo degli inserimenti
if result['conto'] == 0:
	saleIns = sale.insert()
	conn.execute(saleIns,
		[
			{'nFile': '5', 'nPostiPerRiga': '10'},
			{'nFile': '6', 'nPostiPerRiga': '12'},
			{'nFile': '7', 'nPostiPerRiga': '14'}
		])

conn.close() # chiusura della connessione