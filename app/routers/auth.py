from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.schemas.auth_model import TokenResponse, LoginRequest, RefreshTokenRequest
from app.services.ai_service import delete_session
from app.services.auth_service import verify_password
from app.security.jwt_token import create_access_token, create_refresh_token
from app.security.jwt_token import get_current_user, revoke_token
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth_model import UserRegisterRequest
from app.models.user_db import User, InviteCode, UserSession
from app.services.auth_service import hash_password
from datetime import datetime, timezone, timedelta


router = APIRouter(prefix="/auth", tags=["Authentication"])
security_scheme = HTTPBearer()


# - Zwraca token jesli login i haslo sa poprawne
@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()

    # 2. Weryfikujemy istnienie użytkownika oraz poprawne hasło
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Błędny login lub hasło.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generujemy token JWT
    access_token = create_access_token(data={"sub": user.username})

    refresh_token_val = None

    # B. WARUNEK: Jeśli użytkownik ZAZNACZYŁ "Nie wylogowuj mnie"
    if payload.remember_me:
        refresh_token_val = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=30)

        # Zapisujemy Refresh Token w bazie SQL
        session_entry = UserSession(
            user_id=user.id, refresh_token=refresh_token_val, expires_at=expires_at
        )
        db.add(session_entry)
        db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_val,
        token_type="bearer",
    )

# - Tworzenie konta
# Endpoint dla ZWYKŁYCH użytkowników (Wymaga aktywnego Kodu Zaproszenia)
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)

    # 1. Weryfikacja unikalności nazwy użytkownika
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Użytkownik o tym loginie już istnieje.")

    # 2. Weryfikacja kodu zaproszenia
    invite = db.query(InviteCode).filter(
        InviteCode.code == payload.invite_code,
        InviteCode.is_used == False,
        InviteCode.expires_at > now
    ).first()

    if not invite:
        raise HTTPException(status_code=400, detail="Nieprawidłowy lub wykorzystany kod zaproszenia.")

    # 3. Rejestracja nowego konta z rolą "user"
    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role="user",
        preferred_name=payload.preferred_name,
        date_of_birth=payload.date_of_birth,
        gemini_api_key=payload.gemini_api_key,
        info_for_ai=payload.info_for_ai
    )

    # Oznaczamy kod jako użyty
    invite.is_used = True

    db.add(new_user)
    db.commit()

    token = create_access_token(data={"sub": new_user.username})
    return TokenResponse(access_token=token, token_type="bearer")

@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  # 1. Czyszczenie sesji w pamięci RAM (np. historii czatu AI podpiętej pod ten JWT)
  delete_session(current_user.username)
  revoke_token(credentials.credentials, db)

  # 2. Kasujemy Refresh Token z bazy SQL (żeby nie dało się go użyć ponownie)
  db.query(UserSession).filter(UserSession.user_id == current_user.id).delete(synchronize_session=False)
  db.commit()

  # 2. Zwracamy potwerdzenie do klienta
  return {
      "message": (
          f"Użytkownik '{current_user.username}' został pomyślnie wylogowany."
      )
  }

# 2. ENDPOINT ODŚWIEŻANIA TOKENA (/auth/refresh)
@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
  """Wymienia ważny Refresh Token z bazy na nowy Access Token."""
  # Szukamy sesji w bazie danych SQL
  session_entry = (
      db.query(UserSession)
      .filter(UserSession.refresh_token == payload.refresh_token)
      .first()
  )

  if not session_entry:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Nieprawidłowy Refresh Token.",
    )

  # Sprawdzamy czy Refresh Token w bazie nie wygasł
  now = datetime.now(timezone.utc)
  if session_entry.expires_at.tzinfo is None:
    session_expires = session_entry.expires_at.replace(tzinfo=timezone.utc)
  else:
    session_expires = session_entry.expires_at

  if now >= session_expires:
    db.delete(session_entry)
    db.commit()
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Refresh Token wygasł. Zaloguj się ponownie.",
    )

  # Pobieramy użytkownika
  user = db.query(User).filter(User.id == session_entry.user_id).first()

  # Wydajemy nowy krótki Access Token na kolejne 15 minut!
  if user is None:
    db.delete(session_entry)
    db.commit()
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Użytkownik nie istnieje.")

  # Rotate refresh token so a previously used token cannot be replayed.
  rotated_refresh_token = create_refresh_token()
  session_entry.refresh_token = rotated_refresh_token
  session_entry.expires_at = now + timedelta(days=30)
  db.commit()

  new_access_token = create_access_token(data={"sub": user.username})

  return TokenResponse(
      access_token=new_access_token,
      refresh_token=rotated_refresh_token,
      token_type="bearer",
  )
