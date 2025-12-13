import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Railway injects DATABASE_URL automatically
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # fallback for local development only
    DATABASE_URL = "postgresql://postgres:postgres@db:5432/namebingo"

# Railway Postgres requires SSL unless disabled
if "railway" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
