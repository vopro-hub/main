// hooks/usePublicWS.js
import { useEffect, useRef } from "react";

export default function usePublicWS(url, handlers = {}) {
  const wsRef = useRef(null);

  useEffect(() => {
    if (!url) return;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (handlers.onOpen) handlers.onOpen();
    };
    ws.onmessage = (ev) => {
      let payload = null;
      try {
        payload = JSON.parse(ev.data);
      } catch (e) {
        console.warn("ws parse error", e);
        return;
      }
      if (handlers.onMessage) handlers.onMessage(payload);
    };
    ws.onerror = (e) => {
      if (handlers.onError) handlers.onError(e);
    };
    ws.onclose = (e) => {
      if (handlers.onClose) handlers.onClose(e);
    };

    return () => {
      try {
        ws.close();
      } catch {}
    };
  }, [url]); // reconnect if url changes

  return wsRef;
}
