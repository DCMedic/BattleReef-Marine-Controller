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

function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve) => {
    if (signal.aborted) return resolve();
    const id = window.setTimeout(resolve, ms);
    signal.addEventListener("abort", () => {
      window.clearTimeout(id);
      resolve();
    }, { once: true });
  });
}

export function useBattleReefEventStream(): UseBattleReefEventStreamResult {
  const [snapshot, setSnapshot] = useState<StreamSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      while (!controller.signal.aborted) {
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
          if (controller.signal.aborted) return;
          setConnected(false);
          setError(exc instanceof Error ? `Live event stream disconnected: ${exc.message}` : "Live event stream disconnected.");
        }

        if (!controller.signal.aborted) {
          setConnected(false);
          await delay(3000, controller.signal);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, []);

  return { snapshot, connected, error };
}
