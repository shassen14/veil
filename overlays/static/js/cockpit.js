/**
 * veil cockpit — streamer control surface.
 * Reuses veil.js (socket) + chat.js (chat rendering). Speaks the same
 * WS/HTTP protocol as the OBS overlays so no audience-facing change is needed.
 */

const $ = (id) => document.getElementById(id);
const chatEl = $("chat");

// ── auth: the moderation key, kept out of the URL ───────────────────────────
// Reading chat / toggles need no key — only /modqueue approve|reject does.
// The key lives in localStorage on this device and rides in the Authorization
// header, never the URL (so it can't surface on stream or in server logs).
const SECRET_KEY = "veil.cockpit.secret";

(function migrateUrlSecret() {
  const u = new URL(location.href);
  if (!u.searchParams.has("secret")) return;
  localStorage.setItem(SECRET_KEY, u.searchParams.get("secret"));
  u.searchParams.delete("secret");
  history.replaceState(null, "", u.pathname + u.search + u.hash); // scrub it
})();

let secret = localStorage.getItem(SECRET_KEY) || "";

function paintLock() {
  $("lock").classList.toggle("unlocked", !!secret);
  $("lock-txt").textContent = secret ? "unlocked" : "locked";
  document.body.classList.toggle("locked", !secret);
  const input = $("composer-input");
  if (input) input.placeholder = secret ? "Send a message or !command…" : "🔒 unlock to send…";
}
function setSecret(v) {
  secret = (v || "").trim();
  if (secret) localStorage.setItem(SECRET_KEY, secret);
  else localStorage.removeItem(SECRET_KEY);
  paintLock();
}
function openUnlock() {
  $("unlock").classList.add("show");
  $("secret-input").value = "";
  $("secret-input").focus();
}
function closeUnlock() { $("unlock").classList.remove("show"); }

enableLinks(); // URLs in chat become clickable (cockpit only)

// Reader keeps far more history than the overlay, never fades.
const chat = createChatManager(chatEl, {
  maxMessages: 250,
  disableFade: true,
  chatSources: { twitch: true, youtube: true },
});

// ── chat: live messages + auto-scroll ──────────────────────────────────────

let stuck = true; // pinned to bottom?
const NEAR = 70;

function atBottom() {
  return chatEl.scrollHeight - chatEl.scrollTop - chatEl.clientHeight < NEAR;
}
function toBottom() {
  chatEl.scrollTop = chatEl.scrollHeight;
  stuck = true;
  $("jump").classList.remove("show");
}
chatEl.addEventListener("scroll", () => {
  stuck = atBottom();
  if (stuck) $("jump").classList.remove("show");
});
$("jump").onclick = toBottom;

// Auto-scroll / "new messages" pill whenever the feed grows.
new MutationObserver(() => {
  $("empty")?.remove();
  if (stuck) toBottom();
  else $("jump").classList.add("show");
}).observe(chatEl, { childList: true });

// ── pending moderation (mirrors overlays/chat.html) ─────────────────────────

// Keep the full payload of held messages so an approved one can gain the same
// delete/timeout/ban controls a normal message has.
const pendingData = new Map();

function addPending(data) {
  if (chat.messageMap.has(data.message_id)) return;
  pendingData.set(data.message_id, data);
  const el = buildMessageEl(data);
  el.classList.add("pending");

  const actions = document.createElement("span");
  actions.className = "mod-actions";
  for (const [cls, glyph, action] of [["approve", "✓ allow", "approve"], ["deny", "✗ deny", "reject"]]) {
    const b = document.createElement("button");
    b.className = "mod-btn " + cls;
    b.textContent = glyph;
    b.onclick = () => moderate(data.message_id, action);
    actions.appendChild(b);
  }
  el.appendChild(actions);
  chatEl.appendChild(el);
  chat.track(el, data.message_id);
}

function moderate(id, action) {
  if (!secret) { openUnlock(); return; } // need the key before we can act
  fetch(`/modqueue/${id}/${action}`, {
    method: "POST",
    headers: { Authorization: "Bearer " + secret },
  }).catch(() => {});
}

