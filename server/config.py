import os
import tomllib
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


def load() -> dict:
    with open(_CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    # Env vars take precedence over config.toml
    if secret := os.environ.get("VEIL_SECRET"):
        cfg["server"]["secret"] = secret
    if obs_host := os.environ.get("OBS_WS_HOST"):
        cfg.setdefault("obs", {})["host"] = obs_host
    if obs_password := os.environ.get("OBS_WS_PASSWORD"):
        cfg.setdefault("obs", {})["password"] = obs_password
    return cfg


def reload() -> None:
    new = load()
    config.clear()
    config.update(new)


config = load()
