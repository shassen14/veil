/**
 * Shared chat rendering utilities.
 * Globals: emoteMap, applyEmotes, renderMessageContent, userColor, buildMessageEl
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
    if (f.type === "emote") {
      frag.appendChild(_emoteImg(
        `https://static-cdn.jtvnw.net/emoticons/v2/${f.id}/default/dark/2.0`,
        f.text,
      ));
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
