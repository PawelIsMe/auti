from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user_db import User
from app.schemas.auth_model import FirstSetupRequest, TokenResponse
from app.services.auth_service import hash_password
from app.security.jwt_token import create_access_token
from app.logger import logger

router = APIRouter(prefix="/setup", tags=["Setup"])

# Sprawdza czy system jest w trybie Pierwszej Konfiguracji
@router.get("/status")
def check_setup_status(db: Session = Depends(get_db)):
    has_users = db.query(User).first() is not None
    return {"is_initialized": has_users}


# Endpoint dla PIERWSZEGO konta w systemie (Automatycznie daje Admina)
@router.post("/first", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def first_setup(payload: FirstSetupRequest, db: Session = Depends(get_db)):
    if db.query(User).first() is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pierwsza konfiguracja została już wykonana. Użyj rejestracji z kodem."
        )

    admin_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role="admin",  # Przypisujemy rolę Admina!
        preferred_name=payload.preferred_name,
        date_of_birth=payload.date_of_birth,
        gemini_api_key=payload.gemini_api_key,
        info_for_ai=payload.info_for_ai
    )

    db.add(admin_user)
    db.commit()

    token = create_access_token(data={"sub": admin_user.username})
    return TokenResponse(access_token=token, token_type="bearer")