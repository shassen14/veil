from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import config
from .routes import alerts, chat, ingest, scenes, status, test
from .state import state
from .ws_manager import manager

app = FastAPI(title="veil", version="0.1.0")

_ROOT = Path(__file__).parent.parent

# Serve overlay HTML + assets at /overlays/*
app.mount("/overlays", StaticFiles(directory=_ROOT / "overlays"), name="overlays")

# API routes
app.include_router(ingest.router)
app.include_router(scenes.router)
app.include_router(alerts.router)
app.include_router(chat.router)
app.include_router(status.router)
app.include_router(test.router)


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    # Push full current state to the newly connected browser source
    await ws.send_json({
        "type": "state.sync",
        "data": {
            "scene": state.scene,
            "chat_visible": state.chat_visible,
            "chat_sources": state.chat_sources,
            "discord_members": state.discord_members,
        },
    })
    try:
        while True:
            await ws.receive_text()  # keep-alive; browser sends pings
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/")
async def dashboard() -> FileResponse:
    return FileResponse(_ROOT / "dashboard.html")
