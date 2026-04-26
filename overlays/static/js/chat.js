/**
 * Shared chat rendering utilities.
 * Globals: emoteMap, applyEmotes, renderMessageContent, userColor, buildMessageEl,
 *          createChatManager
 */

const emoteMap = new Map();

function applyEmotes(map) {
  emoteMap.clear();
  for (const [name, url] of Object.entries(map || {}))
    emoteMap.set(name, url);
}

function _emoteImg(src, alt) {
  const img = document.createElement("img");
  img.className = "emote";
  img.src = src;
  img.alt = alt;
  return img;
}

function _appendWords(container, text) {
  for (const token of text.split(/(\s+)/)) {
    if (!token) continue;
    const url = emoteMap.get(token);
    container.appendChild(url ? _emoteImg(url, token) : document.createTextNode(token));
  }
}

function renderMessageContent(message, fragments) {
  const frag = document.createDocumentFragment();
  if (!fragments || !fragments.length) {
    _appendWords(frag, message);
    return frag;
  }
  for (const f of fragments) {
    if (f.type === "emote" && f.id) {
      const url = `https://static-cdn.jtvnw.net/emoticons/v2/${f.id}/default/dark/2.0`;
      emoteMap.set(f.text, url);
      frag.appendChild(_emoteImg(url, f.text));
    } else {
      _appendWords(frag, f.text);
    }
  }
  return frag;
}

function userColor(name, twitchColor) {
  if (twitchColor) return twitchColor;
  let hash = 0;
  for (let i = 0; i < name.length; i++)
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return `hsl(${Math.abs(hash) % 360}, 70%, 65%)`;
}

function createChatManager(chatEl, opts = {}) {
  const messages = [];
  const messageMap = new Map();
  let maxMessages = opts.maxMessages ?? 20;
  let fadeTimeout = opts.fadeTimeout ?? 0;
  const chatSources = opts.chatSources ? { ...opts.chatSources } : null;

  function _trim() {
    if (messages.length > maxMessages) {
      const old = messages.shift();
      if (old.dataset.id) messageMap.delete(old.dataset.id);
      old.remove();
    }
  }

  // Register an externally-built element (e.g. pending mod messages).
  function track(el, id) {
    if (id) {
      el.dataset.id = id;
      messageMap.set(id, el);
    }
    messages.push(el);
    _trim();
  }

  function addMessage(data) {
    if (chatSources && data.source && chatSources[data.source] === false) return;
    if (data.message_id && messageMap.has(data.message_id)) return;
    const el = buildMessageEl(data);
    chatEl.appendChild(el);
    track(el, data.message_id);
    if (fadeTimeout > 0) {
      setTimeout(() => {
        el.classList.add("fading");
        setTimeout(() => {
          el.remove();
          if (data.message_id) messageMap.delete(data.message_id);
          const idx = messages.indexOf(el);
          if (idx !== -1) messages.splice(idx, 1);
        }, 500);
      }, fadeTimeout * 1000);
    }
  }

  function deleteMessage(id) {
    const el = messageMap.get(id);
    if (!el) return;
    el.classList.add("fading");
    setTimeout(() => {
      el.remove();
      messageMap.delete(id);
      const idx = messages.indexOf(el);
      if (idx !== -1) messages.splice(idx, 1);
    }, 500);
  }

  function clearUserMessages(username) {
    chatEl.querySelectorAll(`[data-username="${username}"]`).forEach((el) => {
      const msgId = el.dataset.id;
      if (msgId) messageMap.delete(msgId);
      const idx = messages.indexOf(el);
      if (idx !== -1) messages.splice(idx, 1);
      el.remove();
    });
  }

  function applyConfig(cfg) {
    const c = cfg?.chat || {};
    if (c.max_messages != null) maxMessages = c.max_messages;
    if (c.fade_timeout != null) fadeTimeout = c.fade_timeout;
  }

  function setChatSource(platform, enabled) {
    if (chatSources) chatSources[platform] = enabled;
  }

  return { messageMap, track, addMessage, deleteMessage, clearUserMessages, applyConfig, setChatSource };
}

function buildMessageEl(data) {
  const el = document.createElement("div");
  el.className = "msg";
  if (data.username) el.dataset.username = data.username;
  const color = userColor(data.display_name, data.color);
  if (data.source) {
    const icon = document.createElement("img");
    icon.className = "source-icon";
    icon.src = `/overlays/static/img/${data.source}.png`;
    icon.alt = data.source;
    el.appendChild(icon);
  }
  const author = document.createElement("span");
  author.className = "author";
  author.style.color = color;
  author.style.textShadow = `0 0 6px ${color}`;
  author.textContent = data.display_name + ":";
  el.appendChild(author);
  el.appendChild(document.createTextNode(" "));
  el.appendChild(renderMessageContent(data.message, data.fragments));
  return el;
}
