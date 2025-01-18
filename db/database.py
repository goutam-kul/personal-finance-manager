import sys
import os 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.models import engine, Base

# SQLAlchemy ORM SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
