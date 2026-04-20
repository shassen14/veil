from fastapi import APIRouter

from ..state import state
from ..ws_manager import manager

router = APIRouter()


@router.get("/status")
async def get_status() -> dict:
    return {
        "scene": state.scene,
        "chat_visible": state.chat_visible,
        "chat_sources": state.chat_sources,
        "discord_members": state.discord_members,
        "ws_connections": manager.count,
    }
