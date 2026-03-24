import type {
  AdminSummary,
  FloorDetail,
  FloorSummary,
  SiteRecord,
  SpatialAreaRecord,
  SpatialAreaType,
  SpatialPoint
} from "@rtls/contracts";
import {
  useCallback,
  useEffect,
  useState,
  type ChangeEvent,
  type FormEvent,
  type MouseEvent
} from "react";

import { useAuth } from "../auth";

type ScaleTarget = "point_a" | "point_b" | null;
type EditorMode = ScaleTarget | "polygon";

type FeedbackTone = "neutral" | "success" | "error";

type FeedbackState = {
  tone: FeedbackTone;
  message: string;
} | null;

type ScaleFormState = {
  pointA: SpatialPoint | null;
  pointB: SpatialPoint | null;
  realWorldDistanceM: string;
};

type AreaDraftState = {
  id: string | null;
  name: string;
  areaType: SpatialAreaType;
  points: SpatialPoint[];
  slaEligible: boolean;
  alertParticipation: boolean;
};

const DEFAULT_AREA_DRAFT: AreaDraftState = {
  id: null,
  name: "",
  areaType: "zone",
  points: [],
  slaEligible: false,
  alertParticipation: true
};

const AREA_TYPE_LABELS: Record<SpatialAreaType, string> = {
  zone: "Zone",
  table: "Table",
  restricted_zone: "Restricted Zone",
  poi: "Point of Interest"
};

function formatPointLabel(point: SpatialPoint | null) {
  if (!point) {
    return "Not set";
  }

  return `${(point.x * 100).toFixed(1)}%, ${(point.y * 100).toFixed(1)}%`;
}

function parseErrorMessage(payload: unknown) {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail?: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
  }

  return "Request failed";
}

function pointsToSvg(points: SpatialPoint[]) {
  return points.map((point) => `${point.x * 100},${point.y * 100}`).join(" ");
}

function normalizePoint(point: SpatialPoint) {
  return {
    x: Number(point.x.toFixed(4)),
    y: Number(point.y.toFixed(4))
  };
}

function cloneAreaDraft(area: SpatialAreaRecord): AreaDraftState {
  return {
    id: area.id,
    name: area.name,
    areaType: area.area_type,
    points: area.points.map((point) => ({ ...point })),
    slaEligible: area.sla_eligible,
    alertParticipation: area.alert_participation
  };
}

