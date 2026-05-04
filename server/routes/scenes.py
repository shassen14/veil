from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..constants import WsMessageType
from ..obs import obs_client
from ..state import state
from ..ws_manager import manager

router = APIRouter()


class SceneSwitchRequest(BaseModel):
    scene: str


def _require_obs() -> None:
    if not obs_client.connected:
        raise HTTPException(status_code=503, detail="OBS not connected")


@router.get("/scenes")
async def list_scenes() -> dict:
    _require_obs()
    scenes, current = await obs_client.get_scenes()
    state.current_scene = current
    return {"scenes": scenes, "current": current}


@router.post("/scenes/switch")
async def switch_scene(body: SceneSwitchRequest) -> dict:
    _require_obs()
    await obs_client.switch_scene(body.scene)
    state.current_scene = body.scene
    await manager.broadcast({"type": WsMessageType.SCENE_SWITCH, "data": {"scene": body.scene}})
    return {"ok": True, "scene": body.scene}
