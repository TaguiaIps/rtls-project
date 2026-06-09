import { useCallback, useEffect, useRef, useState } from "react";
import type { AssetLocationRecord, LocationConfidenceLevel } from "@rtls/contracts";

export type SelfLocationState = {
  x: number;
  y: number;
  confidenceLevel: LocationConfidenceLevel;
  confidenceScore: number;
  precisionMeters: number | null;
  floorId: string;
  observedAt: string;
};

export type ConnectionStatus = "disconnected" | "connecting" | "connected" | "reconnecting";

const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 15000;
const MAX_RECONNECT_ATTEMPTS = 10;

function buildWsUrl(apiBaseUrl: string, accessToken: string, assetTagId?: string): string {
  const wsBase = apiBaseUrl.replace(/^http/, "ws");
  const params = new URLSearchParams({ access_token: accessToken });
  if (assetTagId) {
    params.set("asset_tag_id", assetTagId);
  }
  return `${wsBase}/ws/locations?${params.toString()}`;
}

export function useSelfLocation(options: {
  apiBaseUrl: string;
  accessToken: string;
  enabled: boolean;
  assetTagId?: string;
  floorId?: string;
  onLocationUpdate?: (location: SelfLocationState) => void;
}) {
  const { apiBaseUrl, accessToken, enabled, assetTagId, floorId, onLocationUpdate } = options;

  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>("disconnected");
  const [location, setLocation] = useState<SelfLocationState | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const enabledRef = useRef(enabled);
  const floorIdRef = useRef(floorId);
  const onLocationUpdateRef = useRef(onLocationUpdate);

  enabledRef.current = enabled;
  floorIdRef.current = floorId;
  onLocationUpdateRef.current = onLocationUpdate;

  const clearConnection = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!enabledRef.current) {
      return;
    }

    clearConnection();
    setConnectionStatus("connecting");

    const url = buildWsUrl(apiBaseUrl, accessToken, assetTagId);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectCountRef.current = 0;
      setConnectionStatus("connected");
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string) as {
          event: string;
          location: AssetLocationRecord;
        };

        if (data.event !== "location.updated" || !data.location.point) {
          return;
        }

        const targetFloorId = floorIdRef.current;
        if (targetFloorId && data.location.floor_id !== targetFloorId) {
          return;
        }

        const newState: SelfLocationState = {
          x: data.location.point.x,
          y: data.location.point.y,
          confidenceLevel: data.location.confidence_level,
          confidenceScore: data.location.confidence_score,
          precisionMeters: data.location.precision_meters,
          floorId: data.location.floor_id,
          observedAt: data.location.observed_at
        };

        setLocation(newState);
        onLocationUpdateRef.current?.(newState);
      } catch {
        // Ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnectionStatus((prev) => {
        if (prev === "disconnected") {
          return "disconnected";
        }
        return "reconnecting";
      });

      const attempt = reconnectCountRef.current + 1;
      reconnectCountRef.current = attempt;

      if (attempt > MAX_RECONNECT_ATTEMPTS) {
        setConnectionStatus("disconnected");
        return;
      }

      const delay = Math.min(
        RECONNECT_BASE_MS * Math.pow(2, attempt - 1),
        RECONNECT_MAX_MS
      );

      reconnectTimerRef.current = setTimeout(() => {
        if (enabledRef.current) {
          connect();
        }
      }, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [apiBaseUrl, accessToken, assetTagId, clearConnection]);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      clearConnection();
      setConnectionStatus("disconnected");
      setLocation(null);
      reconnectCountRef.current = 0;
    }

    return () => {
      clearConnection();
    };
  }, [enabled, connect, clearConnection]);

  return { location, connectionStatus };
}
