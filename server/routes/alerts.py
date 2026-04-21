from fastapi import APIRouter

from ..media import pick_audio, pick_clip
from ..ws_manager import manager

router = APIRouter()


@router.post("/alert/{alert_type}")
async def fire_alert(alert_type: str) -> dict:
    data: dict = {"alert_type": alert_type}
    if clip_url := pick_clip(alert_type):
        data["clip_url"] = clip_url
    if audio_url := pick_audio(alert_type):
        data["audio_url"] = audio_url
    await manager.broadcast({"type": "alert.trigger", "data": data})
    return {"ok": True, "alert_type": alert_type}
