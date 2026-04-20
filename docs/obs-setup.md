# Connecting OBS to veil

veil serves overlay pages over HTTP. OBS loads them as **Browser Sources**, which connect to veil's WebSocket automatically when the scene is loaded. No plugins required.

---

## Prerequisites

- veil is running (check: `curl http://<pi-ip>:8002/status` returns JSON)
- OBS is open on your streaming PC
- Both machines are on the same local network

Replace `<pi-ip>` with your Pi's local IP throughout (e.g. `192.168.1.42`).

---

## Available overlays

| Overlay | URL | What it shows |
|---|---|---|
| Chat | `http://<pi-ip>:8002/overlays/chat.html` | Twitch/YouTube chat, bottom-right, fades after 30s |
| Alerts | `http://<pi-ip>:8002/overlays/alerts.html` | Sub, resub, gift sub, raid, bits, channel points — top-center |
| Discord VC | `http://<pi-ip>:8002/overlays/discord_vc.html` | Voice channel members, speaking indicator, bottom-left |
| Dashboard | `http://<pi-ip>:8002/dashboard.html` | Manual control panel (open in a browser, not OBS) |

---

## Adding a Browser Source in OBS

1. In the **Sources** panel, click **+** → **Browser**
2. Name it (e.g. `veil-chat`) and click **OK**
3. Set **URL** to the overlay URL from the table above
4. Set **Width** and **Height** to match your canvas (usually `1920` × `1080`)
5. Check **Shutdown source when not visible** — this disconnects the WebSocket when the source is hidden, which is fine
6. Uncheck **Refresh browser when scene becomes active** — veil syncs state on connect automatically
7. Click **OK**

Repeat for each overlay you want. Each one opens its own WebSocket connection — `ws_connections` in `/status` will increment for each active source.

---

## Scene layouts

### just_chatting

Webcam fills the canvas. Alerts sit on top for subs/raids.

| Source | Type | W | H | X | Y |
|---|---|---|---|---|---|
| `veil-alerts` | Browser | 1920 | 1080 | 0 | 0 |
| `webcam` | Video Capture | 1920 | 1080 | 0 | 0 |

---

### coding

Right sidebar (340px wide). Screen fills the left 1580px at full height.

| Source | Type | W | H | X | Y |
|---|---|---|---|---|---|
| `veil-alerts` | Browser | 1920 | 1080 | 0 | 0 |
| `veil-discord-vc` | Browser | 340 | 225 | 1580 | 855 |
| `veil-chat` | Browser | 340 | 585 | 1580 | 270 |
| `webcam` | Video Capture | 480 | 270 | 1580 | 0 |
| `screen` | Display Capture | 1580 | 1080 | 0 | 0 |

Sidebar stack top→bottom: webcam 270px · chat 585px · discord 225px = 1080px.

**Webcam crop** — the webcam source is captured at 480×270 then cropped to 340px wide:
1. Right-click the webcam source → **Filters** → **+** → **Crop/Pad**
2. Set Left: `70`, Right: `70`, Top: `0`, Bottom: `0`

**Screen crop** (remove macOS menu bar):
1. Right-click the screen source → **Filters** → **+** → **Crop/Pad**
2. Set Top: `25`

**Browser source settings** (all three overlays):
- Width/Height: match the table above — do NOT use full canvas
- Check **Shutdown source when not visible**
- Uncheck **Refresh browser when scene becomes active**

**Discord layout** auto-adjusts by member count:
- 1–2 members → horizontal pill per member
- 3–4 members → 2×2 grid
- 5–8 members → 4×2 grid

---

## Verifying it's connected

After adding the sources, check:

```bash
curl http://<pi-ip>:8002/status
```

`ws_connections` should equal the number of active Browser Sources. Then fire a test event:

```bash
curl -X POST http://<pi-ip>:8002/test/chat
curl -X POST http://<pi-ip>:8002/test/alert/sub
curl -X POST http://<pi-ip>:8002/test/discord/join
```

You should see the overlay react in OBS immediately.

---

## Troubleshooting

**`ws_connections: 0` after adding sources**
- Make sure veil is reachable from the streaming PC: `ping <pi-ip>` and `curl http://<pi-ip>:8002/status` from that machine
- Check that OBS isn't blocking local network requests (some VPNs or firewalls interfere)
- Try clicking **Refresh** on the Browser Source in OBS

**Overlay loads but events don't appear**
- Confirm boneless_couch is sending to the correct IP and port (8002)
- Check the Bearer token matches `config.toml [server] secret`
- Use the `/test/*` endpoints to rule out boneless_couch as the issue

**Chat is hidden**
- `chat_visible` in `/status` may be `false` — use the dashboard at `http://<pi-ip>:8002/dashboard.html` to toggle it
