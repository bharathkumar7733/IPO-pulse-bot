import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Default to SQLite for local development/testing if no POSTGRES URL provided
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///c:/IPO-BOT/ipo_dev.db"
)

# SQLite requires connect_args check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
