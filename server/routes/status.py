from fastapi import APIRouter

from ..config import config as _config
from ..state import state
from ..ws_manager import manager

router = APIRouter()


@router.get("/status")
async def get_status() -> dict:
    return {
        "chat_visible": state.chat_visible,
        "chat_sources": state.chat_sources,
        "discord_members": state.discord_members,
        "ws_connections": manager.count,
    }


@router.get("/config")
async def get_config() -> dict:
    return {k: v for k, v in _config.items() if k != "server"}
