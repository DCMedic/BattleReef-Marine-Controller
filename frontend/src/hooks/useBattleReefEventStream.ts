import { useEffect, useState } from "react";

import { getAccessToken } from "../api/client";
import type { StreamErrorPayload, StreamSnapshot } from "../types/stream";

type UseBattleReefEventStreamResult = {
  snapshot: StreamSnapshot | null;
  connected: boolean;
  error: string | null;
};

function parseFrame(frame: string): { event: string; data: string } | null {
  let event = "message";
  const data: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
  }
  return data.length ? { event, data: data.join("\n") } : null;
}

export function useBattleReefEventStream(): UseBattleReefEventStreamResult {
  const [snapshot, setSnapshot] = useState<StreamSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function connect() {
      const token = getAccessToken();
      if (!token) {
        setConnected(false);
        setError("Authentication is required for the live event stream.");
        return;
      }

      try {
        const response = await fetch("/api/v1/stream/events", {
          headers: { Authorization: `Bearer ${token}`, Accept: "text/event-stream" },
          signal: controller.signal,
        });
        if (!response.ok || !response.body) throw new Error(`stream_http_${response.status}`);

        setConnected(true);
        setError(null);
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (!controller.signal.aborted) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, "\n");
          let boundary = buffer.indexOf("\n\n");
          while (boundary >= 0) {
            const frame = parseFrame(buffer.slice(0, boundary));
            buffer = buffer.slice(boundary + 2);
            boundary = buffer.indexOf("\n\n");
            if (!frame) continue;
            try {
              if (frame.event === "battlereef_update") {
                setSnapshot(JSON.parse(frame.data) as StreamSnapshot);
                setConnected(true);
                setError(null);
              } else if (frame.event === "battlereef_error") {
                setError((JSON.parse(frame.data) as StreamErrorPayload).error);
              }
            } catch {
              setError("Failed to parse live stream update.");
            }
          }
        }
      } catch (exc) {
        if (!controller.signal.aborted) {
          setConnected(false);
          setError(exc instanceof Error ? `Live event stream disconnected: ${exc.message}` : "Live event stream disconnected.");
        }
      }
    }

    void connect();
    return () => controller.abort();
  }, []);

  return { snapshot, connected, error };
}
