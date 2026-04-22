"""POST /event — receives all events from boneless_couch."""

from fastapi import APIRouter, Depends, Header, HTTPException

from ..config import config
from ..events import Event
from ..media import pick_audio, pick_clip
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
        await manager.broadcast({"type": "chat.message", "data": {**p, "source": "twitch"}})

    elif t == "twitch.chat.message.delete":
        await manager.broadcast({"type": "chat.message.delete", "data": {"message_id": p["message_id"]}})

    elif t == "twitch.chat.clear_user":
        await manager.broadcast({"type": "chat.clear_user", "data": {"username": p["username"]}})

    elif t in ("twitch.sub", "twitch.resub", "twitch.giftsub", "twitch.giftbomb"):
        alert_type = t.split(".", 1)[1]  # "sub", "resub", etc.
        if t == "twitch.giftsub":
            state.last_sub = {"display_name": p.get("recipient_display_name", p.get("recipient_username", ""))}
        elif t == "twitch.giftbomb":
            state.last_sub = {"display_name": p.get("gifter_display_name", p.get("gifter_username", ""))}
        else:
            state.last_sub = {"display_name": p.get("display_name", p.get("username", ""))}
        await _broadcast_viewer_stats()
        await manager.broadcast({"type": "alert.trigger", "data": _alert_data(alert_type, p)})

    elif t == "twitch.bits":
        state.last_bits = {"display_name": p.get("display_name", p.get("username", "")), "bits": p.get("bits", 0)}
        await _broadcast_viewer_stats()
        await manager.broadcast({"type": "alert.trigger", "data": _alert_data("bits", p)})

    elif t == "twitch.raid":
        state.last_raider = {"display_name": p.get("from_display_name", p.get("from_username", "")), "viewer_count": p.get("viewer_count", 0)}
        await _broadcast_viewer_stats()
        await manager.broadcast({"type": "alert.trigger", "data": _alert_data("raid", p)})

    elif t == "twitch.channel_point_redeem":
        await manager.broadcast({"type": "alert.trigger", "data": _alert_data("channel_point", p)})

    elif t == "twitch.follower":
        state.last_follower = {"display_name": p.get("display_name", p.get("username", ""))}
        await _broadcast_viewer_stats()
        await manager.broadcast({"type": "alert.trigger", "data": _alert_data("follower", p)})

    elif t == "modqueue.pending":
        state.pending_messages[p["message_id"]] = p
        await manager.broadcast({"type": "modqueue.pending", "data": p})

    elif t == "modqueue.resolved":
        state.pending_messages.pop(p.get("message_id", ""), None)
        await manager.broadcast({"type": "modqueue.resolved", "data": p})

    elif t == "modqueue.update":
        mid = p.get("message_id", "")
        if mid in state.pending_messages:
            state.pending_messages[mid]["hold_sources"] = p.get("hold_sources", [])
        await manager.broadcast({"type": "modqueue.update", "data": p})

    elif t == "stream.stats.bootstrap":
        state.last_follower = p.get("last_follower", state.last_follower)
        state.last_raider = p.get("last_raider", state.last_raider)
        state.last_bits = p.get("last_bits", state.last_bits)
        state.last_sub = p.get("recent_subs", [{}])[0] if p.get("recent_subs") else state.last_sub
        state.recent_subs = p.get("recent_subs", [])
        state.longest_subs = p.get("longest_subs", [])
        await manager.broadcast({"type": "viewer_stats.bootstrap", "data": p})

    elif t == "emotes.update":
        state.emote_map = p.get("emote_map", {})
        await manager.broadcast({"type": "emotes.update", "data": state.emote_map})

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


async def _broadcast_viewer_stats() -> None:
    await manager.broadcast({"type": "viewer_stats.update", "data": {
        "last_follower": state.last_follower,
        "last_sub": state.last_sub,
        "last_raider": state.last_raider,
        "last_bits": state.last_bits,
    }})


async def _push_discord_voice() -> None:
    await manager.broadcast({"type": "discord.voice.update", "data": {"members": state.discord_members}})


def _alert_data(alert_type: str, payload: dict) -> dict:
    data: dict = {"alert_type": alert_type, **payload}
    if clip_url := pick_clip(alert_type):
        data["clip_url"] = clip_url
    if audio_url := pick_audio(alert_type):
        data["audio_url"] = audio_url
    return data
