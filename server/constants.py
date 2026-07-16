from enum import StrEnum


class ObsRequest(StrEnum):
    GET_SCENE_LIST = "GetSceneList"
    GET_VERSION = "GetVersion"
    SET_CURRENT_SCENE = "SetCurrentProgramScene"


class WsMessageType(StrEnum):
    SCENE_SWITCH = "scene.switch"
    STATE_SYNC = "state.sync"
    CONFIG_UPDATE = "config.update"
    CHAT_SEND_REQUEST = "chat.send.request"
    MOD_ACTION_REQUEST = "mod.action.request"


class ModAction(StrEnum):
    """Streamer moderation actions relayed to boneless_couch. The string values
    are the wire contract — boneless_couch defines its own matching enum."""
    BAN = "ban"
    TIMEOUT = "timeout"
    DELETE = "delete"


# Platforms whose moderation actions the cockpit can relay. boneless_couch owns
# the credentials; veil only forwards. Twitch-only for now.
MODERATABLE_PLATFORMS = ("twitch",)


class AlertType(StrEnum):
    SUB = "sub"
    RESUB = "resub"
    GIFTSUB = "giftsub"
    GIFTBOMB = "giftbomb"
    RAID = "raid"
    BITS = "bits"
    CHANNEL_POINT = "channel_point"
    FOLLOWER = "follower"
    TIP = "tip"


# Alerts that represent real money. These always fire on the overlay and are
# never suppressed by cooldowns — the only off-switch is the global
# alerts_enabled toggle (!alerts off).
MONEY_ALERT_TYPES = frozenset({
    AlertType.SUB,
    AlertType.RESUB,
    AlertType.GIFTSUB,
    AlertType.GIFTBOMB,
    AlertType.BITS,
    AlertType.TIP,
})

# All money alerts share one media pool (media/clips/money, media/audio/money);
# every other alert type has a folder named after itself.
MONEY_MEDIA_FOLDER = "money"
GENERAL_MEDIA_FOLDER = "general"
