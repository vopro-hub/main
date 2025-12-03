import { useEffect, useRef, useState, useCallback } from "react";

export default function useWebSocket(url, { onMessage, onOpen, onClose, onError, reconnect = true, maxRetries = 10 } = {}) {
  const wsRef = useRef(null);
  const queueRef = useRef([]); // queue messages while socket isn't open
  const retriesRef = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  const send = useCallback((data) => {
    const msg = typeof data === "string" ? data : JSON.stringify(data);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    } else {
      queueRef.current.push(msg);
    }
  }, []);

  useEffect(() => {
    let connectTimer;

    function connect() {
      wsRef.current = new WebSocket(url);

      wsRef.current.onopen = () => {
        setIsConnected(true);
        retriesRef.current = 0;
        // Flush queued messages
        while (queueRef.current.length > 0) {
          wsRef.current.send(queueRef.current.shift());
        }
        onOpen && onOpen();
      };

      wsRef.current.onmessage = (event) => {
        let data;
        try {
          data = JSON.parse(event.data);
        } catch {
          data = event.data;
        }
        onMessage && onMessage(data);
      };

      wsRef.current.onclose = () => {
        setIsConnected(false);
        onClose && onClose();

        if (reconnect && retriesRef.current < maxRetries) {
          const delay = Math.min(1000 * 2 ** retriesRef.current, 30000); // capped exponential backoff
          retriesRef.current += 1;
          connectTimer = setTimeout(connect, delay);
        }
      };

      wsRef.current.onerror = (err) => {
        onError && onError(err);
        wsRef.current.close(); // ensure it goes through onclose
      };
    }

    connect();

    return () => {
      reconnect = false;
      clearTimeout(connectTimer);
      wsRef.current && wsRef.current.close();
    };
  }, [url]);

  return { send, isConnected };
}
