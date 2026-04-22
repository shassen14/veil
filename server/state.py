from dataclasses import dataclass, field


@dataclass
class VeilState:
    chat_visible: bool = True
    chat_sources: dict = field(default_factory=lambda: {"twitch": True, "youtube": True})
    discord_members: list = field(default_factory=list)
    pending_messages: dict = field(default_factory=dict)
    emote_map: dict = field(default_factory=dict)
    last_follower: dict = field(default_factory=dict)
    last_sub: dict = field(default_factory=dict)
    last_raider: dict = field(default_factory=dict)
    last_bits: dict = field(default_factory=dict)
    recent_subs: list = field(default_factory=list)
    longest_subs: list = field(default_factory=list)


state = VeilState()
