"""POST /moderate — relay a per-message Twitch moderation action to boneless_couch.

veil holds no platform credentials: it validates and broadcasts the request over
the WS, and the couchd bot (which owns the Twitch token + moderator scopes) does
the work. The cockpit reflects the result via the chat.message.delete /
chat.clear_user events Twitch emits afterwards.
"""

from fastapi import APIRouter, Body, Depends, Header, HTTPException

from ..config import config
from ..constants import MODERATABLE_PLATFORMS, ModAction, WsMessageType
from ..ws_manager import manager

router = APIRouter()


def _verify_secret(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {config['server']['secret']}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid secret")


@router.post("/moderate", dependencies=[Depends(_verify_secret)])
async def moderate(payload: dict = Body(default=None)) -> dict:
    p = payload or {}
    action = p.get("action")
    platform = p.get("platform")

    if action not in tuple(ModAction):
        raise HTTPException(status_code=400, detail="Unknown action")
    if platform not in MODERATABLE_PLATFORMS:
        raise HTTPException(status_code=400, detail="Unsupported platform")

    if action == ModAction.DELETE and not p.get("message_id"):
        raise HTTPException(status_code=400, detail="message_id required")
    if action in (ModAction.BAN, ModAction.TIMEOUT) and not p.get("user_id"):
        raise HTTPException(status_code=400, detail="user_id required")
    if action == ModAction.TIMEOUT and not p.get("duration"):
        raise HTTPException(status_code=400, detail="duration required")

    data = {
        "action": action,
        "platform": platform,
        "user_id": p.get("user_id"),
        "username": p.get("username"),
        "message_id": p.get("message_id"),
        "duration": p.get("duration"),
        "reason": p.get("reason", "via cockpit"),
    }
    await manager.broadcast({"type": WsMessageType.MOD_ACTION_REQUEST, "data": data})
    return {"ok": True, "action": action}
