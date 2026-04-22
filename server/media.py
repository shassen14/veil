import random
from pathlib import Path

from .config import config

_MEDIA_ROOT = Path(__file__).parent.parent / "media"
_CLIP_EXTS = {".gif", ".mp4", ".webm"}
_AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a"}


def _pick_from(directory: Path, exts: set[str]) -> Path | None:
    if not directory.is_dir():
        return None
    files = [f for f in directory.iterdir() if f.suffix.lower() in exts]
    return random.choice(files) if files else None


def pick_clip(alert_type: str) -> str | None:
    f = _pick_from(_MEDIA_ROOT / "clips" / alert_type, _CLIP_EXTS) \
        or _pick_from(_MEDIA_ROOT / "clips" / "general", _CLIP_EXTS)
    if f is None:
        return None
    return f"/media/clips/{f.parent.name}/{f.name}"


def pick_audio(alert_type: str) -> str | None:
    cfg_path = config.get("alerts", {}).get(alert_type, {}).get("audio", "")
    if cfg_path:
        f = _MEDIA_ROOT.parent / cfg_path
        if f.exists():
            return f"/{cfg_path}"
    f = _pick_from(_MEDIA_ROOT / "audio" / alert_type, _AUDIO_EXTS) \
        or _pick_from(_MEDIA_ROOT / "audio" / "general", _AUDIO_EXTS)
    if f is None:
        return None
    return f"/media/audio/{f.parent.name}/{f.name}"
