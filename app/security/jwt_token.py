from datetime import datetime, timedelta, timezone
import secrets
import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY
from app.database import get_db
from app.models.user_db import User, RevokedAccessToken
# if not SECRET_KEY:
#   raise RuntimeError("Brak AUTI_SECRET_KEY. Ustaw silny, losowy klucz przed uruchomieniem Auti.")

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
  """Create a signed access token with an explicit subject, id and expiry."""
  now = datetime.now(timezone.utc)
  payload = dict(data)
  payload.update({"iat": now, "exp": now + (expires_delta or timedelta(minutes=TOKEN_EXPIRE_MINUTES)),
                  "jti": str(uuid.uuid4()), "type": "access"})
  return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token() -> str:
  return secrets.token_urlsafe(48)


def revoke_token(token: str, db: Session | None = None) -> None:
  """Persist a valid token's revocation when a DB session is provided."""
  if db is None:
    return
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
    jti, exp = payload.get("jti"), payload.get("exp")
    if jti and exp:
      expires_at = datetime.fromtimestamp(exp, timezone.utc)
      if not db.get(RevokedAccessToken, jti):
        db.add(RevokedAccessToken(jti=jti, expires_at=expires_at))
        db.commit()
  except (jwt.PyJWTError, TypeError, ValueError):
    return


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
                     db: Session = Depends(get_db)) -> User:
  exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Niepoprawny lub wygasły token logowania", headers={"WWW-Authenticate": "Bearer"})
  if credentials is None:
    raise exception
  try:
    payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
    username, jti = payload.get("sub"), payload.get("jti")
    if not username or payload.get("type", "access") != "access":
      raise exception
  except jwt.PyJWTError:
    raise exception
  if jti and db.get(RevokedAccessToken, jti):
    raise exception
  user = db.query(User).filter(User.username == username).first()
  if user is None:
    raise exception
  return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
  if current_user.role != "admin":
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                        detail="Brak wystarczających uprawnień (wymagana rola Admin).")
  return current_user
