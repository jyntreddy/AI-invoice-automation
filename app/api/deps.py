from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
