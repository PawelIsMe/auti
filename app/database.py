from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Tworzy plik bazy danych 'autidb.db' w katalogu 'data/'
SQLALCHEMY_DATABASE_URL = "sqlite:///./data/autidb.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency do pobierania sesji bazy danych w endpointach FastAPI
def get_db():
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()