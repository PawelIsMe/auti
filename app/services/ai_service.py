"""Integracja czatu z Gemini dla indywidualnych kluczy użytkowników."""

from typing import Any

from fastapi import HTTPException
from google import genai
from google.genai import types
from google.genai.errors import APIError, ServerError

from app.logger import logger
from app.methods import TOOLS
from app.models.user_db import User


MODEL_NAME = "gemini-3.5-flash-lite"
INVALID_API_KEY_DETAIL = "Nieprawidłowy klucz API Gemini. Ustaw poprawny klucz w profilu."

# Sesja przechowuje też klucz, żeby po jego zmianie nie użyć klienta ze starymi danymi.
ACTIVE_SESSIONS: dict[str, dict[str, Any]] = {}


def create_session(user: User, prompt: str) -> dict[str, str]:
    """Wysyła wiadomość w sesji Gemini użytkownika, tworząc ją w razie potrzeby."""
    username = user.username
    api_key = (user.gemini_api_key or "").strip()
    if not api_key:
        raise HTTPException(status_code=401, detail=INVALID_API_KEY_DETAIL)

    session = ACTIVE_SESSIONS.get(username)
    if session is None or session["api_key"] != api_key:
        # Odrzuć poprzedni czat przy zmianie klucza.
        ACTIVE_SESSIONS.pop(username, None)
        if not verify_gemini_api_key(api_key):
            raise HTTPException(status_code=401, detail=INVALID_API_KEY_DETAIL)

        try:
            client = genai.Client(api_key=api_key)
            chat = client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Masz na imię Auti. "
                        f"Rozmawiasz z użytkownikiem {user.preferred_name}. "
                        "Jesteś zarządcą Smart Home. Wykonuj akcje w domu lub "
                        "odpowiadaj na pytania, używając udostępnionych funkcji. "
                        f"Dodatkowe polecenia użytkownika: {user.info_for_ai or ''}"
                    ),
                    tools=TOOLS,
                    temperature=0.1,
                ),
            )
        except ServerError as exc:
            raise HTTPException(
                status_code=503,
                detail="Serwery Gemini są niedostępne lub przeciążone. Spróbuj ponownie za chwilę.",
            ) from exc
        except APIError as exc:
            logger.error("Nie udało się utworzyć sesji Gemini dla %s: %s", username, exc)
            raise HTTPException(
                status_code=502,
                detail="Wystąpił błąd komunikacji z Gemini API.",
            ) from exc
        session = {"api_key": api_key, "client": client, "chat": chat}
        ACTIVE_SESSIONS[username] = session
        logger.info("Utworzono nową sesję czatu dla '%s'.", username)

    chat = session["chat"]
    try:
        prompt_response = chat.send_message(prompt)
    except ServerError as exc:
        logger.error("Gemini API jest niedostępne dla %s: %s", username, exc)
        raise HTTPException(
            status_code=503,
            detail="Serwery Gemini są niedostępne lub przeciążone. Spróbuj ponownie za chwilę.",
        ) from exc
    except APIError as exc:
        logger.error("Błąd Gemini API dla %s: %s", username, exc)
        raise HTTPException(
            status_code=502,
            detail="Wystąpił błąd komunikacji z Gemini API.",
        ) from exc

    response = {"type": "text", "reply": prompt_response.text or ""}
    called_functions = parse_and_get_last_turn_functions(chat)
    if called_functions:
        logger.info("Wywołane funkcje dla %s: %s", username, called_functions)
        if "take_camera_snapshot" in (
            called_functions if isinstance(called_functions, list) else [called_functions]
        ):
            response.update(type="text/image", img_url="/api/static/snapshot")
    return response


def delete_session(username: str) -> None:
    """Usuwa zapamiętaną sesję czatu użytkownika."""
    if ACTIVE_SESSIONS.pop(username, None) is not None:
        logger.info("Zresetowano sesję czatu dla %s.", username)
    else:
        logger.info("Brak aktywnej sesji do usunięcia dla %s.", username)


def verify_gemini_api_key(api_key: str) -> bool:
    """Sprawdza klucz lekkim wywołaniem listy modeli Gemini."""
    if not api_key or not api_key.strip():
        return False

    try:
        client = genai.Client(api_key=api_key.strip())
        next(iter(client.models.list()), None)
        return True
    except APIError as exc:
        logger.warning("Weryfikacja klucza Gemini nie powiodła się: %s", exc)
    except Exception:
        # Obejmuje m.in. problemy z siecią i błędy inicjalizacji klienta.
        logger.exception("Nie udało się połączyć z Gemini podczas weryfikacji klucza.")
    return False


def parse_and_get_last_turn_functions(chat_obj: Any) -> list[str] | str | None:
    """Zwraca nazwy funkcji wywołanych przez model w ostatniej turze użytkownika."""
    try:
        history = chat_obj.get_history()
        if not history:
            return None

        last_user_index = next(
            (
                index
                for index in range(len(history) - 1, -1, -1)
                if getattr(history[index], "role", None) == "user"
                and not any(
                    getattr(part, "function_response", None) is not None
                    for part in getattr(history[index], "parts", [])
                )
            ),
            None,
        )
        if last_user_index is None:
            return None

        function_names = [
            function_call.name
            for message in history[last_user_index:]
            if getattr(message, "role", None) == "model"
            for part in getattr(message, "parts", [])
            if (function_call := getattr(part, "function_call", None)) is not None
            and getattr(function_call, "name", None)
        ]
        if len(function_names) == 1:
            return function_names[0]
        return function_names or None
    except Exception:
        logger.exception("Nie udało się przeanalizować historii czatu Gemini.")
        return None
