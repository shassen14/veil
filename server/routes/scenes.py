from fastapi import APIRouter

from ..state import state
from ..ws_manager import manager

router = APIRouter()


@router.post("/scene/{name}")
async def switch_scene(name: str) -> dict:
    state.scene = name
    await manager.broadcast({"type": "scene.change", "data": {"scene": name}})
    return {"ok": True, "scene": name}
