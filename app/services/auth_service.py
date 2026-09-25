from app.models.user_db import User
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
  # return pwd_context.hash(password)
  # Konwertujemy tekst na bajty, generujemy sól i haszujemy
  pwd_bytes = password.encode("utf-8")
  salt = bcrypt.gensalt()
  hashed_pwd = bcrypt.hashpw(pwd_bytes, salt)
  return hashed_pwd.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
  try:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
  except (ValueError, TypeError):
    return False

def create_user(db: Session, user_data):
  new_user = User(preferred_name=user_data.preferred_name, username=user_data.username, hashed_password=hash_password(user_data.password), date_of_birth=user_data.date_of_birth, gemini_api_key=user_data.gemini_api_key, info_for_ai=user_data.info_for_ai)
  db.add(new_user)
  db.commit()
  db.refresh(new_user)
  return new_user


def authenticate_user(db: Session, username: str, password: str):
  user = db.query(User).filter(User.username == username).first()
  if not user or not verify_password(password, user.hashed_password):
    return None
  return user