function onDecision(data) {
  const held = pendingData.get(data.message_id);
  pendingData.delete(data.message_id);
  const el = chat.messageMap.get(data.message_id);
  if (!el) return;
  if (data.decision === "approve") {
    el.classList.remove("pending");
    el.querySelector(".mod-actions")?.remove();
    attachModControls(held); // now a normal message — give it full controls
  } else {
    chat.deleteMessage(data.message_id);
  }
}

// ── per-message moderation: delete / timeout / ban (Twitch) ─────────────────
// Controls ride on every Twitch message, not just engine-held ones. The action
// is relayed to boneless_couch; the message disappears via the delete/clear_user
// events Twitch emits afterwards, so there's nothing to remove optimistically.
const TIMEOUTS = [["10m", 600], ["1h", 3600], ["24h", 86400]];

function modAction(body) {
  if (!secret) { openUnlock(); return; } // privileged: needs the key
  fetch("/moderate", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + secret },
    body: JSON.stringify(body),
  }).catch(() => {});
}

function attachModControls(data) {
  if (!data || (data.source || data.platform) !== "twitch" || data.is_bot) return;
  const el = chat.messageMap.get(data.message_id);
  if (!el || el.querySelector(".mod-actions")) return;

  const actions = document.createElement("span");
  actions.className = "mod-actions hover-only";

  const del = document.createElement("button");
  del.className = "mod-btn delete";
  del.textContent = "🗑";
  del.title = "delete message";
  del.onclick = () => modAction({ action: "delete", platform: "twitch", message_id: data.message_id });
  actions.appendChild(del);

  if (data.user_id) {
    for (const [label, seconds] of TIMEOUTS) {
      const b = document.createElement("button");
      b.className = "mod-btn timeout";
      b.textContent = label;
      b.title = `timeout ${label}`;
      b.onclick = () => modAction({
        action: "timeout", platform: "twitch",
        user_id: data.user_id, username: data.username, duration: seconds,
      });
      actions.appendChild(b);
    }
    const ban = document.createElement("button");
    ban.className = "mod-btn ban";
    ban.textContent = "⛔";
    ban.title = "ban permanently";
    ban.onclick = () => {
      if (confirm(`Ban ${data.display_name || data.username} permanently?`))
        modAction({ action: "ban", platform: "twitch", user_id: data.user_id, username: data.username });
    };
    actions.appendChild(ban);
  }
  el.appendChild(actions);
}

function addLiveMessage(d) {
  chat.addMessage(d);
  attachModControls(d);
}

// ── controls: source pills + switches ───────────────────────────────────────

const ui = { twitch: true, youtube: true, alerts: true, audio: true, chatViz: true };

function paintSource(p) {
  const el = $("src-" + p);
  el.classList.toggle("on", ui[p]);
  el.classList.toggle("off", !ui[p]);
}
function paintSwitch(id, on) { $(id).classList.toggle("on", on); }

function paintControls() {
  paintSource("twitch");
  paintSource("youtube");
  paintSwitch("sw-alerts", ui.alerts);
  paintSwitch("sw-audio", ui.audio);
  paintSwitch("sw-chat", ui.chatViz);
}

function post(url) { fetch(url, { method: "POST" }).catch(() => {}); }

$("src-twitch").onclick = () => post(`/chat/source/twitch?enabled=${!ui.twitch}`);
$("src-youtube").onclick = () => post(`/chat/source/youtube?enabled=${!ui.youtube}`);
$("sw-alerts").onclick = () => post(ui.alerts ? "/alerts/off" : "/alerts/on");
$("sw-audio").onclick = () => post(ui.audio ? "/alerts/audio/off" : "/alerts/audio/on");
$("sw-chat").onclick = () => post("/chat/toggle");
$("clear-queue").onclick = () => post("/alerts/queue/clear");

// ── stats tiles (dismissible, persisted) ────────────────────────────────────

