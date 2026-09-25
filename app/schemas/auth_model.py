from pydantic import BaseModel, Field
from typing import Optional


# ==========[ ZAPYTANIA DO KLIENTA ]==========
# Rejestracja Pierwszego Administratora
class FirstSetupRequest(BaseModel):
  username: str
  password: str
  preferred_name: str
  date_of_birth: str
  gemini_api_key: Optional[str] = None  # TODO pole obowiazkowe przy rejestracji
  info_for_ai: Optional[str] = None

# Rejestracja Zwykłego Użytkownika (wymaga invite_code)
class UserRegisterRequest(FirstSetupRequest):
  invite_code: str

# Login dla kazdego uzytkownika
class LoginRequest(BaseModel):
  username: str
  password: str
  remember_me: bool = False  # Domyślnie opcja jest wyłączona


# ==========[ ODPOWIEDZI DO KLIENTA ]==========
# Dane zwracane o użytkowniku -> /users/me oraz /admin/users
class UserProfileResponse(BaseModel):
  id: int
  username: str
  role: str
  preferred_name: str
  date_of_birth: str
  gemini_api_key: Optional[str] = None
  info_for_ai: Optional[str] = None

  class Config:
    from_attributes = True


# Generowany Kod Zaproszenia
class InviteResponse(BaseModel):
    code: str
    is_used: bool


# ==========[ ZMIANA PROFILU ]==========
# --- ZMIANA HASŁA ---
class PasswordChangeRequest(BaseModel):
  old_password: str
  new_password: str = Field(..., min_length=6)


# --- ZMIANA GEMINI API KEY ---
class GeminiKeyUpdateRequest(BaseModel):
  gemini_api_key: Optional[str] = None


# --- ZMIANA INFORMACJI DLA AI ---
class InfoForAIUpdateRequest(BaseModel):
  info_for_ai: Optional[str] = None


class DateOfBirthUpdateRequest(BaseModel):
  date_of_birth: str = Field(..., min_length=1, max_length=10, description="Data urodzenia w formacie YYYY-MM-DD")


# --- ZMIANA ROLI (ADMIN ONLY) ---
class RoleUpdateRequest(BaseModel):
  role: str = Field(
      ..., description="Nowa rola użytkownika: 'admin' lub 'user'"
  )

# ==========[ TOKENY ]==========
# TODO osobny plik
# Model danych wyjściowych (zwracany po udanym logowaniu)
class TokenResponse(BaseModel):
  access_token: str
  refresh_token: Optional[str] = (
    None  # Zwracany TYLKO gdy remember_me = True
  )
  token_type: str = "bearer"

class RefreshTokenRequest(BaseModel):
  refresh_token: str
