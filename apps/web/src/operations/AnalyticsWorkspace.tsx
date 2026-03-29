import type {
  AnalyticsDwellReportRecord,
  AnalyticsHeatmapRecord,
  AnalyticsRoundTripReportRecord,
  AnalyticsSlaTrendRecord,
  AnalyticsTrajectoryRecord,
  AssetLocationRecord,
  FloorDetail,
  FloorPlanAsset,
  SpatialAreaRecord
} from "@rtls/contracts";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { useOperationsShell } from "./OperationsShell";

type AnalyticsReportKind = "trajectory" | "heatmap" | "dwell" | "round_trip" | "sla";
type AnalyticsReportData =
  | AnalyticsTrajectoryRecord
  | AnalyticsHeatmapRecord
  | AnalyticsDwellReportRecord
  | AnalyticsRoundTripReportRecord
  | AnalyticsSlaTrendRecord;

const DEFAULT_MAP_WIDTH = 1200;
const DEFAULT_MAP_HEIGHT = 720;

export function AnalyticsWorkspacePage() {
  const { fetchWithAuth, selectedFloor, selectedSite, setSearchParam, shellSearchParams } = useOperationsShell();
  const [floorDetail, setFloorDetail] = useState<FloorDetail | null>(null);
  const [liveAssets, setLiveAssets] = useState<AssetLocationRecord[]>([]);
  const [reportData, setReportData] = useState<AnalyticsReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const report = (shellSearchParams.get("analytics_report") as AnalyticsReportKind | null) ?? "trajectory";
  const startAt = shellSearchParams.get("analytics_start_at");
  const endAt = shellSearchParams.get("analytics_end_at");
  const assetTagId = shellSearchParams.get("analytics_asset_tag_id");
  const assetCategory = shellSearchParams.get("analytics_asset_category");
  const zoneId = shellSearchParams.get("analytics_zone_id");
  const originZoneId = shellSearchParams.get("analytics_origin_zone_id");
  const destinationZoneId = shellSearchParams.get("analytics_destination_zone_id");
  const tableAreaId = shellSearchParams.get("analytics_table_area_id");
  const bucketMinutes = shellSearchParams.get("analytics_bucket_minutes") ?? "60";
  const floorImageUrl = useAuthorizedFloorPlan(floorDetail?.floor_plan ?? null, fetchWithAuth);

  useEffect(() => {
    if (startAt && endAt && shellSearchParams.get("analytics_report")) {
      return;
    }
    const now = new Date();
    const defaultEnd = now.toISOString();
    const defaultStart = new Date(now.getTime() - 4 * 60 * 60 * 1000).toISOString();
    if (!shellSearchParams.get("analytics_report")) {
      setSearchParam("analytics_report", "trajectory");
    }
    if (!startAt) {
      setSearchParam("analytics_start_at", defaultStart);
    }
    if (!endAt) {
      setSearchParam("analytics_end_at", defaultEnd);
    }
  }, [endAt, setSearchParam, shellSearchParams, startAt]);

  useEffect(() => {
    let cancelled = false;

    async function loadFloorContext() {
      if (!selectedFloor?.id) {
        setFloorDetail(null);
        setLiveAssets([]);
        return;
      }

      try {
        const [detailResponse, assetResponse] = await Promise.all([
          fetchWithAuth(`/api/admin/floors/${selectedFloor.id}`),
          fetchWithAuth(`/api/locations/live?floor_id=${selectedFloor.id}`)
        ]);
        if (!detailResponse.ok || !assetResponse.ok) {
          throw new Error("Unable to load analytics context");
        }
        const detailPayload = (await detailResponse.json()) as FloorDetail;
        const assetPayload = (await assetResponse.json()) as AssetLocationRecord[];
        if (!cancelled) {
          setFloorDetail(detailPayload);
          setLiveAssets(assetPayload);
        }
      } catch {
        if (!cancelled) {
          setFloorDetail(null);
          setLiveAssets([]);
        }
      }
    }

    void loadFloorContext();
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth, selectedFloor?.id]);

  const zoneOptions = useMemo(
    () => (floorDetail?.areas ?? []).filter((area) => area.area_type === "zone"),
    [floorDetail?.areas]
  );
  const tableOptions = useMemo(
    () => (floorDetail?.areas ?? []).filter((area) => area.area_type === "table" && area.sla_eligible),
    [floorDetail?.areas]
  );

  const missingPrompt = getMissingPrompt({
    report,
    assetTagId,
    originZoneId,
    destinationZoneId,
    tableAreaId
  });

  useEffect(() => {
    let cancelled = false;

    async function loadReport() {
      if (!selectedFloor?.id || !startAt || !endAt || missingPrompt) {
        setReportData(null);
        setError(null);
        setLoading(false);
        return;
      }

      setLoading(true);
      setReportData(null);
      try {
        const params = new URLSearchParams({
          floor_id: selectedFloor.id,
          start_at: startAt,
          end_at: endAt
        });
        let endpoint = "/api/analytics/trajectory";

        if (report === "trajectory") {
          params.set("asset_tag_id", assetTagId ?? "");
        } else if (report === "heatmap") {
          endpoint = "/api/analytics/heatmap";
          if (assetCategory) {
            params.set("asset_category", assetCategory);
          }
        } else if (report === "dwell") {
          endpoint = "/api/analytics/dwells";
          if (assetCategory) {
            params.set("asset_category", assetCategory);
          }
          if (zoneId) {
            params.set("zone_id", zoneId);
          }
        } else if (report === "round_trip") {
          endpoint = "/api/analytics/round-trips";
          params.set("origin_zone_id", originZoneId ?? "");
          params.set("destination_zone_id", destinationZoneId ?? "");
          if (assetCategory) {
            params.set("asset_category", assetCategory);
          }
        } else {
          endpoint = "/api/analytics/sla-trends";
          params.set("table_area_id", tableAreaId ?? "");
          params.set("bucket_minutes", bucketMinutes);
        }

        const response = await fetchWithAuth(`${endpoint}?${params.toString()}`);
        if (!response.ok) {
          const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
          throw new Error(payload?.detail ?? "Unable to load analytics report");
        }

        const payload = (await response.json()) as AnalyticsReportData;
        if (!cancelled) {
          setReportData(payload);
          setError(null);
        }
      } catch (reportError) {
        if (!cancelled) {
          setReportData(null);
          setError(reportError instanceof Error ? reportError.message : "Unable to load analytics report.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadReport();
    return () => {
      cancelled = true;
    };
  }, [
    assetCategory,
    assetTagId,
    bucketMinutes,
    destinationZoneId,
    endAt,
    fetchWithAuth,
    missingPrompt,
    originZoneId,
    report,
    selectedFloor?.id,
    startAt,
    tableAreaId,
    zoneId
  ]);

  return (
    <div className="analytics-layout">
      <header className="panel analytics-header">
        <div>
          <p className="eyebrow">Analytics</p>
          <h2>{selectedFloor?.name ?? "Awaiting mapped floor"}</h2>
          <p className="muted-text">
            Historical trajectory replay, heatmaps, dwell reports, round-trip analysis, and table SLA trends for{" "}
            {selectedSite?.name ?? "the selected site"}.
          </p>
        </div>
        <div className="analytics-switcher" role="tablist" aria-label="Analytics reports">
          {[
            ["trajectory", "Trajectory"],
            ["heatmap", "Heatmap"],
            ["dwell", "Dwell"],
            ["round_trip", "Round-Trip"],
            ["sla", "SLA Trends"]
          ].map(([value, label]) => (
            <button
              key={value}
              className={report === value ? "analytics-switcher__button analytics-switcher__button--active" : "analytics-switcher__button"}
              onClick={() => setSearchParam("analytics_report", value)}
              type="button"
            >
              {label}
            </button>
          ))}
        </div>
      </header>

      <div className="analytics-grid">
        <aside className="panel analytics-controls">
          <div className="stack-card__header">
            <div>
              <p className="eyebrow">Parameters</p>
              <h2>Report scope</h2>
            </div>
          </div>

          <label>
            <span>Report start</span>
            <input
              aria-label="Report start"
              type="datetime-local"
              value={toInputDateTime(startAt)}
              onChange={(event) => setSearchParam("analytics_start_at", toIsoString(event.target.value))}
            />
          </label>
          <label>
            <span>Report end</span>
            <input
              aria-label="Report end"
              type="datetime-local"
              value={toInputDateTime(endAt)}
              onChange={(event) => setSearchParam("analytics_end_at", toIsoString(event.target.value))}
            />
          </label>

          {report === "trajectory" ? (
            <label>
              <span>Tracked asset</span>
              <select
                aria-label="Tracked asset"
                value={assetTagId ?? ""}
                onChange={(event) => setSearchParam("analytics_asset_tag_id", event.target.value || null)}
              >
                <option value="">Select one asset</option>
                {liveAssets.map((asset) => (
                  <option key={asset.asset_tag_id} value={asset.asset_tag_id}>
                    {asset.display_name}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {report === "heatmap" || report === "dwell" || report === "round_trip" ? (
            <label>
              <span>Asset cohort</span>
              <select
                aria-label="Asset cohort"
                value={assetCategory ?? ""}
                onChange={(event) => setSearchParam("analytics_asset_category", event.target.value || null)}
              >
                <option value="">All categories</option>
                {uniqueValues(liveAssets.map((asset) => asset.asset_category)).map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {report === "dwell" ? (
            <label>
              <span>Zone</span>
              <select
                aria-label="Zone"
                value={zoneId ?? ""}
                onChange={(event) => setSearchParam("analytics_zone_id", event.target.value || null)}
              >
                <option value="">All zones</option>
                {zoneOptions.map((zone) => (
                  <option key={zone.id} value={zone.id}>
                    {zone.name}
                  </option>
                ))}
              </select>
            </label>
          ) : null}

          {report === "round_trip" ? (
            <>
              <label>
                <span>Origin zone</span>
                <select
                  aria-label="Origin zone"
                  value={originZoneId ?? ""}
                  onChange={(event) => setSearchParam("analytics_origin_zone_id", event.target.value || null)}
                >
                  <option value="">Select origin</option>
                  {zoneOptions.map((zone) => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Destination zone</span>
                <select
                  aria-label="Destination zone"
                  value={destinationZoneId ?? ""}
                  onChange={(event) => setSearchParam("analytics_destination_zone_id", event.target.value || null)}
                >
                  <option value="">Select destination</option>
                  {zoneOptions.map((zone) => (
                    <option key={zone.id} value={zone.id}>
                      {zone.name}
                    </option>
                  ))}
                </select>
              </label>
            </>
          ) : null}

          {report === "sla" ? (
            <>
              <label>
                <span>Table</span>
                <select
                  aria-label="Table"
                  value={tableAreaId ?? ""}
                  onChange={(event) => setSearchParam("analytics_table_area_id", event.target.value || null)}
                >
                  <option value="">Select SLA table</option>
                  {tableOptions.map((table) => (
                    <option key={table.id} value={table.id}>
                      {table.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>Bucket size</span>
                <select
                  aria-label="Bucket size"
                  value={bucketMinutes}
                  onChange={(event) => setSearchParam("analytics_bucket_minutes", event.target.value)}
                >
                  <option value="60">Hourly</option>
                  <option value="15">15 minutes</option>
                </select>
              </label>
            </>
          ) : null}

          <p className="muted-text analytics-controls__hint">
            Interactive Analytics stays bounded to report windows and delivered read-only views. Exports and rollups remain later work.
          </p>
        </aside>

        <section className="analytics-results">
          {missingPrompt ? (
            <section className="panel panel--compact">
              <p className="eyebrow">Analytics Workspace</p>
              <h2>Choose report parameters</h2>
              <p className="muted-text">{missingPrompt}</p>
            </section>
          ) : loading ? (
            <section className="panel panel--compact">
              <p className="eyebrow">Analytics Workspace</p>
              <h2>Loading report</h2>
              <p className="muted-text">Resolving historical report data for the selected floor and time range.</p>
            </section>
          ) : error ? (
            <section className="panel panel--compact">
              <p className="eyebrow">Analytics Workspace</p>
              <h2>Report unavailable</h2>
              <p className="muted-text">{error}</p>
            </section>
          ) : report === "trajectory" ? (
            <TrajectoryReportPanel
              floorDetail={floorDetail}
              floorImageUrl={floorImageUrl}
              report={reportData && "points" in reportData ? (reportData as AnalyticsTrajectoryRecord) : null}
            />
          ) : report === "heatmap" ? (
            <HeatmapReportPanel
              floorDetail={floorDetail}
              floorImageUrl={floorImageUrl}
              report={reportData && "cells" in reportData ? (reportData as AnalyticsHeatmapRecord) : null}
            />
          ) : report === "dwell" ? (
            <DwellReportPanel report={reportData && "summary" in reportData && "records" in reportData && "zone_name" in reportData ? (reportData as AnalyticsDwellReportRecord) : null} />
          ) : report === "round_trip" ? (
            <RoundTripReportPanel
              report={
                reportData &&
                "summary" in reportData &&
                "records" in reportData &&
                "origin_zone_name" in reportData
                  ? (reportData as AnalyticsRoundTripReportRecord)
                  : null
              }
            />
          ) : (
            <SlaTrendReportPanel
              report={
                reportData &&
                "buckets" in reportData &&
                "table_name" in reportData
                  ? (reportData as AnalyticsSlaTrendRecord)
                  : null
              }
            />
          )}
        </section>
      </div>
    </div>
  );
}

function TrajectoryReportPanel({
  floorDetail,
  floorImageUrl,
  report
}: {
  floorDetail: FloorDetail | null;
  floorImageUrl: string | null;
  report: AnalyticsTrajectoryRecord | null;
}) {
  const width = floorDetail?.floor_plan?.width_px ?? DEFAULT_MAP_WIDTH;
  const height = floorDetail?.floor_plan?.height_px ?? DEFAULT_MAP_HEIGHT;

  if (!report || report.points.length === 0) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Trajectory Replay</p>
        <h2>No retained path</h2>
        <p className="muted-text">No retained trajectory points match the selected asset and report window.</p>
      </section>
    );
  }

  return (
    <div className="analytics-report-stack">
      <section className="panel">
        <div className="stack-card__header">
          <div>
            <p className="eyebrow">Trajectory Replay</p>
            <h2>{report.display_name}</h2>
          </div>
          <span className="status-badge status-badge--live">{report.points.length} points</span>
        </div>
        <AnalyticsMapSurface floorDetail={floorDetail} floorImageUrl={floorImageUrl}>
          <TrajectoryOverlay areas={floorDetail?.areas ?? []} height={height} points={report.points} width={width} />
        </AnalyticsMapSurface>
      </section>
      <section className="panel analytics-table-panel">
        <div className="stack-card__header">
          <div>
            <p className="eyebrow">Path Detail</p>
            <h2>Historical points</h2>
          </div>
        </div>
        <table className="analytics-table">
          <thead>
            <tr>
              <th>Observed</th>
              <th>Zone</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {report.points.map((point) => (
              <tr key={point.id}>
                <td>{point.observed_at}</td>
                <td>{point.zone_name ?? point.floor_name}</td>
                <td>{point.confidence_level}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function HeatmapReportPanel({
  floorDetail,
  floorImageUrl,
  report
}: {
  floorDetail: FloorDetail | null;
  floorImageUrl: string | null;
  report: AnalyticsHeatmapRecord | null;
}) {
  const width = floorDetail?.floor_plan?.width_px ?? DEFAULT_MAP_WIDTH;
  const height = floorDetail?.floor_plan?.height_px ?? DEFAULT_MAP_HEIGHT;

  if (!report || report.cells.length === 0) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Heatmap</p>
        <h2>No retained density</h2>
        <p className="muted-text">No retained heatmap samples match the selected floor, time range, and cohort.</p>
      </section>
    );
  }

  return (
    <div className="analytics-report-stack">
      <section className="panel">
        <div className="stack-card__header">
          <div>
            <p className="eyebrow">Heatmap</p>
            <h2>Traffic density</h2>
          </div>
          <span className="status-badge status-badge--warning">{report.total_samples} samples</span>
        </div>
        <AnalyticsMapSurface floorDetail={floorDetail} floorImageUrl={floorImageUrl}>
          <HeatmapOverlay height={height} report={report} width={width} />
        </AnalyticsMapSurface>
      </section>
      <section className="panel panel--compact analytics-summary-strip">
        <article className="analytics-summary-card">
          <span>Total samples</span>
          <strong>{report.total_samples}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Max density</span>
          <strong>{report.max_density}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Cohort</span>
          <strong>{report.asset_category ?? "All categories"}</strong>
        </article>
      </section>
    </div>
  );
}

function DwellReportPanel({ report }: { report: AnalyticsDwellReportRecord | null }) {
  if (!report || report.records.length === 0) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Dwell Report</p>
        <h2>No retained visits</h2>
        <p className="muted-text">No dwell records match the selected report scope.</p>
      </section>
    );
  }

  return (
    <div className="analytics-report-stack">
      <section className="panel panel--compact analytics-summary-strip">
        <article className="analytics-summary-card">
          <span>Visits</span>
          <strong>{report.summary.sample_count}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Average dwell</span>
          <strong>{formatDuration(report.summary.avg_duration_seconds)}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Threshold breaches</span>
          <strong>{report.summary.threshold_breach_count}</strong>
        </article>
      </section>
      <section className="panel analytics-table-panel">
        <div className="stack-card__header">
          <div>
            <p className="eyebrow">Dwell Detail</p>
            <h2>{report.zone_name ?? "All selected zones"}</h2>
          </div>
        </div>
        <table className="analytics-table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Zone</th>
              <th>Duration</th>
              <th>Breach</th>
            </tr>
          </thead>
          <tbody>
            {report.records.map((record) => (
              <tr key={record.id}>
                <td>{record.display_name}</td>
                <td>{record.zone_name}</td>
                <td>{formatDuration(record.duration_seconds)}</td>
                <td>{record.threshold_breached ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function RoundTripReportPanel({ report }: { report: AnalyticsRoundTripReportRecord | null }) {
  if (!report || report.records.length === 0) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Round-Trip Report</p>
        <h2>No completed cycles</h2>
        <p className="muted-text">No completed round-trip records match the selected origin, destination, and time scope.</p>
      </section>
    );
  }

  return (
    <div className="analytics-report-stack">
      <section className="panel panel--compact analytics-summary-strip">
        <article className="analytics-summary-card">
          <span>Completed trips</span>
          <strong>{report.summary.sample_count}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Average total</span>
          <strong>{formatDuration(report.summary.avg_duration_seconds)}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Average outbound</span>
          <strong>{formatDuration(report.summary.avg_outbound_seconds)}</strong>
        </article>
      </section>
      <section className="panel analytics-table-panel">
        <div className="stack-card__header">
          <div>
            <p className="eyebrow">Round-Trip Detail</p>
            <h2>
              {report.origin_zone_name} → {report.destination_zone_name} → {report.origin_zone_name}
            </h2>
          </div>
        </div>
        <table className="analytics-table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Outbound</th>
              <th>Return</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {report.records.map((record) => (
              <tr key={`${record.asset_tag_id}-${record.completed_at}`}>
                <td>{record.display_name}</td>
                <td>{formatDuration(record.outbound_seconds)}</td>
                <td>{formatDuration(record.return_seconds)}</td>
                <td>{formatDuration(record.total_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function SlaTrendReportPanel({ report }: { report: AnalyticsSlaTrendRecord | null }) {
  if (!report) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">SLA Trends</p>
        <h2>No SLA scope selected</h2>
      </section>
    );
  }

  return (
    <div className="analytics-report-stack">
      {report.threshold_source === "unavailable" ? (
        <p className="feedback-banner feedback-banner--neutral">
          No matching table SLA rule baseline is configured for this table yet. Trend timing is shown without breach highlighting.
        </p>
      ) : null}
      <section className="panel panel--compact analytics-summary-strip">
        <article className="analytics-summary-card">
          <span>Threshold</span>
          <strong>{report.threshold_seconds ? formatDuration(report.threshold_seconds) : "n/a"}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Current timer</span>
          <strong>{report.current_timer?.status ?? "n/a"}</strong>
        </article>
        <article className="analytics-summary-card">
          <span>Last visit</span>
          <strong>{formatDuration(report.current_timer?.last_visit_duration_seconds ?? null)}</strong>
        </article>
      </section>
      <section className="panel analytics-table-panel">
        <div className="stack-card__header">
          <div>
            <p className="eyebrow">SLA Trend</p>
            <h2>{report.table_name}</h2>
          </div>
        </div>
        <table className="analytics-table">
          <thead>
            <tr>
              <th>Bucket</th>
              <th>Completed visits</th>
              <th>Breaches</th>
              <th>Average duration</th>
            </tr>
          </thead>
          <tbody>
            {report.buckets.map((bucket) => (
              <tr key={bucket.bucket_started_at}>
                <td>{bucket.bucket_started_at}</td>
                <td>{bucket.completed_visit_count}</td>
                <td>{bucket.breach_count}</td>
                <td>{formatDuration(bucket.avg_duration_seconds)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
}

function AnalyticsMapSurface({
  children,
  floorDetail,
  floorImageUrl
}: {
  children: ReactNode;
  floorDetail: FloorDetail | null;
  floorImageUrl: string | null;
}) {
  const width = floorDetail?.floor_plan?.width_px ?? DEFAULT_MAP_WIDTH;
  const height = floorDetail?.floor_plan?.height_px ?? DEFAULT_MAP_HEIGHT;

  return (
    <div className="analytics-map-surface">
      <svg viewBox={`0 0 ${width} ${height}`} aria-label="Analytics map">
        <rect className="map-surface__background" height={height} rx={20} ry={20} width={width} x={0} y={0} />
        {floorImageUrl ? <image height={height} href={floorImageUrl} preserveAspectRatio="none" width={width} x={0} y={0} /> : null}
        {children}
      </svg>
    </div>
  );
}

function TrajectoryOverlay({
  areas,
  height,
  points,
  width
}: {
  areas: SpatialAreaRecord[];
  height: number;
  points: AnalyticsTrajectoryRecord["points"];
  width: number;
}) {
  const areaMap = new Map(areas.map((area) => [area.id, area] as const));
  const coordinates = points
    .map((point) => resolveHistoryCoordinate(point.point, point.zone_id, areaMap, width, height))
    .filter(Boolean) as Array<{ x: number; y: number }>;

  if (coordinates.length === 0) {
    return null;
  }

  return (
    <>
      <polyline
        className="analytics-trajectory"
        points={coordinates.map((point) => `${point.x},${point.y}`).join(" ")}
      />
      {coordinates.map((point, index) => (
        <circle key={`${point.x}-${point.y}-${index}`} className="analytics-trajectory__node" cx={point.x} cy={point.y} r={8} />
      ))}
    </>
  );
}

function HeatmapOverlay({
  height,
  report,
  width
}: {
  height: number;
  report: AnalyticsHeatmapRecord;
  width: number;
}) {
  return (
    <>
      {report.cells.map((cell) => (
        <rect
          key={`${cell.row}-${cell.column}`}
          className="analytics-heatmap-cell"
          x={(cell.column / report.grid_columns) * width}
          y={(cell.row / report.grid_rows) * height}
          width={width / report.grid_columns}
          height={height / report.grid_rows}
          style={{ opacity: Math.max(0.15, cell.intensity) }}
        />
      ))}
    </>
  );
}

function useAuthorizedFloorPlan(
  floorPlan: FloorPlanAsset | null,
  fetchWithAuth: (input: RequestInfo | URL, init?: RequestInit) => Promise<Response>
) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let nextObjectUrl: string | null = null;

    async function loadImage() {
      if (!floorPlan?.file_download_path) {
        setObjectUrl(null);
        return;
      }
      const response = await fetchWithAuth(floorPlan.file_download_path);
      if (!response.ok) {
        throw new Error("Unable to load floor plan asset");
      }
      const blob = await response.blob();
      nextObjectUrl = URL.createObjectURL(blob);
      if (active) {
        setObjectUrl(nextObjectUrl);
      }
    }

    void loadImage().catch(() => {
      if (active) {
        setObjectUrl(null);
      }
    });

    return () => {
      active = false;
      if (nextObjectUrl) {
        URL.revokeObjectURL(nextObjectUrl);
      }
    };
  }, [fetchWithAuth, floorPlan?.file_download_path]);

  return objectUrl;
}

function resolveHistoryCoordinate(
  point: { x: number; y: number } | null,
  zoneId: string | null,
  areasById: Map<string, SpatialAreaRecord>,
  width: number,
  height: number
) {
  if (point) {
    return { x: point.x * width, y: point.y * height };
  }
  if (!zoneId) {
    return null;
  }
  const area = areasById.get(zoneId);
  if (!area || area.points.length === 0) {
    return null;
  }
  const totals = area.points.reduce(
    (accumulator, next) => ({ x: accumulator.x + next.x, y: accumulator.y + next.y }),
    { x: 0, y: 0 }
  );
  return {
    x: (totals.x / area.points.length) * width,
    y: (totals.y / area.points.length) * height
  };
}

function toInputDateTime(value: string | null) {
  if (!value) {
    return "";
  }
  return new Date(value).toISOString().slice(0, 16);
}

function toIsoString(value: string) {
  return value ? new Date(value).toISOString() : null;
}

function formatDuration(value: number | null | undefined) {
  if (value == null) {
    return "n/a";
  }
  if (value < 60) {
    return `${Math.round(value)}s`;
  }
  return `${(value / 60).toFixed(1)}m`;
}

function uniqueValues(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function getMissingPrompt({
  report,
  assetTagId,
  originZoneId,
  destinationZoneId,
  tableAreaId
}: {
  report: AnalyticsReportKind;
  assetTagId: string | null;
  originZoneId: string | null;
  destinationZoneId: string | null;
  tableAreaId: string | null;
}) {
  if (report === "trajectory" && !assetTagId) {
    return "Select one tracked asset to replay its retained trajectory.";
  }
  if (report === "round_trip" && (!originZoneId || !destinationZoneId)) {
    return "Select an origin zone and a destination zone to evaluate completed round trips.";
  }
  if (report === "sla" && !tableAreaId) {
    return "Select one SLA-eligible table to inspect trend buckets and current timer state.";
  }
  return null;
}
