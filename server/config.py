import os
import tomllib
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent.parent / "config.toml"


def load() -> dict:
    with open(_CONFIG_PATH, "rb") as f:
        cfg = tomllib.load(f)
    # VEIL_SECRET env var takes precedence over config.toml
    secret = os.environ.get("VEIL_SECRET")
    if secret:
        cfg["server"]["secret"] = secret
    return cfg


config = load()
