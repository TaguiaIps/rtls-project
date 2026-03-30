import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  ImageBackground,
  LayoutChangeEvent,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import type { AssetTagRecord, FloorDetail, SiteRecord, SpatialPoint } from "@rtls/contracts";

import {
  buildFloorPlanFileUrl,
  fetchAdminContext,
  fetchFloorDetail
} from "./adminApi";
import {
  buildCalibrationProgress,
  buildCalibrationWaypoints,
  buildCommissioningSummary,
  describeTargetKind,
  extractIdentifierFromQrPayload,
  formatElapsedDuration,
  resolveCommissioningTarget,
  type CommissioningSessionSummary,
  upsertCommissioningSummary
} from "./commissioning";
import { MobileQrScanner } from "./MobileQrScanner";
import { normalizeApiBaseUrl } from "./session";
import {
  loadCommissioningSummaries,
  saveCommissioningSummaries
} from "./storage";

type CommissioningScreenProps = {
  apiBaseUrl: string;
  accessToken: string;
};

export function CommissioningScreen({
  apiBaseUrl,
  accessToken
}: CommissioningScreenProps) {
  const [sites, setSites] = useState<SiteRecord[]>([]);
  const [assets, setAssets] = useState<AssetTagRecord[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState("");
  const [selectedFloorId, setSelectedFloorId] = useState("");
  const [floorDetail, setFloorDetail] = useState<FloorDetail | null>(null);
  const [loadingContext, setLoadingContext] = useState(false);
  const [contextLoaded, setContextLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scannerValue, setScannerValue] = useState("");
  const [scannerPanelVisible, setScannerPanelVisible] = useState(false);
  const [selectedZoneId, setSelectedZoneId] = useState<string | null>(null);
  const [capturedPoints, setCapturedPoints] = useState<SpatialPoint[]>([]);
  const [currentPosition, setCurrentPosition] = useState<SpatialPoint | null>(null);
  const [calibrationStartedAt, setCalibrationStartedAt] = useState<string | null>(null);
  const [sessionSummaries, setSessionSummaries] = useState<CommissioningSessionSummary[]>([]);
  const [mapSize, setMapSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    let cancelled = false;

    void loadCommissioningSummaries().then((entries) => {
      if (!cancelled) {
        setSessionSummaries(entries);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    void saveCommissioningSummaries(sessionSummaries);
  }, [sessionSummaries]);

  const normalizedApiBaseUrl = normalizeApiBaseUrl(apiBaseUrl);
  const canLoadContext = Boolean(normalizedApiBaseUrl && accessToken.trim());
  const selectedSite = sites.find((site) => site.id === selectedSiteId) ?? null;
  const selectedZone =
    floorDetail?.areas.find((area) => area.id === selectedZoneId) ?? null;
  const resolvedTarget =
    floorDetail !== null
      ? resolveCommissioningTarget(scannerValue, floorDetail.gateways, assets)
      : null;
  const waypoints = buildCalibrationWaypoints(floorDetail, selectedZoneId);
  const progress = buildCalibrationProgress(waypoints, capturedPoints);

  useEffect(() => {
    if (!selectedSite && sites.length > 0) {
      setSelectedSiteId(sites[0].id);
    }
  }, [selectedSite, sites]);

  useEffect(() => {
    if (!selectedSite) {
      setSelectedFloorId("");
      return;
    }

    const currentFloorStillExists = selectedSite.floors.some((floor) => floor.id === selectedFloorId);
    if (!currentFloorStillExists) {
      setSelectedFloorId(selectedSite.floors[0]?.id ?? "");
    }
  }, [selectedFloorId, selectedSite]);

  useEffect(() => {
    setSelectedZoneId(null);
    setCapturedPoints([]);
    setCurrentPosition(null);
    setCalibrationStartedAt(null);
  }, [selectedFloorId]);

  const loadContext = async (floorIdOverride?: string) => {
    if (!canLoadContext) {
      return;
    }

    setLoadingContext(true);
    setError(null);
    try {
      const adminContext = await fetchAdminContext(normalizedApiBaseUrl, accessToken);
      setSites(adminContext.sites);
      setAssets(adminContext.assets);

      const nextSiteId =
        selectedSiteId || adminContext.sites[0]?.id || "";
      const nextSite =
        adminContext.sites.find((site) => site.id === nextSiteId) ?? adminContext.sites[0] ?? null;
      const nextFloorId =
        floorIdOverride || selectedFloorId || nextSite?.floors[0]?.id || "";

      setSelectedSiteId(nextSite?.id ?? "");
      setSelectedFloorId(nextFloorId);

      if (nextFloorId) {
        const nextFloorDetail = await fetchFloorDetail(
          normalizedApiBaseUrl,
          accessToken,
          nextFloorId
        );
        setFloorDetail(nextFloorDetail);
      } else {
        setFloorDetail(null);
      }

      setContextLoaded(true);
    } catch (contextError) {
      setFloorDetail(null);
      setContextLoaded(false);
      setError(
        contextError instanceof Error
          ? contextError.message
          : "Commissioning context failed to load."
      );
    } finally {
      setLoadingContext(false);
    }
  };

  const handleFloorSelection = async (floorId: string) => {
    setSelectedFloorId(floorId);
    if (!canLoadContext) {
      return;
    }

    setLoadingContext(true);
    setError(null);
    try {
      const nextFloorDetail = await fetchFloorDetail(
        normalizedApiBaseUrl,
        accessToken,
        floorId
      );
      setFloorDetail(nextFloorDetail);
    } catch (floorError) {
      setFloorDetail(null);
      setError(
        floorError instanceof Error
          ? floorError.message
          : "Floor detail failed to load."
      );
    } finally {
      setLoadingContext(false);
    }
  };

  const handleStartCalibration = () => {
    if (!resolvedTarget || !floorDetail || !selectedSite) {
      return;
    }

    setCalibrationStartedAt(new Date().toISOString());
    setCapturedPoints([]);
    setCurrentPosition(waypoints[0]?.point ?? null);
    setError(null);
  };

  const handleScannerCapture = (payload: string) => {
    setScannerValue(extractIdentifierFromQrPayload(payload));
    setScannerPanelVisible(false);
    setError(null);
  };

  const handleMapPress = (event: {
    nativeEvent: { locationX: number; locationY: number };
  }) => {
    if (!calibrationStartedAt || mapSize.width <= 0 || mapSize.height <= 0) {
      return;
    }

    const point = {
      x: Number((event.nativeEvent.locationX / mapSize.width).toFixed(4)),
      y: Number((event.nativeEvent.locationY / mapSize.height).toFixed(4))
    };

    setCurrentPosition(point);
    setCapturedPoints((current) => [...current, point]);
  };

  const handleCompleteCalibration = () => {
    if (!calibrationStartedAt || !resolvedTarget || !floorDetail || !selectedSite) {
      return;
    }

    const completedAt = new Date().toISOString();
    const summary = buildCommissioningSummary({
      target: resolvedTarget,
      site: selectedSite,
      floor: floorDetail,
      zone: selectedZone,
      startedAt: calibrationStartedAt,
      completedAt,
      captures: capturedPoints,
      progress
    });

    setSessionSummaries((current) => upsertCommissioningSummary(current, summary));
    setCalibrationStartedAt(null);
  };

  const handleMapLayout = (event: LayoutChangeEvent) => {
    setMapSize({
      width: event.nativeEvent.layout.width,
      height: event.nativeEvent.layout.height
    });
  };

  const zoneOptions = floorDetail?.areas.filter((area) => area.area_type !== "restricted_zone") ?? [];
  const canStartCalibration =
    Boolean(resolvedTarget && floorDetail?.floor_plan) &&
    (zoneOptions.length === 0 || selectedZoneId !== null);

  const currentSummaryPreview =
    calibrationStartedAt && resolvedTarget && floorDetail && selectedSite
      ? buildCommissioningSummary({
          target: resolvedTarget,
          site: selectedSite,
          floor: floorDetail,
          zone: selectedZone,
          startedAt: calibrationStartedAt,
          completedAt: new Date().toISOString(),
          captures: capturedPoints,
          progress
        })
      : null;

  return (
    <>
      <View style={styles.heroCard}>
        <Text style={styles.eyebrow}>Mobile Commissioning</Text>
        <Text style={styles.title}>Scan, assign, and walk the floor.</Text>
        <Text style={styles.body}>
          Load an admin floor, resolve a device identifier, assign it to the right room, and
          capture a blue-dot calibration walkthrough without leaving the mobile workflow.
        </Text>
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Admin Context</Text>
        <Text style={styles.helperText}>
          Load the delivered admin sites, floors, zones, gateways, and asset registry with the
          current Administrator session.
        </Text>
        <Pressable
          disabled={!canLoadContext || loadingContext}
          onPress={() => void loadContext()}
          style={({ pressed }) => [
            styles.primaryButton,
            (!canLoadContext || loadingContext) && styles.primaryButtonDisabled,
            pressed && canLoadContext && !loadingContext ? styles.primaryButtonPressed : null
          ]}
        >
          {loadingContext ? (
            <ActivityIndicator color="#f8fafc" />
          ) : (
            <Text style={styles.primaryButtonLabel}>
              {contextLoaded ? "Refresh Context" : "Load Context"}
            </Text>
          )}
        </Pressable>
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        {!sites.length && !error ? (
          <Text style={styles.helperText}>No admin context loaded yet.</Text>
        ) : null}
        {sites.length ? (
          <View style={styles.chipWrap}>
            {sites.map((site) => (
              <Pressable
                key={site.id}
                onPress={() => setSelectedSiteId(site.id)}
                style={({ pressed }) => [
                  styles.chip,
                  selectedSiteId === site.id && styles.chipSelected,
                  pressed ? styles.resultCardPressed : null
                ]}
              >
                <Text style={styles.chipLabel}>{site.name}</Text>
              </Pressable>
            ))}
          </View>
        ) : null}
        {selectedSite?.floors.length ? (
          <View style={styles.chipWrap}>
            {selectedSite.floors.map((floor) => (
              <Pressable
                key={floor.id}
                onPress={() => void handleFloorSelection(floor.id)}
                style={({ pressed }) => [
                  styles.chip,
                  selectedFloorId === floor.id && styles.chipSelected,
                  pressed ? styles.resultCardPressed : null
                ]}
              >
                <Text style={styles.chipLabel}>
                  {floor.name}
                  {floor.level_label ? ` · ${floor.level_label}` : ""}
                </Text>
              </Pressable>
            ))}
          </View>
        ) : null}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Scanner Input</Text>
        <Text style={styles.helperText}>
          Open the camera scanner to capture a QR code directly on device, or keep the fallback
          field for simulator testing and external scanner input.
        </Text>
        <View style={styles.buttonRow}>
          <Pressable
            onPress={() => setScannerPanelVisible((current) => !current)}
            style={({ pressed }) => [
              styles.primaryButton,
              pressed ? styles.primaryButtonPressed : null
            ]}
          >
            <Text style={styles.primaryButtonLabel}>
              {scannerPanelVisible ? "Hide Camera Scanner" : "Open Camera Scanner"}
            </Text>
          </Pressable>
        </View>
        {scannerPanelVisible ? (
          <MobileQrScanner
            onClose={() => setScannerPanelVisible(false)}
            onScan={handleScannerCapture}
          />
        ) : null}
        <TextInput
          autoCapitalize="characters"
          autoCorrect={false}
          onChangeText={setScannerValue}
          placeholder="Scan or enter gateway/tag identifier"
          placeholderTextColor="#64748b"
          style={styles.input}
          value={scannerValue}
        />
        {!resolvedTarget ? (
          <Text style={styles.helperText}>No device identifier resolved yet.</Text>
        ) : (
          <View style={styles.resultCard}>
            <View style={styles.resultHeader}>
              <Text style={styles.resultTitle}>{resolvedTarget.displayName}</Text>
              <Text style={styles.badge}>{describeTargetKind(resolvedTarget.kind)}</Text>
            </View>
            <Text style={styles.resultMeta}>{resolvedTarget.identifier}</Text>
            <Text style={styles.resultMeta}>{resolvedTarget.description}</Text>
            {resolvedTarget.kind === "unknown" ? (
              <Text style={styles.warningText}>
                This identifier is not present in the current registry context.
              </Text>
            ) : null}
          </View>
        )}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Zone Assignment</Text>
        {!floorDetail ? (
          <Text style={styles.helperText}>Load a floor before assigning a room or zone.</Text>
        ) : !zoneOptions.length ? (
          <Text style={styles.helperText}>This floor does not yet have supported zones.</Text>
        ) : (
          <>
            <Text style={styles.helperText}>
              Assign the current device to the room or zone you are commissioning before starting
              the calibration walk.
            </Text>
            <View style={styles.chipWrap}>
              {zoneOptions.map((area) => (
                <Pressable
                  key={area.id}
                  onPress={() => setSelectedZoneId(area.id)}
                  style={({ pressed }) => [
                    styles.chip,
                    selectedZoneId === area.id && styles.chipSelected,
                    pressed ? styles.resultCardPressed : null
                  ]}
                >
                  <Text style={styles.chipLabel}>{area.name}</Text>
                </Pressable>
              ))}
            </View>
          </>
        )}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Calibration Walkthrough</Text>
        {!floorDetail?.floor_plan ? (
          <Text style={styles.helperText}>
            Load a calibrated floor plan before starting the blue-dot walkthrough.
          </Text>
        ) : (
          <>
            <Text style={styles.helperText}>
              Tap the floor preview as you move to capture your current position and advance the
              blue-dot calibration route.
            </Text>
            <Pressable
              onLayout={handleMapLayout}
              onPress={handleMapPress}
              style={[
                styles.mapFrame,
                {
                  aspectRatio:
                    floorDetail.floor_plan.width_px / floorDetail.floor_plan.height_px
                }
              ]}
            >
              <ImageBackground
                imageStyle={styles.mapImage}
                resizeMode="cover"
                source={{
                  uri: buildFloorPlanFileUrl(
                    normalizedApiBaseUrl,
                    floorDetail.floor_plan.file_download_path
                  ),
                  headers: {
                    Authorization: `Bearer ${accessToken.trim()}`
                  }
                }}
                style={styles.mapContent}
              >
                {floorDetail.gateways.map((gateway) => (
                  <View
                    key={gateway.id}
                    style={[
                      styles.gatewayMarker,
                      markerPositionStyle(gateway.placement, 12)
                    ]}
                  />
                ))}
                {waypoints.map((waypoint) => (
                  <View
                    key={waypoint.id}
                    style={[
                      styles.waypointMarker,
                      progress.nextWaypoint?.id === waypoint.id && styles.waypointMarkerActive,
                      markerPositionStyle(waypoint.point, 18)
                    ]}
                  />
                ))}
                {selectedZone ? (
                  <View
                    style={[
                      styles.zoneMarker,
                      markerPositionStyle(waypoints[0]?.point ?? { x: 0.5, y: 0.5 }, 22)
                    ]}
                  />
                ) : null}
                {currentPosition ? (
                  <View
                    style={[
                      styles.blueDot,
                      markerPositionStyle(currentPosition, 20)
                    ]}
                  />
                ) : null}
              </ImageBackground>
            </Pressable>

            <View style={styles.resultCard}>
              <Text style={styles.resultTitle}>Progress</Text>
              <Text style={styles.resultMeta}>
                {progress.completedCount}/{progress.totalCount} checkpoints reached
              </Text>
              <Text style={styles.resultMeta}>
                Samples captured {capturedPoints.length}
              </Text>
              <Text style={styles.resultMeta}>
                {progress.nextWaypoint
                  ? `Next checkpoint: ${progress.nextWaypoint.label}`
                  : "All route checkpoints are complete."}
              </Text>
            </View>

            <View style={styles.buttonRow}>
              <Pressable
                disabled={!canStartCalibration}
                onPress={handleStartCalibration}
                style={({ pressed }) => [
                  styles.primaryButton,
                  !canStartCalibration && styles.primaryButtonDisabled,
                  pressed && canStartCalibration ? styles.primaryButtonPressed : null
                ]}
              >
                <Text style={styles.primaryButtonLabel}>Start Calibration</Text>
              </Pressable>
              <Pressable
                disabled={!calibrationStartedAt}
                onPress={handleCompleteCalibration}
                style={({ pressed }) => [
                  styles.secondaryButton,
                  !calibrationStartedAt && styles.secondaryButtonDisabled,
                  pressed && calibrationStartedAt ? styles.secondaryButtonPressed : null
                ]}
              >
                <Text style={styles.secondaryButtonLabel}>Complete Session</Text>
              </Pressable>
            </View>
          </>
        )}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Session Summary</Text>
        {!currentSummaryPreview ? (
          <Text style={styles.helperText}>Start calibration to build a session summary.</Text>
        ) : (
          <View style={styles.resultCard}>
            <Text style={styles.resultTitle}>{currentSummaryPreview.target_display_name}</Text>
            <Text style={styles.resultMeta}>
              {currentSummaryPreview.floor_name}
              {currentSummaryPreview.zone_name ? ` · ${currentSummaryPreview.zone_name}` : ""}
            </Text>
            <Text style={styles.resultMeta}>
              Elapsed {formatElapsedDuration(currentSummaryPreview.elapsed_seconds)}
            </Text>
            <Text style={styles.resultMeta}>
              Samples {currentSummaryPreview.sample_count} · Waypoints{" "}
              {currentSummaryPreview.completed_waypoints}/{currentSummaryPreview.total_waypoints}
            </Text>
          </View>
        )}
        {sessionSummaries.length ? (
          <View style={styles.resultsList}>
            {sessionSummaries.map((summary) => (
              <View key={`${summary.target_identifier}:${summary.floor_id}`} style={styles.recentCard}>
                <View style={styles.resultHeader}>
                  <Text style={styles.resultTitle}>{summary.target_display_name}</Text>
                  <Text style={styles.badge}>{describeTargetKind(summary.target_kind)}</Text>
                </View>
                <Text style={styles.resultMeta}>
                  {summary.floor_name}
                  {summary.zone_name ? ` · ${summary.zone_name}` : ""}
                </Text>
                <Text style={styles.resultMeta}>
                  {summary.sample_count} samples · {summary.completed_waypoints}/
                  {summary.total_waypoints} checkpoints
                </Text>
                <Text style={styles.resultMeta}>
                  Completed {formatElapsedDuration(summary.elapsed_seconds)}
                </Text>
              </View>
            ))}
          </View>
        ) : null}
      </View>
    </>
  );
}

function markerPositionStyle(point: SpatialPoint, size: number) {
  return {
    left: `${point.x * 100}%`,
    top: `${point.y * 100}%`,
    marginLeft: -size / 2,
    marginTop: -size / 2
  } as const;
}

const styles = StyleSheet.create({
  heroCard: {
    backgroundColor: "#101729",
    borderRadius: 24,
    paddingHorizontal: 20,
    paddingVertical: 22,
    borderWidth: 1,
    borderColor: "#224564"
  },
  panel: {
    backgroundColor: "#0f172a",
    borderRadius: 20,
    paddingHorizontal: 18,
    paddingVertical: 18,
    borderWidth: 1,
    borderColor: "#1e293b",
    gap: 10
  },
  eyebrow: {
    color: "#f59e0b",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 1.2,
    textTransform: "uppercase",
    marginBottom: 10
  },
  title: {
    color: "#f8fafc",
    fontSize: 30,
    fontWeight: "700",
    lineHeight: 36,
    marginBottom: 12
  },
  body: {
    color: "#cbd5e1",
    fontSize: 16,
    lineHeight: 24
  },
  panelTitle: {
    color: "#f8fafc",
    fontSize: 20,
    fontWeight: "700"
  },
  helperText: {
    color: "#94a3b8",
    fontSize: 14,
    lineHeight: 20
  },
  input: {
    backgroundColor: "#08101e",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#233248",
    color: "#f8fafc",
    fontSize: 15,
    paddingHorizontal: 14,
    paddingVertical: 12
  },
  primaryButton: {
    backgroundColor: "#0ea5e9",
    borderRadius: 14,
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16
  },
  primaryButtonDisabled: {
    backgroundColor: "#334155"
  },
  primaryButtonPressed: {
    opacity: 0.9
  },
  primaryButtonLabel: {
    color: "#f8fafc",
    fontSize: 15,
    fontWeight: "700"
  },
  secondaryButton: {
    backgroundColor: "#172033",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#35506f",
    minHeight: 48,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 16
  },
  secondaryButtonDisabled: {
    borderColor: "#334155",
    opacity: 0.6
  },
  secondaryButtonPressed: {
    opacity: 0.92
  },
  secondaryButtonLabel: {
    color: "#dbeafe",
    fontSize: 15,
    fontWeight: "700"
  },
  errorText: {
    color: "#fca5a5",
    fontSize: 14
  },
  warningText: {
    color: "#fbbf24",
    fontSize: 14
  },
  chipWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 10
  },
  chip: {
    backgroundColor: "#122234",
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#1f3450",
    paddingHorizontal: 12,
    paddingVertical: 8
  },
  chipSelected: {
    borderColor: "#38bdf8",
    backgroundColor: "#0f3046"
  },
  chipLabel: {
    color: "#e2e8f0",
    fontSize: 13,
    fontWeight: "600"
  },
  resultCard: {
    backgroundColor: "#111c31",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1f3450",
    paddingHorizontal: 14,
    paddingVertical: 14,
    gap: 4
  },
  recentCard: {
    backgroundColor: "#111c31",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1f3450",
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 4
  },
  resultHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10
  },
  resultTitle: {
    color: "#f8fafc",
    fontSize: 16,
    fontWeight: "700",
    flex: 1
  },
  resultMeta: {
    color: "#cbd5e1",
    fontSize: 14,
    lineHeight: 20
  },
  badge: {
    color: "#fde68a",
    backgroundColor: "#3a2810",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    overflow: "hidden",
    fontSize: 12,
    fontWeight: "700"
  },
  mapFrame: {
    overflow: "hidden",
    borderRadius: 18,
    borderWidth: 1,
    borderColor: "#29445f",
    backgroundColor: "#0b1220"
  },
  mapContent: {
    flex: 1,
    minHeight: 240
  },
  mapImage: {
    opacity: 0.55
  },
  gatewayMarker: {
    position: "absolute",
    width: 12,
    height: 12,
    borderRadius: 3,
    backgroundColor: "#f59e0b",
    borderWidth: 1,
    borderColor: "#fef3c7"
  },
  waypointMarker: {
    position: "absolute",
    width: 18,
    height: 18,
    borderRadius: 9,
    borderWidth: 2,
    borderColor: "#f97316",
    backgroundColor: "rgba(249, 115, 22, 0.25)"
  },
  waypointMarkerActive: {
    borderColor: "#fb7185",
    backgroundColor: "rgba(251, 113, 133, 0.35)"
  },
  zoneMarker: {
    position: "absolute",
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: "#34d399",
    backgroundColor: "rgba(52, 211, 153, 0.2)"
  },
  blueDot: {
    position: "absolute",
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: "#dbeafe",
    backgroundColor: "#2563eb"
  },
  buttonRow: {
    flexDirection: "row",
    gap: 10
  },
  resultsList: {
    gap: 10
  },
  resultCardPressed: {
    opacity: 0.92
  }
});
