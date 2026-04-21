import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import config, reload as reload_config
from .routes import alerts, chat, ingest, modqueue, status, test
from .state import state
from .ws_manager import manager

_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = _ROOT / "config.toml"


def _public_config() -> dict:
    return {k: v for k, v in config.items() if k != "server"}


async def _watch_config() -> None:
    mtime = _CONFIG_PATH.stat().st_mtime
    while True:
        await asyncio.sleep(2)
        try:
            new_mtime = _CONFIG_PATH.stat().st_mtime
        except OSError:
            continue
        if new_mtime != mtime:
            mtime = new_mtime
            reload_config()
            await manager.broadcast({"type": "config.update", "data": _public_config()})


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_watch_config())
    yield
    task.cancel()


app = FastAPI(title="veil", version="0.1.0", lifespan=lifespan)

# Serve overlay HTML + assets at /overlays/*
app.mount("/overlays", StaticFiles(directory=_ROOT / "overlays"), name="overlays")

# Serve media files (clips, audio) at /media/*
app.mount("/media", StaticFiles(directory=_ROOT / "media"), name="media")

# API routes
app.include_router(ingest.router)
app.include_router(modqueue.router)
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
            "chat_visible": state.chat_visible,
            "chat_sources": state.chat_sources,
            "discord_members": state.discord_members,
            "pending_messages": list(state.pending_messages.values()),
            "config": _public_config(),
        },
    })
    try:
        while True:
            await ws.receive_text()  # keep-alive; browser sends pings
    except WebSocketDisconnect:
        manager.disconnect(ws)


@app.get("/")
@app.get("/dashboard.html")
async def dashboard() -> FileResponse:
    return FileResponse(_ROOT / "dashboard.html")
