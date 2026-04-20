"""
/test/* endpoints — fire fake events without boneless_couch.
Available any time: off-stream, pre-stream, or during dev.
"""

import time

from fastapi import APIRouter

from ..events import Event
from .ingest import dispatch

router = APIRouter(prefix="/test", tags=["test"])

_PAYLOADS: dict[str, dict] = {
    "sub": {
        "username": "test_viewer", "display_name": "TestViewer",
        "tier": "1000", "is_gift": False,
    },
    "resub": {
        "username": "test_viewer", "display_name": "TestViewer",
        "tier": "1000", "cumulative_months": 6, "streak_months": 3,
        "message": "6 months hype!",
    },
    "giftsub": {
        "gifter_username": "generous_person", "gifter_display_name": "GenerousPerson",
        "recipient_username": "lucky_viewer", "recipient_display_name": "LuckyViewer",
        "tier": "1000", "total_gifted": 5,
    },
    "giftbomb": {
        "gifter_username": "generous_person", "gifter_display_name": "GenerousPerson",
        "count": 10, "tier": "1000",
    },
    "raid": {
        "from_username": "raider_channel", "from_display_name": "RaiderChannel",
        "viewer_count": 42, "profile_image_url": "",
    },
    "bits": {
        "username": "test_viewer", "display_name": "TestViewer",
        "bits": 500, "message": "hype!", "total_bits_given": 2500,
    },
    "channel_point": {
        "username": "test_viewer", "display_name": "TestViewer",
        "reward_id": "test-001", "reward_title": "Hydrate!",
        "reward_cost": 1000, "user_input": "please drink water",
    },
}

_EVENT_TYPE_MAP: dict[str, str] = {
    "sub": "twitch.sub",
    "resub": "twitch.resub",
    "giftsub": "twitch.giftsub",
    "giftbomb": "twitch.giftbomb",
    "raid": "twitch.raid",
    "bits": "twitch.bits",
    "channel_point": "twitch.channel_point_redeem",
}


@router.post("/alert/{alert_type}")
async def test_alert(alert_type: str) -> dict:
    event_type = _EVENT_TYPE_MAP.get(alert_type, f"twitch.{alert_type}")
    payload = _PAYLOADS.get(alert_type, {"username": "test_viewer", "display_name": "TestViewer"})
    await dispatch(Event(type=event_type, ts=time.time(), payload=payload))
    return {"ok": True, "fired": alert_type}


@router.post("/chat")
async def test_chat(message: str = "This is a test chat message!") -> dict:
    await dispatch(Event(type="twitch.chat.message", ts=time.time(), payload={
        "username": "test_viewer",
        "display_name": "TestViewer",
        "message": message,
        "color": "#FF4500",
        "badges": ["subscriber/6"],
        "emotes": [],
        "message_id": "test-msg-001",
        "platform": "twitch",
    }))
    return {"ok": True}


@router.post("/discord/join")
async def test_discord_join(display_name: str = "GuestUser") -> dict:
    await dispatch(Event(type="discord.voice.join", ts=time.time(), payload={
        "user_id": f"test-{display_name.lower()}",
        "username": display_name.lower(),
        "display_name": display_name,
        "avatar_url": "",
        "channel_id": "test-channel",
        "channel_name": "Gaming",
    }))
    return {"ok": True}


@router.post("/discord/leave")
async def test_discord_leave(display_name: str = "GuestUser") -> dict:
    await dispatch(Event(type="discord.voice.leave", ts=time.time(), payload={
        "user_id": f"test-{display_name.lower()}",
        "username": display_name.lower(),
        "channel_id": "test-channel",
    }))
    return {"ok": True}


@router.post("/discord/speaking")
async def test_discord_speaking(display_name: str = "GuestUser", speaking: bool = True) -> dict:
    await dispatch(Event(type="discord.voice.speaking", ts=time.time(), payload={
        "user_id": f"test-{display_name.lower()}",
        "speaking": speaking,
    }))
    return {"ok": True}
