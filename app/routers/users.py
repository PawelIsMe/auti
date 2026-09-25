from fastapi import APIRouter, status, HTTPException, Response
from fastapi.params import Depends
from app.schemas.auth_model import UserProfileResponse, PasswordChangeRequest, GeminiKeyUpdateRequest, \
    InfoForAIUpdateRequest, DateOfBirthUpdateRequest
from app.security.jwt_token import get_current_user
from app.models.user_db import User
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth_service import verify_password, hash_password
from app.models.user_db import UserSession, InviteCode
from app.services.ai_service import delete_session

router = APIRouter(prefix="/users", tags=["Authentication"])

# Zwraca dane o zalogowanym użytkowniku
@router.get("/me", response_model=UserProfileResponse)
def get_user_info(current_user = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  """Delete the authenticated account and its refresh sessions."""
  delete_session(current_user.username)
  db.query(UserSession).filter(UserSession.user_id == current_user.id).delete(synchronize_session=False)
  # Keep invite records valid while removing the creator foreign key.
  db.query(InviteCode).filter(InviteCode.created_by == current_user.id).update(
      {InviteCode.created_by: None}, synchronize_session=False)
  db.delete(current_user)
  db.commit()
  return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/me/date-of-birth", status_code=status.HTTP_200_OK)
def update_date_of_birth(payload: DateOfBirthUpdateRequest,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
  """Update the authenticated user's date of birth (YYYY-MM-DD)."""
  from datetime import date
  try:
    normalized_date = date.fromisoformat(payload.date_of_birth).isoformat()
  except ValueError as exc:
    raise HTTPException(status_code=422, detail="Data musi być w formacie YYYY-MM-DD.") from exc
  current_user.date_of_birth = normalized_date
  db.commit()
  return {"status": "ok", "date_of_birth": normalized_date}

# Endpointy do zmiany ustawien profilu:
# 1. ZMIANA HASŁA
@router.put("/me/password", status_code=status.HTTP_200_OK)
def change_password(payload: PasswordChangeRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  """Zmiana hasła zalogowanego użytkownika z weryfikacją starego hasła."""
  if not verify_password(payload.old_password, current_user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Stare hasło jest niepoprawne.",
    )

  current_user.hashed_password = hash_password(payload.new_password)
  db.commit()

  return {"status": "ok", "message": "Hasło zostało pomyślnie zmienione."}


# 2. ZMIANA GEMINI API KEY
@router.put("/me/gemini-key", status_code=status.HTTP_200_OK)
def update_gemini_key(payload: GeminiKeyUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  """Aktualizuje indywidualny klucz API Gemini zalogowanego użytkownika."""
  current_user.gemini_api_key = payload.gemini_api_key
  db.commit()

  return {
      "status": "ok",
      "message": "Klucz Gemini API został pomyślnie zaktualizowany.",
  }


# 3. ZMIANA INFORMACJI DLA AI
@router.put("/me/info-for-ai", status_code=status.HTTP_200_OK)
def update_info_for_ai(payload: InfoForAIUpdateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
  """Aktualizuje kontekst/informacje przekazywane do asystenta AI dla zalogowanego użytkownika."""
  current_user.info_for_ai = payload.info_for_ai
  db.commit()

  return {
      "status": "ok",
      "message": "Informacje dla AI zostały pomyślnie zaktualizowane.",
  }
