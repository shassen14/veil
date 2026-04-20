"""POST /event — receives all events from boneless_couch."""

from fastapi import APIRouter, Depends, Header, HTTPException

from ..config import config
from ..events import Event
from ..state import state
from ..ws_manager import manager

router = APIRouter()


def _verify_secret(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {config['server']['secret']}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid secret")


@router.post("/event", dependencies=[Depends(_verify_secret)])
async def receive_event(event: Event) -> dict:
    await dispatch(event)
    return {"ok": True}


async def dispatch(event: Event) -> None:
    t = event.type
    p = event.payload

    if t == "twitch.chat.message":
        await manager.broadcast({"type": "chat.message", "data": {**p, "platform": "twitch"}})

    elif t in ("twitch.sub", "twitch.resub", "twitch.giftsub", "twitch.giftbomb"):
        alert_type = t.split(".", 1)[1]  # "sub", "resub", etc.
        await manager.broadcast({"type": "alert.trigger", "data": {"alert_type": alert_type, **p}})

    elif t == "twitch.bits":
        await manager.broadcast({"type": "alert.trigger", "data": {"alert_type": "bits", **p}})

    elif t == "twitch.raid":
        await manager.broadcast({"type": "alert.trigger", "data": {"alert_type": "raid", **p}})

    elif t == "twitch.channel_point_redeem":
        await manager.broadcast({"type": "alert.trigger", "data": {"alert_type": "channel_point", **p}})

    elif t == "discord.voice.join":
        member = {
            "user_id": p["user_id"],
            "display_name": p["display_name"],
            "avatar_url": p.get("avatar_url", ""),
            "speaking": False,
            "muted": False,
        }
        if not any(m["user_id"] == member["user_id"] for m in state.discord_members):
            state.discord_members.append(member)
        await _push_discord_voice()

    elif t == "discord.voice.leave":
        state.discord_members = [m for m in state.discord_members if m["user_id"] != p["user_id"]]
        await _push_discord_voice()

    elif t == "discord.voice.speaking":
        for m in state.discord_members:
            if m["user_id"] == p["user_id"]:
                m["speaking"] = p["speaking"]
        await _push_discord_voice()

    elif t == "discord.voice.mute":
        for m in state.discord_members:
            if m["user_id"] == p["user_id"]:
                m["muted"] = p.get("self_mute", False) or p.get("self_deaf", False)
        await _push_discord_voice()


async def _push_discord_voice() -> None:
    await manager.broadcast({"type": "discord.voice.update", "data": {"members": state.discord_members}})