const STATS_KEY = "veil.cockpit.hiddenStats";
let hiddenStats = new Set(JSON.parse(localStorage.getItem(STATS_KEY) || "[]"));
const stats = {};

function persistStats() {
  localStorage.setItem(STATS_KEY, JSON.stringify([...hiddenStats]));
}
function paintTile(key) {
  const tile = $("tile-" + key);
  if (tile) tile.classList.toggle("hidden", hiddenStats.has(key));
}
function setTile(key, value, accent) {
  stats[key] = value;
  const v = $("v-" + key);
  if (!v) return;
  v.classList.toggle("dim", !value);
  v.innerHTML = value
    ? (accent != null ? `${value} · <em>${accent}</em>` : value)
    : "—";
}
function refreshRestore() {
  $("restore").classList.toggle("show", hiddenStats.size > 0);
}

document.querySelectorAll(".tile .x").forEach((x) => {
  x.onclick = (e) => {
    e.stopPropagation();
    const key = x.closest(".tile").dataset.key;
    hiddenStats.add(key);
    paintTile(key);
    persistStats();
    refreshRestore();
  };
});
$("restore").onclick = () => {
  hiddenStats.forEach((k) => { const t = $("tile-" + k); if (t) t.classList.remove("hidden"); });
  hiddenStats.clear();
  persistStats();
  refreshRestore();
};

function name(o) { return o && (o.display_name || o.username) || ""; }

function applyStats(d) {
  if (d.last_follower !== undefined) setTile("follower", name(d.last_follower));
  if (d.last_sub !== undefined) setTile("sub", name(d.last_sub));
  if (d.last_raider !== undefined) setTile("raid", name(d.last_raider), d.last_raider?.viewer_count || null);
  if (d.last_bits !== undefined) setTile("bits", name(d.last_bits), d.last_bits?.bits || null);
}

function applyDiscord(members) {
  const box = $("vc-list");
  if (!members || !members.length) {
    box.innerHTML = `<div class="vc-empty">empty</div>`;
    return;
  }
  box.innerHTML = "";
  for (const m of members) {
    const row = document.createElement("div");
    row.className = "vc-row" + (m.speaking ? " speaking" : "");
    const avi = document.createElement("img");
    avi.className = "avi";
    avi.src = m.avatar_url || "/overlays/static/img/default_avatar.png";
    const nm = document.createElement("span");
    nm.textContent = m.display_name;
    row.append(avi, nm);
    if (m.muted) {
      const mu = document.createElement("span");
      mu.className = "mute"; mu.textContent = "muted";
      row.appendChild(mu);
    }
    box.appendChild(row);
  }
}

// ── collapsible panels (persisted) ──────────────────────────────────────────

document.querySelectorAll(".panel-head").forEach((h) => {
  const panel = h.closest(".panel");
  const key = "veil.cockpit.collapse." + panel.id;
  if (localStorage.getItem(key) === "1") panel.classList.add("collapsed");
  h.onclick = () => {
    panel.classList.toggle("collapsed");
    localStorage.setItem(key, panel.classList.contains("collapsed") ? "1" : "0");
  };
});

// ── narrow-screen drawer ────────────────────────────────────────────────────

const toggleRail = (open) => document.body.classList.toggle("rail-open", open);
$("drawer-toggle").onclick = () => toggleRail(!document.body.classList.contains("rail-open"));
$("scrim").onclick = () => toggleRail(false);

// ── composer: send chat / run commands (needs the key) ──────────────────────
const TARGETS_KEY = "veil.cockpit.targets";
let targets = JSON.parse(localStorage.getItem(TARGETS_KEY) || '{"twitch":true,"youtube":true}');

function paintTargets() {
  for (const t of ["twitch", "youtube"]) $("tgt-" + t).classList.toggle("on", !!targets[t]);
}
for (const t of ["twitch", "youtube"]) {
  $("tgt-" + t).onclick = () => {
    targets[t] = !targets[t];
    localStorage.setItem(TARGETS_KEY, JSON.stringify(targets));
    paintTargets();
  };
}

