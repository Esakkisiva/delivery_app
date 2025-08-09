import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from config import settings
# Load environment variables from .env file
# load_dotenv()

# DATABASE_URL from settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
