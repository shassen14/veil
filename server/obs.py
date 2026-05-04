import asyncio
import logging

import simpleobsws

from .config import config
from .constants import ObsRequest

log = logging.getLogger(__name__)

_RECONNECT_BACKOFF_S = 5
_KEEPALIVE_INTERVAL_S = 30


class ObsClient:
    def __init__(self) -> None:
        self._ws: simpleobsws.WebSocketClient | None = None
        self._connected: bool = False
        self._reconnect_needed: asyncio.Event = asyncio.Event()

    @property
    def connected(self) -> bool:
        return self._connected

    def _signal_reconnect(self) -> None:
        self._connected = False
        self._reconnect_needed.set()

    async def connect(self) -> None:
        obs_cfg = config.get("obs", {})
        url = f"ws://{obs_cfg['host']}:{obs_cfg['port']}"
        self._ws = simpleobsws.WebSocketClient(url=url, password=obs_cfg.get("password", ""))
        try:
            await self._ws.connect()
            await asyncio.wait_for(self._ws.wait_until_identified(), timeout=5.0)
            self._connected = True
            self._reconnect_needed.clear()
            log.info("Connected to OBS WebSocket at %s", url)
        except Exception as exc:
            self._connected = False
            log.warning("OBS not available: %s", exc)

    async def disconnect(self) -> None:
        if self._ws and self._connected:
            await self._ws.disconnect()
        self._connected = False

    async def reconnect_loop(self) -> None:
        """Wakes on disconnect signal; the sleep is backoff only, not a poll interval."""
        while True:
            await self._reconnect_needed.wait()
            self._reconnect_needed.clear()
            await asyncio.sleep(_RECONNECT_BACKOFF_S)
            log.info("OBS reconnect attempt...")
            await self.connect()

    async def keepalive_loop(self) -> None:
        """Periodic ping to detect silent disconnects when no button presses are occurring."""
        while True:
            await asyncio.sleep(_KEEPALIVE_INTERVAL_S)
            if self._connected:
                try:
                    await self._ws.call(simpleobsws.Request(ObsRequest.GET_VERSION))
                except Exception:
                    log.info("OBS keepalive failed — signalling reconnect")
                    self._signal_reconnect()

    async def get_scenes(self) -> tuple[list[str], str]:
        try:
            result = await self._ws.call(simpleobsws.Request(ObsRequest.GET_SCENE_LIST))
        except Exception as exc:
            self._signal_reconnect()
            log.warning("OBS call failed: %s", exc)
            raise
        scenes = sorted(result.responseData["scenes"], key=lambda s: s["sceneIndex"], reverse=True)
        current: str = result.responseData["currentProgramSceneName"]
        return [s["sceneName"] for s in scenes], current

    async def switch_scene(self, name: str) -> None:
        try:
            req = simpleobsws.Request(ObsRequest.SET_CURRENT_SCENE, {"sceneName": name})
            await self._ws.call(req)
        except Exception as exc:
            self._signal_reconnect()
            log.warning("OBS call failed: %s", exc)
            raise


obs_client = ObsClient()