export function AdminSpatialWorkspace() {
  const { fetchWithAuth, user } = useAuth();
  const [managedRoles, setManagedRoles] = useState<string[]>([]);
  const [sites, setSites] = useState<SiteRecord[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null);
  const [selectedFloorId, setSelectedFloorId] = useState<string | null>(null);
  const [floorDetail, setFloorDetail] = useState<FloorDetail | null>(null);
  const [floorPlanUrl, setFloorPlanUrl] = useState<string | null>(null);
  const [siteName, setSiteName] = useState("");
  const [siteTimezone, setSiteTimezone] = useState("America/Bahia");
  const [floorName, setFloorName] = useState("");
  const [floorLevelLabel, setFloorLevelLabel] = useState("");
  const [floorPlanFile, setFloorPlanFile] = useState<File | null>(null);
  const [scaleForm, setScaleForm] = useState<ScaleFormState>({
    pointA: null,
    pointB: null,
    realWorldDistanceM: "10"
  });
  const [areaDraft, setAreaDraft] = useState<AreaDraftState>(DEFAULT_AREA_DRAFT);
  const [selectedAreaId, setSelectedAreaId] = useState<string | null>(null);
  const [editorMode, setEditorMode] = useState<EditorMode>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [isFloorLoading, setIsFloorLoading] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>(null);

  const selectedSite =
    sites.find((site) => site.id === selectedSiteId) ?? (sites.length > 0 ? sites[0] : null);
  const selectedFloor =
    selectedSite?.floors.find((floor) => floor.id === selectedFloorId) ??
    (selectedSite?.floors[0] ?? null);

  const requestJson = useCallback(async <T,>(path: string, init?: RequestInit): Promise<T> => {
    const response = await fetchWithAuth(path, init);
    if (!response.ok) {
      let message = `Request failed with ${response.status}`;
      try {
        message = parseErrorMessage(await response.json());
      } catch {
        message = response.statusText || message;
      }
      throw new Error(message);
    }

    return (await response.json()) as T;
  }, [fetchWithAuth]);

  const loadSites = useCallback(async (preferredSiteId?: string | null, preferredFloorId?: string | null) => {
    const siteRecords = await requestJson<SiteRecord[]>("/api/admin/sites");
    setSites(siteRecords);

    const nextSite =
      siteRecords.find((site) => site.id === preferredSiteId) ??
      siteRecords.find((site) => site.id === selectedSiteId) ??
      siteRecords[0] ??
      null;
    const nextFloor =
      nextSite?.floors.find((floor) => floor.id === preferredFloorId) ??
      nextSite?.floors.find((floor) => floor.id === selectedFloorId) ??
      nextSite?.floors[0] ??
      null;

    setSelectedSiteId(nextSite?.id ?? null);
    setSelectedFloorId(nextFloor?.id ?? null);
  }, [requestJson, selectedFloorId, selectedSiteId]);

  const loadFloorDetail = useCallback(async (floorId: string) => {
    setIsFloorLoading(true);
    try {
      const detail = await requestJson<FloorDetail>(`/api/admin/floors/${floorId}`);
      setFloorDetail(detail);
      setSelectedFloorId(detail.id);
      setSelectedAreaId((current) =>
        detail.areas.some((area) => area.id === current) ? current : null
      );
    } finally {
      setIsFloorLoading(false);
    }
  }, [requestJson]);

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      setIsBusy(true);
      try {
        const summary = await requestJson<AdminSummary>("/api/admin/summary");
        const siteRecords = await requestJson<SiteRecord[]>("/api/admin/sites");
        if (!active) {
          return;
        }

        setManagedRoles(summary.managed_roles);
        setSites(siteRecords);
        setSelectedSiteId(siteRecords[0]?.id ?? null);
        setSelectedFloorId(siteRecords[0]?.floors[0]?.id ?? null);
      } catch (error) {
        if (active) {
          setFeedback({
            tone: "error",
            message: (error as Error).message || "Unable to load the Admin Console."
          });
        }
      } finally {
        if (active) {
          setIsBusy(false);
        }
      }
    }

    void bootstrap();

    return () => {
      active = false;
    };
  }, [requestJson]);

  useEffect(() => {
    if (!selectedSite) {
      setSelectedFloorId(null);
      setFloorDetail(null);
      return;
    }

    if (!selectedFloor || selectedFloor.site_id !== selectedSite.id) {
      setSelectedFloorId(selectedSite.floors[0]?.id ?? null);
    }
  }, [selectedFloor, selectedSite]);

  useEffect(() => {
    if (!selectedFloorId) {
      setFloorDetail(null);
      return;
    }

    void loadFloorDetail(selectedFloorId).catch((error: Error) => {
      setFeedback({
        tone: "error",
        message: error.message || "Unable to load the selected floor."
      });
    });
  }, [loadFloorDetail, selectedFloorId]);

  useEffect(() => {
    if (!floorDetail) {
      setScaleForm({
        pointA: null,
        pointB: null,
        realWorldDistanceM: "10"
      });
      setAreaDraft(DEFAULT_AREA_DRAFT);
      return;
    }

    setScaleForm({
      pointA: floorDetail.scale?.point_a ?? null,
      pointB: floorDetail.scale?.point_b ?? null,
      realWorldDistanceM: floorDetail.scale
        ? String(floorDetail.scale.real_world_distance_m)
        : "10"
    });

    setAreaDraft((current) =>
      current.id && floorDetail.areas.some((area) => area.id === current.id)
        ? current
        : DEFAULT_AREA_DRAFT
    );
  }, [floorDetail]);

  useEffect(() => {
    let objectUrl: string | null = null;
    let active = true;

    async function loadFloorPlanImage() {
      if (!floorDetail?.floor_plan) {
        setFloorPlanUrl(null);
        return;
      }

      try {
        const response = await fetchWithAuth(floorDetail.floor_plan.file_download_path);
        if (!response.ok) {
          throw new Error("Unable to load the floor-plan image");
        }

        const blob = await response.blob();
        objectUrl = URL.createObjectURL(blob);
        if (active) {
          setFloorPlanUrl(objectUrl);
        }
      } catch (error) {
        if (active) {
          setFloorPlanUrl(null);
          setFeedback({
            tone: "error",
            message: (error as Error).message || "Unable to load the floor-plan image."
          });
        }
      }
    }

    void loadFloorPlanImage();

    return () => {
      active = false;
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [fetchWithAuth, floorDetail]);

  async function handleCreateSite(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsBusy(true);
    setFeedback(null);

    try {
      const site = await requestJson<SiteRecord>("/api/admin/sites", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: siteName.trim(),
          timezone_name: siteTimezone.trim() || null
        })
      });
      setSiteName("");
      await loadSites(site.id, null);
      setFeedback({ tone: "success", message: `Site ${site.name} created.` });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateFloor(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedSite) {
      return;
    }

    setIsBusy(true);
    setFeedback(null);
    try {
      const floor = await requestJson<FloorSummary>(`/api/admin/sites/${selectedSite.id}/floors`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: floorName.trim(),
          level_label: floorLevelLabel.trim() || null
        })
      });
      setFloorName("");
      setFloorLevelLabel("");
      await loadSites(selectedSite.id, floor.id);
      setFeedback({ tone: "success", message: `Floor ${floor.name} created.` });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUploadFloorPlan(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFloorId || !floorPlanFile) {
      setFeedback({ tone: "error", message: "Choose a PNG or JPG floor plan first." });
      return;
    }

    const formData = new FormData();
    formData.append("floor_plan", floorPlanFile);

    setIsBusy(true);
    setFeedback(null);
    try {
      const response = await fetchWithAuth(`/api/admin/floors/${selectedFloorId}/floor-plan`, {
        method: "POST",
        body: formData
      });
      if (!response.ok) {
        throw new Error(parseErrorMessage(await response.json()));
      }

      await loadFloorDetail(selectedFloorId);
      setFloorPlanFile(null);
      setFeedback({ tone: "success", message: "Floor plan uploaded." });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSaveScale() {
    if (!selectedFloorId || !scaleForm.pointA || !scaleForm.pointB) {
      setFeedback({
        tone: "error",
        message: "Set both reference points before confirming scale."
      });
      return;
    }

    setIsBusy(true);
    setFeedback(null);
    try {
      await requestJson<FloorDetail>(`/api/admin/floors/${selectedFloorId}/scale`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          point_a: scaleForm.pointA,
          point_b: scaleForm.pointB,
          real_world_distance_m: Number(scaleForm.realWorldDistanceM)
        })
      });
      await loadFloorDetail(selectedFloorId);
      setEditorMode(null);
      setFeedback({ tone: "success", message: "Scale configuration saved." });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  function resetAreaDraft() {
    setAreaDraft(DEFAULT_AREA_DRAFT);
    setSelectedAreaId(null);
    setEditorMode(null);
  }

  async function handleSaveArea() {
    if (!selectedFloorId) {
      return;
    }
    if (areaDraft.points.length < 3) {
      setFeedback({
        tone: "error",
        message: "Add at least three polygon points before saving an area."
      });
      return;
    }

    const payload = {
      name: areaDraft.name.trim(),
      area_type: areaDraft.areaType,
      points: areaDraft.points,
      sla_eligible: areaDraft.slaEligible,
      alert_participation: areaDraft.alertParticipation
    };

    setIsBusy(true);
    setFeedback(null);
    try {
      if (areaDraft.id) {
        await requestJson<SpatialAreaRecord>(`/api/admin/areas/${areaDraft.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        await requestJson<SpatialAreaRecord>(`/api/admin/floors/${selectedFloorId}/areas`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      await loadFloorDetail(selectedFloorId);
      resetAreaDraft();
      setFeedback({
        tone: "success",
        message: areaDraft.id ? "Operational area updated." : "Operational area created."
      });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteArea() {
    if (!areaDraft.id) {
      return;
    }

    setIsBusy(true);
    setFeedback(null);
    try {
      const response = await fetchWithAuth(`/api/admin/areas/${areaDraft.id}`, {
        method: "DELETE"
      });
      if (!response.ok) {
        throw new Error(parseErrorMessage(await response.json()));
      }

      if (selectedFloorId) {
        await loadFloorDetail(selectedFloorId);
      }
      resetAreaDraft();
      setFeedback({ tone: "success", message: "Operational area deleted." });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  function handleCanvasClick(event: MouseEvent<HTMLDivElement>) {
    if (!editorMode || !floorDetail?.floor_plan) {
      return;
    }

    const bounds = event.currentTarget.getBoundingClientRect();
    if (bounds.width <= 0 || bounds.height <= 0) {
      return;
    }

    const point = normalizePoint({
      x: (event.clientX - bounds.left) / bounds.width,
      y: (event.clientY - bounds.top) / bounds.height
    });

    if (editorMode === "point_a") {
      setScaleForm((current) => ({ ...current, pointA: point }));
      setEditorMode(null);
      return;
    }
    if (editorMode === "point_b") {
      setScaleForm((current) => ({ ...current, pointB: point }));
      setEditorMode(null);
      return;
    }

    setAreaDraft((current) => ({
      ...current,
      points: [...current.points, point]
    }));
  }

  function beginNewArea(areaType: SpatialAreaType) {
    setAreaDraft({
      ...DEFAULT_AREA_DRAFT,
      areaType
    });
    setSelectedAreaId(null);
    setEditorMode("polygon");
  }

  function selectExistingArea(area: SpatialAreaRecord) {
    setSelectedAreaId(area.id);
    setAreaDraft(cloneAreaDraft(area));
    setEditorMode(null);
  }

  function updateDraftPoint(index: number, axis: keyof SpatialPoint, value: string) {
    const nextValue = Number(value);
    if (Number.isNaN(nextValue)) {
      return;
    }

    setAreaDraft((current) => ({
      ...current,
      points: current.points.map((point, pointIndex) =>
        pointIndex === index
          ? normalizePoint({
              ...point,
              [axis]: Math.min(1, Math.max(0, nextValue))
            })
          : point
      )
    }));
  }

  function removeDraftPoint(index: number) {
    setAreaDraft((current) => ({
      ...current,
      points: current.points.filter((_, pointIndex) => pointIndex !== index)
    }));
  }

  function updateScalePoint(target: "pointA" | "pointB", axis: keyof SpatialPoint, value: string) {
    const nextValue = Number(value);
    if (Number.isNaN(nextValue)) {
      return;
    }

    setScaleForm((current) => ({
      ...current,
      [target]: normalizePoint({
        ...(current[target] ?? { x: 0, y: 0 }),
        [axis]: Math.min(1, Math.max(0, nextValue))
      })
    }));
  }

  function renderAreaLayer(area: SpatialAreaRecord) {
    const isSelected = area.id === selectedAreaId;
    return (
      <g key={area.id}>
        <polygon
          className={`map-area map-area--${area.area_type}${isSelected ? " map-area--selected" : ""}`}
          points={pointsToSvg(area.points)}
        />
        <text className="map-area__label" x={area.points[0]?.x ? area.points[0].x * 100 : 0} y={(area.points[0]?.y ?? 0) * 100 - 1.2}>
          {area.name}
        </text>
      </g>
    );
  }

  return (
    <section className="admin-spatial-shell">
      <div className="admin-spatial-header">
        <div>
          <p className="eyebrow">Industrial Command Deck</p>
          <h1>Admin Spatial Workspace</h1>
          <p className="panel-copy">
            Build the canonical site hierarchy, upload the floor plan, confirm physical scale, and
            define the operational zones that later live-map, alerting, and analytics features will
            reuse.
          </p>
        </div>
        <div className="status-strip">
          <span>{user?.email}</span>
          <span>{managedRoles.join(" / ") || "Administrator"}</span>
          <span>{floorDetail?.floor_plan ? "Floor plan ready" : "Awaiting floor plan"}</span>
        </div>
      </div>

      {feedback ? (
        <div className={`feedback-banner feedback-banner--${feedback.tone}`}>{feedback.message}</div>
      ) : null}

      <div className="admin-spatial-grid">
        <aside className="admin-sidebar">
          <article className="panel panel--compact stack-card">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Step 01</p>
                <h2>Sites</h2>
              </div>
              <span className="metric-chip">{sites.length} configured</span>
            </div>

            <form className="admin-form" onSubmit={handleCreateSite}>
              <label>
                <span>Site Name</span>
                <input
                  placeholder="Salvador Flagship"
                  value={siteName}
                  onChange={(event) => setSiteName(event.target.value)}
                />
              </label>
              <label>
                <span>Timezone</span>
                <input
                  placeholder="America/Bahia"
                  value={siteTimezone}
                  onChange={(event) => setSiteTimezone(event.target.value)}
                />
              </label>
              <button className="primary-button" disabled={isBusy || !siteName.trim()} type="submit">
                Create Site
              </button>
            </form>

            <div className="selection-list">
              {sites.length === 0 ? (
                <p className="empty-copy">Create the first site to unlock floor planning.</p>
              ) : null}
              {sites.map((site) => (
                <button
                  key={site.id}
                  className={`selection-card${site.id === selectedSite?.id ? " selection-card--active" : ""}`}
                  onClick={() => {
                    setSelectedSiteId(site.id);
                    setSelectedFloorId(site.floors[0]?.id ?? null);
                  }}
                  type="button"
                >
                  <strong>{site.name}</strong>
                  <span>{site.timezone_name || "Timezone pending"}</span>
                </button>
              ))}
            </div>
          </article>

          <article className="panel panel--compact stack-card">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Step 02</p>
                <h2>Floors</h2>
              </div>
              <span className="metric-chip">{selectedSite?.floors.length ?? 0} floor(s)</span>
            </div>

            <form className="admin-form" onSubmit={handleCreateFloor}>
              <label>
                <span>Floor Name</span>
                <input
                  placeholder="Dining Room"
                  value={floorName}
                  onChange={(event) => setFloorName(event.target.value)}
                />
              </label>
              <label>
                <span>Level Label</span>
                <input
                  placeholder="L1"
                  value={floorLevelLabel}
                  onChange={(event) => setFloorLevelLabel(event.target.value)}
                />
              </label>
              <button
                className="secondary-button"
                disabled={isBusy || !selectedSite || !floorName.trim()}
                type="submit"
              >
                Add Floor
              </button>
            </form>

            <div className="selection-list">
              {selectedSite?.floors.length ? null : (
                <p className="empty-copy">No floors configured for the selected site yet.</p>
              )}
              {selectedSite?.floors.map((floor) => (
                <button
                  key={floor.id}
                  className={`selection-card${floor.id === selectedFloor?.id ? " selection-card--active" : ""}`}
                  onClick={() => setSelectedFloorId(floor.id)}
                  type="button"
                >
                  <strong>{floor.name}</strong>
                  <span>{floor.level_label || "Unlabeled level"}</span>
                  <small>
                    {floor.has_floor_plan ? "Plan ready" : "Plan missing"} ·{" "}
                    {floor.scale_configured ? "Scale ready" : "Scale pending"}
                  </small>
                </button>
              ))}
            </div>
          </article>
        </aside>

        <div className="admin-main-column">
          <article className="panel admin-floor-summary">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Step 03</p>
                <h2>{selectedFloor?.name || "Select a floor"}</h2>
              </div>
              <span className="metric-chip">
                {selectedFloor?.level_label || "Awaiting floor selection"}
              </span>
            </div>

            {selectedFloor ? (
              <div className="summary-strip">
                <div>
                  <span className="summary-label">Site</span>
                  <strong>{selectedSite?.name}</strong>
                </div>
                <div>
                  <span className="summary-label">Floor Plan</span>
                  <strong>{floorDetail?.floor_plan ? "Uploaded" : "Missing"}</strong>
                </div>
                <div>
                  <span className="summary-label">Scale</span>
                  <strong>{floorDetail?.scale ? "Confirmed" : "Pending"}</strong>
                </div>
                <div>
                  <span className="summary-label">Operational Areas</span>
                  <strong>{floorDetail?.areas.length ?? 0}</strong>
                </div>
              </div>
            ) : (
              <p className="empty-copy">
                Choose a site and floor from the left rail to start the spatial setup flow.
              </p>
            )}
          </article>

          <div className="admin-workspace-grid">
            <article className="panel stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Step 04</p>
                  <h2>Floor Plan & Scale</h2>
                </div>
                <span className="metric-chip">
                  {floorDetail?.floor_plan?.mime_type || "PNG / JPG only"}
                </span>
              </div>

              <form className="admin-form admin-form--inline" onSubmit={handleUploadFloorPlan}>
                <label className="file-input">
                  <span>Raster Floor Plan</span>
                  <input
                    accept=".png,.jpg,.jpeg,image/png,image/jpeg"
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      setFloorPlanFile(event.target.files?.[0] ?? null)
                    }
                    type="file"
                  />
                </label>
                <button
                  className="secondary-button"
                  disabled={isBusy || !selectedFloor || !floorPlanFile}
                  type="submit"
                >
                  Upload Floor Plan
                </button>
              </form>

              <div className="scale-controls">
                <div className="scale-targets">
                  <button
                    className={`tool-button${editorMode === "point_a" ? " tool-button--active" : ""}`}
                    disabled={!floorDetail?.floor_plan}
                    onClick={() => setEditorMode("point_a")}
                    type="button"
                  >
                    Set Point A
                  </button>
                  <button
                    className={`tool-button${editorMode === "point_b" ? " tool-button--active" : ""}`}
                    disabled={!floorDetail?.floor_plan}
                    onClick={() => setEditorMode("point_b")}
                    type="button"
                  >
                    Set Point B
                  </button>
                  <button className="tool-button" onClick={() => setEditorMode(null)} type="button">
                    Stop Targeting
                  </button>
                </div>

                <div className="coordinate-grid">
                  <label>
                    <span>Point A X</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.001"
                      value={scaleForm.pointA?.x ?? 0}
                      onChange={(event) => updateScalePoint("pointA", "x", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Point A Y</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.001"
                      value={scaleForm.pointA?.y ?? 0}
                      onChange={(event) => updateScalePoint("pointA", "y", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Point B X</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.001"
                      value={scaleForm.pointB?.x ?? 0}
                      onChange={(event) => updateScalePoint("pointB", "x", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Point B Y</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.001"
                      value={scaleForm.pointB?.y ?? 0}
                      onChange={(event) => updateScalePoint("pointB", "y", event.target.value)}
                    />
                  </label>
                  <label>
                    <span>Measured Distance (m)</span>
                    <input
                      type="number"
                      min="0.1"
                      step="0.1"
                      value={scaleForm.realWorldDistanceM}
                      onChange={(event) =>
                        setScaleForm((current) => ({
                          ...current,
                          realWorldDistanceM: event.target.value
                        }))
                      }
                    />
                  </label>
                </div>

                <div className="status-grid">
                  <div>
                    <span className="summary-label">Point A</span>
                    <strong>{formatPointLabel(scaleForm.pointA)}</strong>
                  </div>
                  <div>
                    <span className="summary-label">Point B</span>
                    <strong>{formatPointLabel(scaleForm.pointB)}</strong>
                  </div>
                  <div>
                    <span className="summary-label">Scale Factor</span>
                    <strong>
                      {floorDetail?.scale
                        ? `${floorDetail.scale.pixels_per_meter.toFixed(2)} px/m`
                        : "Awaiting confirmation"}
                    </strong>
                  </div>
                </div>

                <button
                  className="primary-button"
                  disabled={!floorDetail?.floor_plan || isBusy}
                  onClick={() => void handleSaveScale()}
                  type="button"
                >
                  Confirm Scale
                </button>
              </div>
            </article>

            <article className="panel stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Step 05</p>
                  <h2>Zone & POI Editor</h2>
                </div>
                <span className="metric-chip">
                  {isFloorLoading ? "Loading floor..." : `${floorDetail?.areas.length ?? 0} defined`}
                </span>
              </div>

              <div
                className={`map-canvas${editorMode ? " map-canvas--targeting" : ""}`}
                onClick={handleCanvasClick}
                role="presentation"
              >
                {floorPlanUrl ? (
                  <>
                    <img alt="Floor plan preview" className="map-canvas__image" src={floorPlanUrl} />
                    <svg className="map-canvas__overlay" viewBox="0 0 100 100" preserveAspectRatio="none">
                      {floorDetail?.areas.map(renderAreaLayer)}

                      {areaDraft.points.length >= 1 ? (
                        <g>
                          {areaDraft.points.length >= 2 ? (
                            <polyline
                              className="map-draft map-draft--line"
                              points={pointsToSvg(areaDraft.points)}
                            />
                          ) : null}
                          {areaDraft.points.length >= 3 ? (
                            <polygon
                              className="map-draft map-draft--polygon"
                              points={pointsToSvg(areaDraft.points)}
                            />
                          ) : null}
                          {areaDraft.points.map((point, index) => (
                            <circle
                              key={`${point.x}-${point.y}-${index}`}
                              className="map-point map-point--draft"
                              cx={point.x * 100}
                              cy={point.y * 100}
                              r="0.9"
                            />
                          ))}
                        </g>
                      ) : null}

                      {scaleForm.pointA && scaleForm.pointB ? (
                        <line
                          className="map-scale"
                          x1={scaleForm.pointA.x * 100}
                          x2={scaleForm.pointB.x * 100}
                          y1={scaleForm.pointA.y * 100}
                          y2={scaleForm.pointB.y * 100}
                        />
                      ) : null}
                      {scaleForm.pointA ? (
                        <circle
                          className="map-point map-point--scale"
                          cx={scaleForm.pointA.x * 100}
                          cy={scaleForm.pointA.y * 100}
                          r="1"
                        />
                      ) : null}
                      {scaleForm.pointB ? (
                        <circle
                          className="map-point map-point--scale"
                          cx={scaleForm.pointB.x * 100}
                          cy={scaleForm.pointB.y * 100}
                          r="1"
                        />
                      ) : null}
                    </svg>
                  </>
                ) : (
                  <div className="map-placeholder">
                    <p className="eyebrow">Floor Plan Pending</p>
                    <h3>Upload a PNG or JPG to unlock calibration and polygon editing.</h3>
                    <p className="muted-text">
                      CAD and PDF parsing are intentionally deferred to a later implementation
                      change after this raster-first spatial model stabilizes.
                    </p>
                  </div>
                )}
              </div>

              <div className="canvas-guidance">
                <span>Click image to place scale targets or polygon vertices.</span>
                <span>{editorMode ? `Active tool: ${editorMode}` : "No active targeting tool"}</span>
              </div>
            </article>
          </div>

          <div className="admin-workspace-grid admin-workspace-grid--bottom">
            <article className="panel panel--compact stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Area Library</p>
                  <h2>Existing Operational Areas</h2>
                </div>
                <span className="metric-chip">{floorDetail?.areas.length ?? 0}</span>
              </div>

              <div className="toolbar-row">
                <button className="tool-button" onClick={() => beginNewArea("zone")} type="button">
                  New Zone
                </button>
                <button className="tool-button" onClick={() => beginNewArea("table")} type="button">
                  New Table
                </button>
                <button
                  className="tool-button"
                  onClick={() => beginNewArea("restricted_zone")}
                  type="button"
                >
                  New Restricted Zone
                </button>
                <button className="tool-button" onClick={() => beginNewArea("poi")} type="button">
                  New POI
                </button>
              </div>

              <div className="selection-list">
                {floorDetail?.areas.length ? null : (
                  <p className="empty-copy">
                    Define at least one zone, table, restricted zone, or POI for this floor.
                  </p>
                )}
                {floorDetail?.areas.map((area) => (
                  <button
                    key={area.id}
                    className={`selection-card${area.id === selectedAreaId ? " selection-card--active" : ""}`}
                    onClick={() => selectExistingArea(area)}
                    type="button"
                  >
                    <strong>{area.name}</strong>
                    <span>{AREA_TYPE_LABELS[area.area_type]}</span>
                    <small>
                      {area.sla_eligible ? "SLA eligible" : "SLA neutral"} ·{" "}
                      {area.alert_participation ? "Alert participant" : "Alert excluded"}
                    </small>
                  </button>
                ))}
              </div>
            </article>

            <article className="panel panel--compact stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Area Editor</p>
                  <h2>{areaDraft.id ? "Edit Area" : "Draft Area"}</h2>
                </div>
                <span className="metric-chip">
                  {AREA_TYPE_LABELS[areaDraft.areaType]} · {areaDraft.points.length} point(s)
                </span>
              </div>

              <div className="admin-form">
                <label>
                  <span>Area Name</span>
                  <input
                    placeholder="Kitchen Pass"
                    value={areaDraft.name}
                    onChange={(event) =>
                      setAreaDraft((current) => ({
                        ...current,
                        name: event.target.value
                      }))
                    }
                  />
                </label>

                <label>
                  <span>Area Type</span>
                  <select
                    value={areaDraft.areaType}
                    onChange={(event) =>
                      setAreaDraft((current) => ({
                        ...current,
                        areaType: event.target.value as SpatialAreaType
                      }))
                    }
                  >
                    {Object.entries(AREA_TYPE_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                </label>

                <div className="toggle-grid">
                  <label className="toggle-card">
                    <input
                      checked={areaDraft.slaEligible}
                      onChange={(event) =>
                        setAreaDraft((current) => ({
                          ...current,
                          slaEligible: event.target.checked
                        }))
                      }
                      type="checkbox"
                    />
                    <span>SLA Eligible</span>
                  </label>
                  <label className="toggle-card">
                    <input
                      checked={areaDraft.alertParticipation}
                      onChange={(event) =>
                        setAreaDraft((current) => ({
                          ...current,
                          alertParticipation: event.target.checked
                        }))
                      }
                      type="checkbox"
                    />
                    <span>Alert Participation</span>
                  </label>
                </div>

                <div className="toolbar-row">
                  <button
                    className={`tool-button${editorMode === "polygon" ? " tool-button--active" : ""}`}
                    disabled={!floorDetail?.floor_plan}
                    onClick={() => setEditorMode("polygon")}
                    type="button"
                  >
                    Add Polygon Points
                  </button>
                  <button
                    className="tool-button"
                    onClick={() =>
                      setAreaDraft((current) => ({
                        ...current,
                        points: []
                      }))
                    }
                    type="button"
                  >
                    Clear Points
                  </button>
                  <button className="tool-button" onClick={resetAreaDraft} type="button">
                    Reset Draft
                  </button>
                </div>

                <div className="point-editor-list">
                  {areaDraft.points.length === 0 ? (
                    <p className="empty-copy">
                      Click the floor plan to add polygon points, or edit them numerically here.
                    </p>
                  ) : null}
                  {areaDraft.points.map((point, index) => (
                    <div className="point-editor-row" key={`${point.x}-${point.y}-${index}`}>
                      <strong>P{index + 1}</strong>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.001"
                        value={point.x}
                        onChange={(event) => updateDraftPoint(index, "x", event.target.value)}
                      />
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.001"
                        value={point.y}
                        onChange={(event) => updateDraftPoint(index, "y", event.target.value)}
                      />
                      <button
                        className="icon-button"
                        onClick={() => removeDraftPoint(index)}
                        type="button"
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>

                <div className="toolbar-row">
                  <button
                    className="primary-button"
                    disabled={isBusy || !areaDraft.name.trim()}
                    onClick={() => void handleSaveArea()}
                    type="button"
                  >
                    {areaDraft.id ? "Update Area" : "Create Area"}
                  </button>
                  <button
                    className="secondary-button"
                    disabled={!areaDraft.id || isBusy}
                    onClick={() => void handleDeleteArea()}
                    type="button"
                  >
                    Delete Area
                  </button>
                </div>
              </div>
            </article>
          </div>
        </div>
      </div>

      {isBusy ? <p className="muted-text">Saving changes...</p> : null}
    </section>
  );
}
