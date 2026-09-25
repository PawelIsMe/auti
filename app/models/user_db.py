from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from datetime import datetime, timezone


class User(Base):
  __tablename__ = "users"
  id = Column(Integer, primary_key=True, index=True)
  username = Column(String, unique=True, index=True, nullable=False)
  hashed_password = Column(String, nullable=False)

  # Rola: "admin" lub "user"
  role = Column(String, default="user", nullable=False) # TODO w create_user dodac dla pierwszej konfiguracji

  # Dane profilowe
  preferred_name = Column(String, nullable=False)
  date_of_birth = Column(String, nullable=False)
  gemini_api_key = Column(String, nullable=True)  # TODO zeby bylo wymagane przy tworzeniu konta
  info_for_ai = Column(String, nullable=True)



class InviteCode(Base):
  __tablename__ = "invites"

  id = Column(Integer, primary_key=True, index=True)
  code = Column(String, unique=True, index=True, nullable=False)
  is_used = Column(Boolean, default=False, nullable=False)
  created_by = Column(Integer, ForeignKey("users.id"))
  expires_at = Column(DateTime(timezone=True), nullable=False)


class UserSession(Base):
  __tablename__ = "user_sessions"

  id = Column(Integer, primary_key=True, index=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  refresh_token = Column(String, unique=True, index=True, nullable=False)
  created_at = Column(
      DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
  )
  expires_at = Column(DateTime(timezone=True), nullable=False)


class RevokedAccessToken(Base):
  """Persisted access-token revocations, shared across API workers/restarts."""
  __tablename__ = "revoked_access_tokens"

  jti = Column(String, primary_key=True)
  expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
