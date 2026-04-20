from fastapi import APIRouter

from ..state import state
from ..ws_manager import manager

router = APIRouter()


@router.post("/chat/toggle")
async def toggle_chat() -> dict:
    state.chat_visible = not state.chat_visible
    await manager.broadcast({"type": "overlay.toggle", "data": {"overlay": "chat", "visible": state.chat_visible}})
    return {"ok": True, "visible": state.chat_visible}


@router.post("/chat/source/{platform}")
async def toggle_source(platform: str, enabled: bool = True) -> dict:
    state.chat_sources[platform] = enabled
    await manager.broadcast({"type": "chat.source.toggle", "data": {"platform": platform, "enabled": enabled}})
    return {"ok": True, "platform": platform, "enabled": enabled}
