from app.config import MDNS_ENABLED, MDNS_NAME, MDNS_IP, AUTI_PORT
from app.routers import auth, chat, snapshot, admin, setup, users
from app.models.user_db import User
from app.database import Base, engine
from app.logger import logger
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from zeroconf.asyncio import AsyncZeroconf
from zeroconf import ServiceInfo
from pathlib import Path
from app import __version__
import os
import socket



def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

# Globalne obiekty Zeroconf
# service_info = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    aiozc = AsyncZeroconf()
    service_info = None
    try:
        if MDNS_ENABLED:
            local_ip = MDNS_IP or get_local_ip()
            service_name = MDNS_NAME
            service_info = ServiceInfo(
                "_auti._tcp.local.",
                f"{service_name}._auti._tcp.local.",
                addresses=[socket.inet_aton(local_ip)],
                port=AUTI_PORT,
                properties={"version": __version__},
            )
            await aiozc.async_register_service(service_info)
    except Exception:
        # Discovery is optional; a broken or unavailable multicast network
        # should not prevent the HTTP server from starting.
        logger.exception("Nie udało się uruchomić usługi mDNS")

    try:
        yield
    finally:
        # Ten kod wykona się ZAWSZE przy zamknięciu aplikacji
        try:
            if service_info is not None:
                await aiozc.async_unregister_service(service_info)
            await aiozc.async_close()
        except Exception:
            pass


def create_application() -> FastAPI:
    # Fast API
    app = FastAPI(title="Auti API", description="REST API for Auti", version=f"{__version__}", lifespan=lifespan)

    # Entry logs
    logger.info("====================")
    logger.info(f"Auti v{__version__}")
    logger.info("====================")


    # Tworzy tabele w bazie danych przy starcie, jeśli jeszcze nie istnieją
    Base.metadata.create_all(bind=engine)

    # Rejestracja routerów
    api_router = APIRouter(prefix="/api")
    api_router.include_router(admin.router)
    api_router.include_router(auth.router)
    api_router.include_router(chat.router)
    api_router.include_router(setup.router)
    api_router.include_router(snapshot.router)
    api_router.include_router(users.router)
    app.include_router(api_router)

    # ===[ FRONTEND ]===
    # 2. Określasz ścieżkę do wygenerowanego folderu dist
    # (Ścieżka wychodzi z miejsca, gdzie leży ten plik do głównego katalogu auti/frontend/dist)
    BASE_DIR = Path(__file__).resolve().parent.parent  # Lub .parent jeśli main.py leży bezpośrednio w auti/
    FRONTEND_DIST = BASE_DIR / "frontend" / "dist"

    if FRONTEND_DIST.exists():
        # Serwowanie zasobów statycznych z wygenerowanego folderu (JS, CSS, obrazki)
        assets_dir = FRONTEND_DIST / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        # Reakcja na wszystkie pozostałe ścieżki i zwracanie index.html
        # (dzięki temu odświeżanie stron w React Routerze np. /login, /chat nie zwróci błędu 404)
        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            # Jeśli zapytanie dotyczy konkretnego pliku z głównego katalogu dist (np. favicon.ico, manifest.json)
            file_path = FRONTEND_DIST / full_path
            if file_path.is_file():
                return FileResponse(file_path)

            # W przeciwnym razie zwróć główny plik aplikacji React
            return FileResponse(FRONTEND_DIST / "index.html")
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:create_application", factory=True, host="0.0.0.0", port=AUTI_PORT, reload=False, log_config=None)
