from fastapi.responses import FileResponse
from fastapi import APIRouter, HTTPException
from app.services.snapshot_service import get_latest_snapshot


router = APIRouter(prefix="/static", tags=["Snapshot"])

# - Wysyła snapshota z kamery
@router.post("/snapshot")
def get_static_snapshot():
    file_path = get_latest_snapshot()
    if file_path:
        return FileResponse(file_path, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail="Snapshot jeszcze nie istnieje.")
