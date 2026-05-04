from enum import StrEnum


class ObsRequest(StrEnum):
    GET_SCENE_LIST = "GetSceneList"
    GET_VERSION = "GetVersion"
    SET_CURRENT_SCENE = "SetCurrentProgramScene"


class WsMessageType(StrEnum):
    SCENE_SWITCH = "scene.switch"
    STATE_SYNC = "state.sync"
    CONFIG_UPDATE = "config.update"
