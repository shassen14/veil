from dataclasses import dataclass, field


@dataclass
class VeilState:
    scene: str = "brb"
    chat_visible: bool = True
    chat_sources: dict = field(default_factory=lambda: {"twitch": True, "youtube": True})
    discord_members: list = field(default_factory=list)


state = VeilState()
