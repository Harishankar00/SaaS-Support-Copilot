import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

# 1. Fetch the Database URL from your .env file
DATABASE_URL = os.getenv("DATABASE_URL")

# 2. Configure the Engine
# NOTE: If you are using Supabase's Transaction Pooler (Port 6543), 
# we use NullPool to let Supabase manage the connections effectively.
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool if ":6543" in (DATABASE_URL or "") else None
)

# 3. Create a Session factory
# This is what generates a new 'talk' session for every API request
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Define the Base class for your models
# All your tables (Users, History) will inherit from this
Base = declarative_base()

# 5. The Dependency: get_db
# This is used in main.py to inject the database session into your routes.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()