$("composer").addEventListener("submit", (e) => {
  e.preventDefault();
  const input = $("composer-input");
  const text = input.value.trim();
  if (!text) return;
  if (!secret) { openUnlock(); return; }       // privileged: needs the key
  const to = ["twitch", "youtube"].filter((t) => targets[t]);
  if (!to.length) return;
  fetch("/chat/send", {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: "Bearer " + secret },
    body: JSON.stringify({ text, targets: to }),
  }).then((r) => { if (r.ok) input.value = ""; }).catch(() => {});
});

// lock: click to enter the key (when locked) or clear it (when unlocked)
$("lock").onclick = () => (secret ? setSecret("") : openUnlock());
$("secret-save").onclick = () => { setSecret($("secret-input").value); closeUnlock(); };
$("secret-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") $("secret-save").click();
  if (e.key === "Escape") closeUnlock();
});

function paintPendingBadge() {
  const n = chat.messageMap.size && [...document.querySelectorAll(".msg.pending")].length;
  const b = $("pending-badge");
  b.textContent = n;
  b.classList.toggle("show", n > 0);
}

// ── clock + connection ──────────────────────────────────────────────────────

setInterval(() => {
  $("clock").textContent = new Date().toLocaleTimeString("en-US", { hour12: false });
}, 1000);

function setLive(on) {
  const p = $("signal");
  p.classList.toggle("live", on);
  $("signal-label").textContent = on ? "LIVE" : "OFFLINE";
}

// ── socket ──────────────────────────────────────────────────────────────────

createVeilSocket({
  "state.sync": (d) => {
    applyEmotes(d.emote_map);
    ui.twitch = d.chat_sources?.twitch ?? true;
    ui.youtube = d.chat_sources?.youtube ?? true;
    ui.alerts = d.alerts_enabled ?? true;
    ui.audio = d.alerts_audio_enabled ?? true;
    ui.chatViz = d.chat_visible ?? true;
    paintControls();
    Object.entries(d.chat_sources || {}).forEach(([p, v]) => chat.setChatSource(p, v));
    applyStats(d);
    applyDiscord(d.discord_members);
    (d.pending_messages || []).forEach(addPending);
    paintPendingBadge();
  },
  "emotes.update": (d) => applyEmotes(d),
  "chat.message": (d) => addLiveMessage(d),
  "chat.bot.message": (d) => chat.addMessage(d), // bot replies — cockpit-only feedback
  "chat.message.delete": (d) => chat.deleteMessage(d.message_id),
  "chat.clear_user": (d) => chat.clearUserMessages(d.username),
  "modqueue.pending": (d) => { addPending(d); paintPendingBadge(); },
  "modqueue.resolved": (d) => { pendingData.delete(d.message_id); chat.deleteMessage(d.message_id); paintPendingBadge(); },
  "modqueue.decision": (d) => { onDecision(d); paintPendingBadge(); },
  "chat.source.toggle": (d) => {
    ui[d.platform] = d.enabled;
    chat.setChatSource(d.platform, d.enabled);
    paintSource(d.platform);
  },
  "alerts.toggle": (d) => { ui.alerts = d.enabled; paintSwitch("sw-alerts", d.enabled); },
  "alerts.audio.toggle": (d) => { ui.audio = d.enabled; paintSwitch("sw-audio", d.enabled); },
  "overlay.toggle": (d) => { if (d.overlay === "chat") { ui.chatViz = d.visible; paintSwitch("sw-chat", d.visible); } },
  "viewer_stats.update": (d) => applyStats(d),
  "viewer_stats.bootstrap": (d) => applyStats(d),
  "discord.voice.update": (d) => applyDiscord(d.members),
}, {
  onopen: () => setLive(true),
  onclose: () => setLive(false),
});

// initial tile visibility from storage
["follower", "sub", "raid", "bits"].forEach(paintTile);
refreshRestore();
paintTargets();
paintLock();
