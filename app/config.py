# HA_URL = "http://ha2:8123"
# HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjNTkwN2VmYzRiOTU0M2YzYmJkYzFjY2YzNTE4Yjc0ZCIsImlhdCI6MTc5MDI0NzcwMywiZXhwIjoyMTA1NjA3NzAzfQ.JlZZPCEaKrt1jZZz5wJfpX8sDql1H0W-zfxTbSx297w"
# MDNS_NAME = "Auti Server"
# MDNS_IP = "192.168.1.40"
# MDNS_ENABLED = True
# AUTI_PORT = 8000
# SECRET_KEY = "super-tajny-klucz-auti-serwera-dla-ha"
# ALGORITHM = "HS256"
# TOKEN_EXPIRE_MINUTES = 60  # Token będzie ważny przez godzinę


from pathlib import Path
from dotenv import load_dotenv
import os

from app.logger import logger

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


HA_URL = os.getenv("AUTI_HA_URL", "")
HA_TOKEN = os.getenv("AUTI_HA_TOKEN", "")

#MDNS
MDNS_NAME = os.getenv("AUTI_MDNS_NAME", "Auti Server")
MDNS_IP = os.getenv("AUTI_MDNS_IP", "")
MDNS_ENABLED = os.getenv("AUTI_MDNS_ENABLED", "true").lower() not in {"0", "false", "no"}

AUTI_PORT = int(os.getenv("AUTI_PORT", "8000"))

# Ustawienia zabezpieczeń JWT
SECRET_KEY = os.getenv("AUTI_SECRET_KEY", "")


ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60  # Token będzie ważny przez godzinę

# logger.info(f"{HA_URL, HA_TOKEN, MDNS_NAME, MDNS_IP, MDNS_ENABLED, AUTI_PORT, SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_MINUTES}")