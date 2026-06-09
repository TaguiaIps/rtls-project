import { useEffect, useRef, useState } from "react";
import type { ViewStyle } from "react-native";
import { View } from "react-native";
import type { LocationConfidenceLevel } from "@rtls/contracts";

export type SelfLocationMarkerProps = {
  x: number;
  y: number;
  confidenceLevel: LocationConfidenceLevel;
  confidenceScore: number;
  precisionMeters: number | null;
  mapWidth: number;
  mapHeight: number;
  floorPixelsPerMeter?: number | null;
};

const CONFIDENCE_CONFIG: Record<LocationConfidenceLevel, { dotColor: string; ringColor: string; ringAlpha: number }> = {
  high: { dotColor: "#2563eb", ringColor: "#3b82f6", ringAlpha: 0.3 },
  medium: { dotColor: "#7c3aed", ringColor: "#8b5cf6", ringAlpha: 0.35 },
  low: { dotColor: "#dc2626", ringColor: "#ef4444", ringAlpha: 0.4 }
};

const MIN_RING_DP = 20;
const MAX_RING_DP = 80;

function precisionToRingDp(
  precisionMeters: number | null,
  floorPixelsPerMeter: number | null,
  mapWidth: number
): number {
  if (precisionMeters == null || !floorPixelsPerMeter || mapWidth <= 0) {
    return MIN_RING_DP;
  }

  const ringPx = precisionMeters * floorPixelsPerMeter * (mapWidth / 1000);
  return Math.round(Math.max(MIN_RING_DP, Math.min(MAX_RING_DP, ringPx)));
}

export function SelfLocationMarker({
  x,
  y,
  confidenceLevel,
  precisionMeters,
  mapWidth,
  mapHeight,
  floorPixelsPerMeter
}: SelfLocationMarkerProps) {
  const [smoothed, setSmoothed] = useState({ x, y });
  const prevRef = useRef({ x, y });
  const prevTimestamp = useRef(Date.now());

  useEffect(() => {
    const now = Date.now();
    const dt = now - prevTimestamp.current;

    if (dt > 0 && dt < 5000) {
      const alpha = Math.min(0.8, dt / 300);
      setSmoothed((prev) => ({
        x: prev.x + (x - prev.x) * alpha,
        y: prev.y + (y - prev.y) * alpha
      }));
    } else {
      setSmoothed({ x, y });
    }

    prevRef.current = { x, y };
    prevTimestamp.current = now;
  }, [x, y]);

  const config = CONFIDENCE_CONFIG[confidenceLevel] ?? CONFIDENCE_CONFIG.low;
  const ringDp = precisionToRingDp(precisionMeters, floorPixelsPerMeter, mapWidth);

  const markerStyle: ViewStyle = {
    position: "absolute",
    left: `${smoothed.x * 100}%`,
    top: `${smoothed.y * 100}%`,
    marginLeft: -ringDp / 2,
    marginTop: -ringDp / 2,
    width: ringDp,
    height: ringDp,
    borderRadius: ringDp / 2,
    borderWidth: 1.5,
    borderColor: config.ringColor,
    backgroundColor: `rgba(59, 130, 246, ${config.ringAlpha})`
  };

  const dotDp = 16;
  const dotStyle: ViewStyle = {
    position: "absolute",
    left: "50%",
    top: "50%",
    marginLeft: -dotDp / 2,
    marginTop: -dotDp / 2,
    width: dotDp,
    height: dotDp,
    borderRadius: dotDp / 2,
    borderWidth: 2,
    borderColor: "#dbeafe",
    backgroundColor: config.dotColor
  };

  return (
    <View style={markerStyle}>
      <View style={dotStyle} />
    </View>
  );
}
