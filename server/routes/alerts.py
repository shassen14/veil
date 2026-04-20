from fastapi import APIRouter

from ..ws_manager import manager

router = APIRouter()


@router.post("/alert/{alert_type}")
async def fire_alert(alert_type: str) -> dict:
    await manager.broadcast({"type": "alert.trigger", "data": {"alert_type": alert_type}})
    return {"ok": True, "alert_type": alert_type}
