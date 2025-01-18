from sqlalchemy import Column, Integer, String, Float, Date, create_engine
from sqlalchemy.ext.declarative import declarative_base

# Base class for defining models
Base = declarative_base()


# Expense table
class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String, nullable=False)
    date = Column(Date, nullable=False)

# Budget table
class Budget(Base):
    __tablename__ = 'Budget'
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, nullable=False, unique=True)
    limit = Column(Float, nullable=False)
    current_total = Column(Float, default=0.0)

# SQLite Engine
DATABASE_URL = "sqlite:///db/database.db"
engine = create_engine(DATABASE_URL)