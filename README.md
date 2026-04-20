# veil

Stream overlay server. Runs on a Raspberry Pi, serves browser sources to OBS on your streaming computer.

Handles chat aggregation (Twitch + YouTube), alert animations (subs, raids, bits, etc.), Discord voice channel display, and scene switching. Receives events from `boneless_couch` via HTTP POST and pushes updates to OBS browser sources over WebSocket.

---

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

---

## Setup

Copy the example env file and set your secret:

```bash
cp .env.example .env
```

Edit `.env`:

```
VEIL_SECRET=your-secret-here
```

Install dependencies with uv:

```bash
uv sync
```

## Run

```bash
uv run python run.py
```

Server starts at `http://0.0.0.0:8002`. From any device on the same network, use the Pi's IP:

```
http://<pi-ip>:8002/          ← test dashboard
http://<pi-ip>:8002/status    ← JSON status
```

---

## Docker

Build and run from the `docker/` directory:

```bash
# from repo root
docker compose -f docker/docker-compose.yml up --build
```

The `.env` file at the repo root is loaded automatically. `config.toml` and `media/` are mounted as volumes so you can edit them without rebuilding.

---

## OBS Setup

Add three Browser Sources in OBS, pointed at the Pi:

| Source | URL |
|---|---|
| Chat | `http://<pi-ip>:8002/overlays/chat.html` |
| Alerts | `http://<pi-ip>:8002/overlays/alerts.html` |
| Discord VC | `http://<pi-ip>:8002/overlays/discord_vc.html` |

Recommended size: 1920×1080, transparent background. The overlays connect as soon as OBS opens — no stream required.

---

## Testing Off-Stream

Open `http://<pi-ip>:8002/` on any device. The dashboard lets you fire test alerts, send fake chat messages, simulate Discord voice joins, and switch scenes — without `boneless_couch` running.

You can also use curl:

```bash
# fire a test raid
curl -X POST http://<pi-ip>:8002/test/alert/raid

# send a chat message
curl -X POST "http://<pi-ip>:8002/test/chat?message=hello"

# switch scene
curl -X POST http://<pi-ip>:8002/scene/coding
```

---

## boneless_couch Integration

Set the same secret in both projects. Then send events to veil with a `POST /event`:

```bash
curl -X POST http://<pi-ip>:8002/event \
  -H "Authorization: Bearer your-secret-here" \
  -H "Content-Type: application/json" \
  -d '{"type": "twitch.raid", "payload": {"from_username": "raider", "from_display_name": "Raider", "viewer_count": 42}}'
```

Full event type list and payload shapes: [`server/events.py`](server/events.py) and [`docs/veil.md`](docs/veil.md).

---

## helm Integration

```
POST /scene/:name           — switch scene
POST /alert/:type           — fire alert
POST /chat/toggle           — show/hide chat
GET  /status                — current state
```

---

## Project Docs

See [`docs/veil.md`](docs/veil.md) for full architecture, event schema, WebSocket protocol, and file structure.
