"""POST /modqueue/{id}/approve|reject — streamer moderation decisions."""

from fastapi import APIRouter, Depends, Header, HTTPException

from ..config import config
from ..state import state
from ..ws_manager import manager

router = APIRouter()


def _verify_secret(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {config['server']['secret']}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid secret")


@router.post("/modqueue/{message_id}/approve", dependencies=[Depends(_verify_secret)])
async def approve(message_id: str) -> dict:
    entry = state.pending_messages.pop(message_id, None)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    chat_data = {k: v for k, v in entry.items() if k != "hold_sources"}
    await manager.broadcast({"type": "chat.message", "data": chat_data})
    await manager.broadcast({"type": "modqueue.decision", "data": {
        "message_id": message_id,
        "decision": "approve",
        "platform": entry.get("platform", "twitch"),
    }})
    return {"ok": True}


@router.post("/modqueue/{message_id}/reject", dependencies=[Depends(_verify_secret)])
async def reject(message_id: str) -> dict:
    entry = state.pending_messages.pop(message_id, None)
    if not entry:
        raise HTTPException(status_code=404, detail="Not found")
    await manager.broadcast({"type": "modqueue.decision", "data": {
        "message_id": message_id,
        "decision": "deny",
        "platform": entry.get("platform", "twitch"),
    }})
    return {"ok": True}
