from typing import Any

from fastapi import APIRouter, Body

from ..media import pick_audio, pick_clip
from ..state import state
from ..ws_manager import manager

router = APIRouter()


@router.post("/alert/{alert_type}")
async def fire_alert(
    alert_type: str,
    payload: dict[str, Any] | None = Body(default=None),
) -> dict:
    data: dict = {"alert_type": alert_type, **(payload or {})}
    if clip_url := pick_clip(alert_type):
        data["clip_url"] = clip_url
    if state.alerts_audio_enabled:
        if audio_url := pick_audio(alert_type):
            data["audio_url"] = audio_url
    await manager.broadcast({"type": "alert.trigger", "data": data})
    return {"ok": True, "alert_type": alert_type}


@router.post("/alerts/on")
async def alerts_on() -> dict:
    state.alerts_enabled = True
    await manager.broadcast({"type": "alerts.toggle", "data": {"enabled": True}})
    return {"ok": True, "enabled": True}


@router.post("/alerts/off")
async def alerts_off() -> dict:
    state.alerts_enabled = False
    await manager.broadcast({"type": "alerts.toggle", "data": {"enabled": False}})
    return {"ok": True, "enabled": False}


@router.post("/alerts/audio/on")
async def alerts_audio_on() -> dict:
    state.alerts_audio_enabled = True
    await manager.broadcast({"type": "alerts.audio.toggle", "data": {"enabled": True}})
    return {"ok": True, "audio_enabled": True}


@router.post("/alerts/audio/off")
async def alerts_audio_off() -> dict:
    state.alerts_audio_enabled = False
    await manager.broadcast({"type": "alerts.audio.toggle", "data": {"enabled": False}})
    return {"ok": True, "audio_enabled": False}


@router.post("/alerts/queue/clear")
async def clear_queue() -> dict:
    await manager.broadcast({"type": "alerts.queue.clear"})
    return {"ok": True}
