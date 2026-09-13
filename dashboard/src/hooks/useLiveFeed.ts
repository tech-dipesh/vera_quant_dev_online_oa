"use client";

import { useEffect, useRef, useState } from "react";
import { liveEventSchema, type LiveEvent } from "@/lib/schemas";
import { liveFeedUrl } from "@/lib/api";

export type ConnectionStatus = "connecting" | "open" | "closed";

export function useLiveFeed(onEvent: (event: LiveEvent) => void): ConnectionStatus {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const onEventRef = useRef(onEvent);

  useEffect(() => {
    onEventRef.current = onEvent;
  });

  useEffect(() => {
    let socket: WebSocket | undefined;
    let cancelled = false;
    let reconnectTimer: ReturnType<typeof setTimeout>;

    function connect() {
      socket = new WebSocket(liveFeedUrl());
      setStatus("connecting");

      socket.onopen = () => setStatus("open");

      socket.onclose = () => {
        setStatus("closed");
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 2000);
        }
      };

      socket.onerror = () => socket?.close();

      socket.onmessage = (message: MessageEvent<string>) => {
        const parsed = liveEventSchema.safeParse(JSON.parse(message.data));
        if (parsed.success) {
          onEventRef.current(parsed.data);
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  return status;
}
