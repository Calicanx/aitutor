import { useEffect, useRef, useState, useCallback } from 'react';

interface UseWebSocketWithReconnectOptions {
  url: string;
  onOpen?: (event: Event) => void;
  onMessage?: (event: MessageEvent) => void;
  onError?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  maxReconnectAttempts?: number;
  reconnectInterval?: number;
  enabled?: boolean;
}

export function useWebSocketWithReconnect(options: UseWebSocketWithReconnectOptions) {
  const {
    url,
    onOpen,
    onMessage,
    onError,
    onClose,
    maxReconnectAttempts = 10,
    reconnectInterval = 3000,
    enabled = true,
  } = options;

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const isIntentionallyClosedRef = useRef(false);
  const handlersRef = useRef({ onOpen, onMessage, onError, onClose });

  // Update handlers ref when they change
  useEffect(() => {
    handlersRef.current = { onOpen, onMessage, onError, onClose };
  }, [onOpen, onMessage, onError, onClose]);

  const connect = useCallback(() => {
    if (!enabled || isIntentionallyClosedRef.current) {
      return;
    }

    if (socket && (socket.readyState === WebSocket.CONNECTING || socket.readyState === WebSocket.OPEN)) {
      return; // Already connecting or connected
    }

    try {
      const ws = new WebSocket(url);

      ws.onopen = (event) => {
        console.log('WebSocket connected:', url);
        reconnectAttemptsRef.current = 0;
        setIsConnected(true);
        handlersRef.current.onOpen?.(event);
      };

      ws.onmessage = (event) => {
        handlersRef.current.onMessage?.(event);
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', url, event);
        handlersRef.current.onError?.(event);
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', url, {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
        });
        setIsConnected(false);
        handlersRef.current.onClose?.(event);

        // Attempt reconnection if not intentionally closed and haven't exceeded max attempts
        if (!isIntentionallyClosedRef.current && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current += 1;
          const delay = reconnectInterval * Math.pow(2, reconnectAttemptsRef.current - 1); // Exponential backoff
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = window.setTimeout(() => {
            connect();
          }, delay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error(`Max reconnection attempts (${maxReconnectAttempts}) reached for ${url}`);
        }
      };

      setSocket(ws);
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [url, enabled, maxReconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    isIntentionallyClosedRef.current = true;
    if (reconnectTimeoutRef.current !== null) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (socket) {
      socket.close();
      setSocket(null);
      setIsConnected(false);
    }
  }, [socket]);

  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return { socket, isConnected, reconnect: connect, disconnect };
}

