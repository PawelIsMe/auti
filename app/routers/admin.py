import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.logger import logger
from app.models.user_db import User, InviteCode, UserSession
from app.schemas.auth_model import InviteResponse, UserProfileResponse, RoleUpdateRequest
from app.security.jwt_token import require_admin
from datetime import datetime, timedelta, timezone
from app.services.ai_service import delete_session



router = APIRouter(prefix="/admin", tags=["Admin Panel"])

# Generowanie jednorazowego kodu zaproszenia
@router.post("/invitations", response_model=InviteResponse)
def generate_code(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    # Generujemy unikalny, krótki kod (np. 8 znaków)
    random_code = str(uuid.uuid4())[:8].upper()
    expire_time = datetime.now(timezone.utc) + timedelta(hours=24)

    new_invite = InviteCode(code=random_code, created_by=admin.id, expires_at=expire_time)
    db.add(new_invite)
    db.commit()

    return InviteResponse(code=random_code, is_used=False)


# Pobieranie listy wszystkich użytkowników
@router.get("/users", response_model=List[UserProfileResponse])
def get_all_users(admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    return db.query(User).all()


# Usuwanie uzytkownika po id
@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
    user_to_delete = db.query(User).filter(User.id == user_id).first()
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Użytkownik nie istnieje.")

    if user_to_delete.id == admin.id:
        raise HTTPException(status_code=400, detail="Nie możesz usunąć własnego konta administratora.")
    logger.info(f"Usunięto konto '{user_to_delete.username}' z bazy danych!")
    delete_session(user_to_delete.username)
    db.query(UserSession).filter(UserSession.user_id == user_to_delete.id).delete(synchronize_session=False)
    db.query(InviteCode).filter(InviteCode.created_by == user_to_delete.id).update(
        {InviteCode.created_by: None}, synchronize_session=False)
    db.delete(user_to_delete)
    db.commit()
    return None

# 4. NADAWANIE / ODEBRANIE UPRAWNIEŃ ADMINISTRATORA (ADMIN ONLY)
@router.put("/users/{user_id}/role", status_code=status.HTTP_200_OK)
def update_user_role(user_id: int, payload: RoleUpdateRequest, admin: User = Depends(require_admin), db: Session = Depends(get_db)):
  """
  Pozwala administratorowi na zmianę roli dowolnego użytkownika (np. nadanie 'admin' lub obniżenie do 'user').
  """
  # Walidacja dozwolonych ról
  if payload.role not in ["admin", "user"]:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Nieprawidłowa rola. Dozwolone wartości to 'admin' lub 'user'.",
    )

  # Szukamy docelowego użytkownika
  target_user = db.query(User).filter(User.id == user_id).first()
  if not target_user:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Użytkownik o podanym ID nie istnieje.",
    )

  # Zabezpieczenie: Admin nie może zabrać uprawnień samemu sobie bezpośrednio
  if target_user.id == admin.id and payload.role != "admin":
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Nie możesz odebrać samemu sobie uprawnień administratora.",
    )

  target_user.role = payload.role
  db.commit()

  return {
      "status": "ok",
      "message": (
          f"Rola użytkownika '{target_user.username}' została zmieniona na"
          f" '{payload.role}'."
      ),
  }
