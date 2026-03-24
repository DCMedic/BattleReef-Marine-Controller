import { useEffect, useRef, useState } from "react";

import type { StreamErrorPayload, StreamSnapshot } from "../types/stream";

type UseBattleReefEventStreamResult = {
  snapshot: StreamSnapshot | null;
  connected: boolean;
  error: string | null;
};

export function useBattleReefEventStream(): UseBattleReefEventStreamResult {
  const [snapshot, setSnapshot] = useState<StreamSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const source = new EventSource("/api/v1/stream/events");
    sourceRef.current = source;

    source.onopen = () => {
      setConnected(true);
      setError(null);
    };

    source.addEventListener("battlereef_update", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as StreamSnapshot;
        setSnapshot(payload);
        setConnected(true);
        setError(null);
      } catch {
        setError("Failed to parse live stream update.");
      }
    });

    source.addEventListener("battlereef_error", (event) => {
      try {
        const payload = JSON.parse((event as MessageEvent).data) as StreamErrorPayload;
        setError(payload.error);
      } catch {
        setError("Unknown stream error.");
      }
    });

    source.onerror = () => {
      setConnected(false);
      setError("Live event stream disconnected.");
    };

    return () => {
      source.close();
      sourceRef.current = null;
    };
  }, []);

  return {
    snapshot,
    connected,
    error,
  };
}