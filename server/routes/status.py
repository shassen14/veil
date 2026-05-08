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
        "alerts_enabled": state.alerts_enabled,
        "alerts_audio_enabled": state.alerts_audio_enabled,
        "current_scene": state.current_scene,
        "last_follower": state.last_follower,
        "last_sub": state.last_sub,
        "last_raider": state.last_raider,
        "last_bits": state.last_bits,
    }


@router.get("/config")
async def get_config() -> dict:
    return {k: v for k, v in _config.items() if k != "server"}
