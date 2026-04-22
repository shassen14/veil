"""
Event envelope and payload models for the boneless_couch → veil contract.

boneless_couch POSTs to POST /event with an Event body.
All payloads are typed here so both sides can stay in sync.
"""

from __future__ import annotations

import time
from typing import Any, Literal

from pydantic import BaseModel, model_validator


class Event(BaseModel):
    type: str
    ts: float = 0.0
    payload: dict[str, Any] = {}

    @model_validator(mode="after")
    def set_ts(self) -> Event:
        if self.ts == 0.0:
            self.ts = time.time()
        return self


# ---------------------------------------------------------------------------
# Twitch payload shapes (for documentation + boneless_couch reference)
# ---------------------------------------------------------------------------

class TwitchSubPayload(BaseModel):
    username: str
    display_name: str
    tier: Literal["1000", "2000", "3000"] = "1000"
    is_gift: bool = False


class TwitchResubPayload(BaseModel):
    username: str
    display_name: str
    tier: Literal["1000", "2000", "3000"] = "1000"
    cumulative_months: int
    streak_months: int = 0
    message: str = ""


class TwitchGiftSubPayload(BaseModel):
    gifter_username: str
    gifter_display_name: str
    recipient_username: str
    recipient_display_name: str
    tier: Literal["1000", "2000", "3000"] = "1000"
    total_gifted: int = 1


class TwitchGiftBombPayload(BaseModel):
    gifter_username: str
    gifter_display_name: str
    count: int
    tier: Literal["1000", "2000", "3000"] = "1000"


class TwitchBitsPayload(BaseModel):
    username: str
    display_name: str
    bits: int
    message: str = ""
    total_bits_given: int = 0


class TwitchRaidPayload(BaseModel):
    from_username: str
    from_display_name: str
    viewer_count: int
    profile_image_url: str = ""


class TwitchChannelPointRedeemPayload(BaseModel):
    username: str
    display_name: str
    reward_id: str
    reward_title: str
    reward_cost: int
    user_input: str = ""


class TwitchFollowerPayload(BaseModel):
    username: str
    display_name: str


class TwitchChatMessagePayload(BaseModel):
    username: str
    display_name: str
    message: str
    color: str = "#FFFFFF"
    badges: list[str] = []
    emotes: list[dict] = []
    message_id: str = ""
    platform: str = "twitch"


class ChatMessageDeletePayload(BaseModel):
    message_id: str
    platform: str = "twitch"


class ChatClearUserPayload(BaseModel):
    username: str
    platform: str = "twitch"


# ---------------------------------------------------------------------------
# Modqueue payload shapes
# ---------------------------------------------------------------------------

class ModQueuePendingPayload(BaseModel):
    message_id: str
    username: str
    display_name: str
    message: str
    color: str = ""
    badges: list[str] = []
    platform: str = "twitch"
    hold_sources: list[str] = []


class ModQueueResolvedPayload(BaseModel):
    message_id: str
    resolution: str  # "approved" | "denied" | "expired"


class ModQueueUpdatePayload(BaseModel):
    message_id: str
    hold_sources: list[str]


# ---------------------------------------------------------------------------
# Discord payload shapes
# ---------------------------------------------------------------------------

class DiscordVoiceJoinPayload(BaseModel):
    user_id: str
    username: str
    display_name: str
    avatar_url: str = ""
    channel_id: str
    channel_name: str


class DiscordVoiceLeavePayload(BaseModel):
    user_id: str
    username: str
    channel_id: str


class DiscordVoiceSpeakingPayload(BaseModel):
    user_id: str
    speaking: bool


class DiscordVoiceMutePayload(BaseModel):
    user_id: str
    self_mute: bool = False
    self_deaf: bool = False


# ---------------------------------------------------------------------------
# Event type registry — canonical string → payload model
# ---------------------------------------------------------------------------

class StreamStatsBootstrapPayload(BaseModel):
    last_follower: dict = {}
    last_raider: dict = {}
    last_bits: dict = {}
    recent_subs: list = []
    longest_subs: list = []


EVENT_TYPES: dict[str, type[BaseModel]] = {
    "stream.stats.bootstrap": StreamStatsBootstrapPayload,
    "twitch.sub": TwitchSubPayload,
    "twitch.resub": TwitchResubPayload,
    "twitch.giftsub": TwitchGiftSubPayload,
    "twitch.giftbomb": TwitchGiftBombPayload,
    "twitch.bits": TwitchBitsPayload,
    "twitch.raid": TwitchRaidPayload,
    "twitch.channel_point_redeem": TwitchChannelPointRedeemPayload,
    "twitch.follower": TwitchFollowerPayload,
    "twitch.chat.message": TwitchChatMessagePayload,
    "twitch.chat.message.delete": ChatMessageDeletePayload,
    "twitch.chat.clear_user": ChatClearUserPayload,
    "modqueue.pending": ModQueuePendingPayload,
    "modqueue.resolved": ModQueueResolvedPayload,
    "modqueue.update": ModQueueUpdatePayload,
    "discord.voice.join": DiscordVoiceJoinPayload,
    "discord.voice.leave": DiscordVoiceLeavePayload,
    "discord.voice.speaking": DiscordVoiceSpeakingPayload,
    "discord.voice.mute": DiscordVoiceMutePayload,
}
