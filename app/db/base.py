from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Import all models here for Alembic
from app.models.user import User
from app.models.invoice import Invoice

__all__ = ["Base", "User", "Invoice"]
