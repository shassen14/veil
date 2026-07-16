import random
from pathlib import Path

from .config import config
from .constants import GENERAL_MEDIA_FOLDER, MONEY_ALERT_TYPES, MONEY_MEDIA_FOLDER, AlertType

_MEDIA_ROOT = Path(__file__).parent.parent / "media"
_CLIP_EXTS = {".gif", ".mp4", ".webm"}
_AUDIO_EXTS = {".mp3", ".wav", ".ogg", ".m4a"}

# Money alerts share one media pool; everything else gets its own folder.
_FOLDER = {
    t.value: MONEY_MEDIA_FOLDER if t in MONEY_ALERT_TYPES else t.value
    for t in AlertType
}


def _pick_from(directory: Path, exts: set[str]) -> Path | None:
    if not directory.is_dir():
        return None
    files = [f for f in directory.iterdir() if f.suffix.lower() in exts]
    return random.choice(files) if files else None


def pick_clip(alert_type: str) -> str | None:
    folder = _FOLDER.get(alert_type, GENERAL_MEDIA_FOLDER)
    f = _pick_from(_MEDIA_ROOT / "clips" / folder, _CLIP_EXTS) \
        or _pick_from(_MEDIA_ROOT / "clips" / GENERAL_MEDIA_FOLDER, _CLIP_EXTS)
    if f is None:
        return None
    return f"/media/clips/{f.parent.name}/{f.name}"


def pick_audio(alert_type: str) -> str | None:
    cfg_path = config.get("alerts", {}).get(alert_type, {}).get("audio", "")
    if cfg_path:
        f = _MEDIA_ROOT.parent / cfg_path
        if f.exists():
            return f"/{cfg_path}"
    folder = _FOLDER.get(alert_type, GENERAL_MEDIA_FOLDER)
    f = _pick_from(_MEDIA_ROOT / "audio" / folder, _AUDIO_EXTS) \
        or _pick_from(_MEDIA_ROOT / "audio" / GENERAL_MEDIA_FOLDER, _AUDIO_EXTS)
    if f is None:
        return None
    return f"/media/audio/{f.parent.name}/{f.name}"
