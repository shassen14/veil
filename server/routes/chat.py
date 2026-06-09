from fastapi import APIRouter, Body, Depends, Header, HTTPException

from ..config import config
from ..constants import WsMessageType
from ..state import state
from ..ws_manager import manager

router = APIRouter()

# Platforms a cockpit message may be routed to. boneless_couch decides what it
# can actually deliver; veil just relays the request.
VALID_TARGETS = ("twitch", "youtube")


def _verify_secret(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {config['server']['secret']}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid secret")


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


@router.post("/chat/send", dependencies=[Depends(_verify_secret)])
async def send_chat(payload: dict = Body(default=None)) -> dict:
    """Relay a streamer-typed message/command out to boneless_couch over the WS.

    veil holds no platform credentials — it broadcasts the request and the
    couchd bots (listening on the same WS as the modqueue) do the sending.
    """
    text = (payload or {}).get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty message")
    targets = [t for t in (payload or {}).get("targets", VALID_TARGETS) if t in VALID_TARGETS]
    if not targets:
        raise HTTPException(status_code=400, detail="No valid targets")
    await manager.broadcast({
        "type": WsMessageType.CHAT_SEND_REQUEST,
        "data": {"text": text, "targets": targets},
    })
    return {"ok": True, "targets": targets}
