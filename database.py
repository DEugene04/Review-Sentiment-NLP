import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("postgresql+psycopg2://macbookpro@localhost:5432/review_intelligence")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)
