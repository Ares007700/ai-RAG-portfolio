#database.py is used to set up the database connection and define the base class for the models. It uses SQLAlchemy to create an engine that connects to a SQLite database file called app.db. The SessionLocal class is used to create new database sessions, and the Base class is used as a base for all the models defined in models.py.

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./app.db"  # creates a file called app.db

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()