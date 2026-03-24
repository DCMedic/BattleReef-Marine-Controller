import { useCallback, useEffect, useRef, useState } from "react";

import { fetchDeviceState } from "../api/queries";
import type { DeviceStateResponse } from "../types/deviceState";

type UseLiveDeviceStateResult = {
  state: DeviceStateResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  pulseRefresh: (durationMs?: number, intervalMs?: number) => void;
};

export function useLiveDeviceState(deviceKey: string): UseLiveDeviceStateResult {
  const [state, setState] = useState<DeviceStateResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const pulseTimerRef = useRef<number | null>(null);
  const pulseEndRef = useRef<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const response = await fetchDeviceState(deviceKey);
      setState(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch device state");
    } finally {
      setLoading(false);
    }
  }, [deviceKey]);

  const clearPulse = useCallback(() => {
    if (pulseTimerRef.current !== null) {
      window.clearInterval(pulseTimerRef.current);
      pulseTimerRef.current = null;
    }
    pulseEndRef.current = null;
  }, []);

  const pulseRefresh = useCallback(
    (durationMs = 15000, intervalMs = 1000) => {
      clearPulse();
      pulseEndRef.current = Date.now() + durationMs;

      pulseTimerRef.current = window.setInterval(() => {
        void refresh();

        if (pulseEndRef.current !== null && Date.now() >= pulseEndRef.current) {
          clearPulse();
        }
      }, intervalMs);
    },
    [clearPulse, refresh]
  );

  useEffect(() => {
    void refresh();

    const timer = window.setInterval(() => {
      void refresh();
    }, 4000);

    return () => {
      window.clearInterval(timer);
      clearPulse();
    };
  }, [clearPulse, refresh]);

  return {
    state,
    loading,
    error,
    refresh,
    pulseRefresh,
  };
}