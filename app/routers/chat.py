from fastapi import APIRouter, Depends, status
from app.schemas.chat_model import ChatRequest
from app.security.jwt_token import get_current_user
from app.services.ai_service import create_session, delete_session
from app.models.user_db import User


router = APIRouter(prefix="/chat", tags=["Chat"])


# - Czat uzytkownika z gemini
@router.post("/session")
def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    response = create_session(user=current_user, prompt=request.message)
    return response


# TODO zrobic endpoint który usuwa ostatnią sesję czatu z AI i tworzy nową dla użytkownika.
@router.post("/delete-session", status_code=status.HTTP_200_OK)
def delete_chat_session(current_user: User = Depends(get_current_user)):
    """Wywoływane przez Fluttera przy wejściu do ekranu czatu / uruchomieniu apki."""
    delete_session(current_user.username)
    return {"status": "ok", "message": "Usunieto chat z AI."}