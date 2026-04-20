/**
 * Shared WebSocket client for veil overlay pages.
 * Automatically reconnects with exponential backoff.
 *
 * Usage:
 *   const veil = createVeilSocket({
 *     "alert.trigger": (data) => showAlert(data),
 *     "chat.message":  (data) => addMessage(data),
 *   });
 */
function createVeilSocket(handlers) {
  const url = `ws://${window.location.host}/ws`;
  let socket;
  let delay = 1000;

  function connect() {
    socket = new WebSocket(url);

    socket.onopen = () => {
      console.log("[veil] connected");
      delay = 1000;
    };

    socket.onmessage = (event) => {
      let msg;
      try { msg = JSON.parse(event.data); } catch { return; }
      const handler = handlers[msg.type];
      if (handler) handler(msg.data);
    };

    socket.onclose = () => {
      console.log(`[veil] disconnected — retrying in ${delay}ms`);
      setTimeout(connect, delay);
      delay = Math.min(delay * 2, 30000);
    };

    socket.onerror = () => socket.close();
  }

  connect();
  return { send: (msg) => socket && socket.readyState === 1 && socket.send(JSON.stringify(msg)) };
}
