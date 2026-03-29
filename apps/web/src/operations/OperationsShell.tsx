import type {
  AlertNotificationSummaryRecord,
  AssetLocationRecord,
  FloorDetail,
  FloorPlanAsset,
  FloorSummary,
  GatewayRecord,
  LiveLocationStreamEvent,
  LocationConfidenceLevel,
  OperationsFeedStatus,
  OperationsOverviewRecord,
  SiteRecord,
  SpatialAreaRecord
} from "@rtls/contracts";
import {
  startTransition,
  useCallback,
  useDeferredValue,
  useEffect,
  useMemo,
  useState
} from "react";
import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
  useOutletContext,
  useSearchParams
} from "react-router-dom";

import { useAuth } from "../auth";

type ShellContextValue = {
  accessToken: string | null;
  alertSummary: AlertNotificationSummaryRecord | null;
  apiBaseUrl: string;
  fetchWithAuth: ReturnType<typeof useAuth>["fetchWithAuth"];
  refreshAlertSummary: () => Promise<void>;
  selectedSite: SiteRecord | null;
  selectedFloor: FloorSummary | null;
  setSearchParam: (key: string, value: string | null) => void;
  setShellFeed: (status: OperationsFeedStatus, updatedAt: string | null) => void;
  shellSearchParams: URLSearchParams;
  sites: SiteRecord[];
  sitesLoading: boolean;
  sitesError: string | null;
  userRole: string | undefined;
};

const DEFAULT_MAP_WIDTH = 1200;
const DEFAULT_MAP_HEIGHT = 720;

export function OperationsShellLayout() {
  const { accessToken, fetchWithAuth, user } = useAuth();
  const apiBaseUrl = useAuth().apiBaseUrl;
  const [searchParams, setSearchParams] = useSearchParams();
  const [sites, setSites] = useState<SiteRecord[]>([]);
  const [sitesLoading, setSitesLoading] = useState(true);
  const [sitesError, setSitesError] = useState<string | null>(null);
  const [alertSummary, setAlertSummary] = useState<AlertNotificationSummaryRecord | null>(null);
  const [feedStatus, setFeedStatus] = useState<OperationsFeedStatus>("empty");
  const [feedUpdatedAt, setFeedUpdatedAt] = useState<string | null>(null);
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;

    async function loadSites() {
      setSitesLoading(true);
      try {
        const response = await fetchWithAuth("/api/admin/sites");
        if (!response.ok) {
          throw new Error("Unable to load site context");
        }
        const payload = (await response.json()) as SiteRecord[];
        if (!cancelled) {
          setSites(payload);
          setSitesError(null);
        }
      } catch {
        if (!cancelled) {
          setSites([]);
          setSitesError("Unable to load mapped sites.");
        }
      } finally {
        if (!cancelled) {
          setSitesLoading(false);
        }
      }
    }

    void loadSites();
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth]);

  const selectedSite = useMemo(() => {
    const siteId = searchParams.get("site_id");
    return sites.find((site) => site.id === siteId) ?? null;
  }, [searchParams, sites]);

  const selectedFloor = useMemo(() => {
    const floorId = searchParams.get("floor_id");
    const floorPool = selectedSite?.floors ?? sites.flatMap((site) => site.floors);
    return floorPool.find((floor) => floor.id === floorId) ?? null;
  }, [searchParams, selectedSite, sites]);

  const refreshAlertSummary = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (selectedSite?.id) {
        params.set("site_id", selectedSite.id);
      }
      if (selectedFloor?.id) {
        params.set("floor_id", selectedFloor.id);
      }
      const response = await fetchWithAuth(`/api/alerts/summary?${params.toString()}`);
      if (!response.ok) {
        throw new Error("Unable to load alert summary");
      }
      const payload = (await response.json()) as AlertNotificationSummaryRecord;
      setAlertSummary(payload);
    } catch {
      setAlertSummary(null);
    }
  }, [fetchWithAuth, selectedFloor?.id, selectedSite?.id]);

  useEffect(() => {
    void refreshAlertSummary();
  }, [refreshAlertSummary]);

  useEffect(() => {
    if (sitesLoading || sites.length === 0) {
      return;
    }

    const nextSite = selectedSite ?? sites[0];
    const nextFloor = nextSite.floors.find((floor) => floor.id === selectedFloor?.id) ?? nextSite.floors[0] ?? null;
    const nextParams = new URLSearchParams(searchParams);
    let changed = false;

    if (nextParams.get("site_id") !== nextSite.id) {
      nextParams.set("site_id", nextSite.id);
      changed = true;
    }
    if (nextFloor && nextParams.get("floor_id") !== nextFloor.id) {
      nextParams.set("floor_id", nextFloor.id);
      changed = true;
    }
    if (!nextFloor && nextParams.has("floor_id")) {
      nextParams.delete("floor_id");
      changed = true;
    }

    if (changed) {
      startTransition(() => {
        setSearchParams(nextParams, { replace: true });
      });
    }
  }, [searchParams, selectedFloor, selectedSite, setSearchParams, sites, sitesLoading]);

  const setSearchParam = (key: string, value: string | null) => {
    const nextParams = new URLSearchParams(searchParams);
    if (value) {
      nextParams.set(key, value);
    } else {
      nextParams.delete(key);
    }
    startTransition(() => {
      setSearchParams(nextParams, { replace: true });
    });
  };

  const shellContext: ShellContextValue = {
    accessToken,
    alertSummary,
    apiBaseUrl,
    fetchWithAuth,
    refreshAlertSummary,
    selectedSite,
    selectedFloor,
    setSearchParam,
    setShellFeed: (status, updatedAt) => {
      setFeedStatus(status);
      setFeedUpdatedAt(updatedAt);
    },
    shellSearchParams: searchParams,
    sites,
    sitesLoading,
    sitesError,
    userRole: user?.role
  };

  const navItems = [
    { label: "Overview", path: "/operations" },
    { label: "Live Map", path: "/operations/live-map" },
    {
      label: "Alerts",
      path: "/operations/alerts",
      badgeCount: alertSummary?.unresolved_count ?? 0
    }
  ];
  if (user?.role === "Administrator") {
    navItems.push({ label: "Admin", path: "/admin" });
  }

  return (
    <main className="app-shell">
      <aside className="shell-rail">
        <div className="shell-brand">
          <p className="eyebrow">RTLS Analytics Platform</p>
          <h1>Operations</h1>
          <p className="muted-text">
            Live service readiness, map-first monitoring, and spatial triage for restaurant operations.
          </p>
        </div>

        <nav className="shell-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              className={({ isActive }) =>
                isActive ? "shell-nav__link shell-nav__link--active" : "shell-nav__link"
              }
              end={item.path === "/operations"}
              to={{
                pathname: item.path,
                search: searchParams.toString() ? `?${searchParams.toString()}` : ""
              }}
            >
              <span>{item.label}</span>
              {"badgeCount" in item && item.badgeCount ? (
                <span className="shell-nav__badge">{item.badgeCount}</span>
              ) : null}
            </NavLink>
          ))}
        </nav>

        <div className="shell-status-card">
          <p className="shell-status-card__label">Context</p>
          <strong>{selectedSite?.name ?? "Awaiting mapped site"}</strong>
          <span>{selectedFloor?.name ?? "No floor selected"}</span>
        </div>
      </aside>

      <section className="shell-main">
        <header className="shell-topbar">
          <div className="shell-topbar__context">
            <label>
              <span>Site</span>
              <select
                aria-label="Site"
                disabled={sitesLoading || sites.length === 0}
                value={selectedSite?.id ?? ""}
                onChange={(event) => {
                  const nextSite = sites.find((site) => site.id === event.target.value) ?? null;
                  setSearchParam("site_id", nextSite?.id ?? null);
                  setSearchParam("floor_id", nextSite?.floors[0]?.id ?? null);
                }}
              >
                {sites.length === 0 ? <option value="">No mapped sites</option> : null}
                {sites.map((site) => (
                  <option key={site.id} value={site.id}>
                    {site.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Floor</span>
              <select
                aria-label="Floor"
                disabled={!selectedSite || selectedSite.floors.length === 0}
                value={selectedFloor?.id ?? ""}
                onChange={(event) => setSearchParam("floor_id", event.target.value || null)}
              >
                {!selectedSite?.floors.length ? <option value="">No mapped floors</option> : null}
                {selectedSite?.floors.map((floor) => (
                  <option key={floor.id} value={floor.id}>
                    {floor.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="shell-topbar__meta">
            <div className={`live-pill live-pill--${feedStatus}`}>
              <span className="live-pill__dot" />
              <div>
                <strong>{feedStatusLabel(feedStatus)}</strong>
                <span>{feedUpdatedAt ? `Updated ${relativeTime(feedUpdatedAt)}` : "Awaiting live feed"}</span>
              </div>
            </div>
            <div className="shell-user-chip">
              <strong>{user?.display_name ?? user?.email}</strong>
              <span>{user?.role}</span>
            </div>
          </div>
        </header>

        {sitesError ? <p className="feedback-banner feedback-banner--error">{sitesError}</p> : null}
        <div className={location.pathname === "/operations/live-map" ? "shell-page shell-page--map" : "shell-page"}>
          <Outlet context={shellContext} />
        </div>
      </section>
    </main>
  );
}

export function useOperationsShell() {
  return useOutletContext<ShellContextValue>();
}

export function OperationsOverviewPage() {
  const { fetchWithAuth, selectedFloor, selectedSite, setShellFeed, shellSearchParams } = useOperationsShell();
  const [summary, setSummary] = useState<OperationsOverviewRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const previewImageUrl = useAuthorizedFloorPlan(
    summary?.map_preview.floor_plan ?? null,
    fetchWithAuth
  );

  useEffect(() => {
    let cancelled = false;

    async function loadOverview() {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (selectedSite?.id) {
          params.set("site_id", selectedSite.id);
        }
        if (selectedFloor?.id) {
          params.set("floor_id", selectedFloor.id);
        }
        const response = await fetchWithAuth(`/api/operations/overview?${params.toString()}`);
        if (!response.ok) {
          throw new Error("Unable to load operations overview");
        }
        const payload = (await response.json()) as OperationsOverviewRecord;
        if (!cancelled) {
          setSummary(payload);
          setError(null);
          setShellFeed(payload.feed_status, payload.feed_updated_at);
        }
      } catch {
        if (!cancelled) {
          setSummary(null);
          setError("Unable to load operations overview.");
          setShellFeed("degraded", null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadOverview();
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth, selectedFloor?.id, selectedSite?.id, setShellFeed]);

  const openLiveMap = (assetTagId: string | null) => {
    const nextParams = new URLSearchParams(shellSearchParams);
    if (assetTagId) {
      nextParams.set("asset_tag_id", assetTagId);
    } else {
      nextParams.delete("asset_tag_id");
    }
    navigate(`/operations/live-map?${nextParams.toString()}`);
  };

  if (loading) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Operations Overview</p>
        <h2>Loading live snapshot</h2>
        <p className="muted-text">Pulling current location and health signals for the selected floor.</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="panel panel--compact">
        <p className="eyebrow">Operations Overview</p>
        <h2>Overview unavailable</h2>
        <p className="muted-text">{error}</p>
      </section>
    );
  }

  const preview = summary?.map_preview;
  const priorityItems = summary?.priority_items ?? [];
  const gatewaySnapshot = summary?.gateway_snapshot ?? [];

  return (
    <div className="overview-layout">
      <header className="page-header panel panel--compact">
        <div>
          <p className="eyebrow">Operations Overview</p>
          <h2>{summary?.floor_name ?? "Awaiting mapped floor"}</h2>
          <p className="muted-text">
            {summary?.site_name
              ? `${summary.site_name} · Live operational snapshot derived from current telemetry and gateway health`
              : "Create mapped sites and start telemetry ingestion to unlock the live monitoring shell."}
          </p>
        </div>
        <button className="primary-button" onClick={() => openLiveMap(null)} type="button">
          Open Live Map
        </button>
      </header>

      <section className="overview-kpis">
        <KpiCard label="Active Assets" value={summary?.kpis.active_assets ?? 0} tone="live" />
        <KpiCard label="Low Confidence" value={summary?.kpis.low_confidence_assets ?? 0} tone="warning" />
        <KpiCard
          label="Restricted Zone Hits"
          value={summary?.kpis.restricted_zone_assets ?? 0}
          tone="critical"
        />
        <KpiCard label="Stale Gateways" value={summary?.kpis.stale_gateways ?? 0} tone="warning" />
      </section>

      <div className="overview-grid">
        <section className="panel overview-map-panel">
          <div className="stack-card__header">
            <div>
              <p className="eyebrow">Live Map Preview</p>
              <h2>{preview?.floor_name ?? "No floor selected"}</h2>
            </div>
            <button className="secondary-button" onClick={() => openLiveMap(null)} type="button">
              Open Live Map
            </button>
          </div>
          <MapCanvas
            areas={preview?.areas ?? []}
            compact
            floorImageUrl={previewImageUrl}
            floorPlan={preview?.floor_plan ?? null}
            gateways={preview?.gateways ?? []}
            locations={preview?.locations ?? []}
            onSelectAsset={(assetTagId) => openLiveMap(assetTagId)}
            selectedAssetId={null}
            showGateways
            showZones
          />
        </section>

        <div className="overview-side-column">
          <section className="panel">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Priority Queue</p>
                <h2>Current operational focus</h2>
              </div>
            </div>
            {priorityItems.length === 0 ? (
              <p className="empty-copy">No active incidents on the selected floor.</p>
            ) : (
              <div className="priority-list">
                {priorityItems.map((item) => (
                  <article
                    key={item.id}
                    className={
                      item.severity === "critical"
                        ? "priority-card priority-card--critical"
                        : "priority-card priority-card--warning"
                    }
                  >
                    <div>
                      <strong>{item.title}</strong>
                      <p className="muted-text">{item.summary}</p>
                    </div>
                    <div className="priority-card__meta">
                      <span>{relativeTime(item.observed_at)}</span>
                      <button
                        className="secondary-button"
                        onClick={() => openLiveMap(item.asset_tag_id)}
                        type="button"
                      >
                        View on map
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="panel">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Infrastructure Snapshot</p>
                <h2>Gateway issues</h2>
              </div>
            </div>
            {gatewaySnapshot.length === 0 ? (
              <p className="empty-copy">No stale gateways reported for the selected floor.</p>
            ) : (
              <div className="health-list">
                {gatewaySnapshot.map((gateway) => (
                  <div key={gateway.gateway_id} className="health-row">
                    <div>
                      <strong>{gateway.display_name}</strong>
                      <p className="muted-text">
                        Last heartbeat {relativeTime(gateway.last_seen_at)} · Firmware {gateway.firmware_version ?? "n/a"}
                      </p>
                    </div>
                    <span className="status-badge status-badge--warning">{gateway.status}</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

export function LiveMapPage() {
  const {
    accessToken,
    apiBaseUrl,
    fetchWithAuth,
    selectedFloor,
    setSearchParam,
    setShellFeed
  } = useOperationsShell();
  const [searchParams] = useSearchParams();
  const [floorDetail, setFloorDetail] = useState<FloorDetail | null>(null);
  const [locations, setLocations] = useState<AssetLocationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState(searchParams.get("search") ?? "");
  const [socketConnected, setSocketConnected] = useState(false);
  const deferredSearch = useDeferredValue(searchInput);
  const selectedAssetId = searchParams.get("asset_tag_id");
  const assetCategory = searchParams.get("asset_category");
  const confidenceLevel = searchParams.get("confidence_level") as LocationConfidenceLevel | null;
  const locationType = searchParams.get("location_type");
  const floorImageUrl = useAuthorizedFloorPlan(floorDetail?.floor_plan ?? null, fetchWithAuth);

  useEffect(() => {
    setSearchInput(searchParams.get("search") ?? "");
  }, [searchParams]);

  useEffect(() => {
    if ((searchParams.get("search") ?? "") === deferredSearch) {
      return;
    }
    setSearchParam("search", deferredSearch || null);
  }, [deferredSearch, searchParams, setSearchParam]);

  useEffect(() => {
    let cancelled = false;

    async function loadFloor() {
      if (!selectedFloor?.id) {
        setFloorDetail(null);
        return;
      }
      try {
        const response = await fetchWithAuth(`/api/admin/floors/${selectedFloor.id}`);
        if (!response.ok) {
          throw new Error("Unable to load floor detail");
        }
        const payload = (await response.json()) as FloorDetail;
        if (!cancelled) {
          setFloorDetail(payload);
        }
      } catch {
        if (!cancelled) {
          setFloorDetail(null);
        }
      }
    }

    void loadFloor();
    return () => {
      cancelled = true;
    };
  }, [fetchWithAuth, selectedFloor?.id]);

  useEffect(() => {
    let cancelled = false;

    async function loadLocations() {
      if (!selectedFloor?.id) {
        setLocations([]);
        setLoading(false);
        return;
      }
      setLoading(true);
      try {
        const params = new URLSearchParams({ floor_id: selectedFloor.id });
        if (deferredSearch) {
          params.set("search", deferredSearch);
        }
        if (assetCategory) {
          params.set("asset_category", assetCategory);
        }
        if (confidenceLevel) {
          params.set("confidence_level", confidenceLevel);
        }
        if (locationType) {
          params.set("location_type", locationType);
        }
        const response = await fetchWithAuth(`/api/locations/live?${params.toString()}`);
        if (!response.ok) {
          throw new Error("Unable to load live map");
        }
        const payload = (await response.json()) as AssetLocationRecord[];
        if (!cancelled) {
          setLocations(payload);
          setError(null);
        }
      } catch {
        if (!cancelled) {
          setLocations([]);
          setError("Unable to load live map data.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadLocations();
    return () => {
      cancelled = true;
    };
  }, [assetCategory, confidenceLevel, deferredSearch, fetchWithAuth, locationType, selectedFloor?.id]);

  useEffect(() => {
    if (!selectedFloor?.id || !accessToken) {
      setSocketConnected(false);
      return;
    }

    const wsUrl = new URL(apiBaseUrl);
    wsUrl.protocol = wsUrl.protocol === "https:" ? "wss:" : "ws:";
    wsUrl.pathname = "/ws/locations";
    wsUrl.searchParams.set("access_token", accessToken);
    wsUrl.searchParams.set("floor_id", selectedFloor.id);
    if (deferredSearch) {
      wsUrl.searchParams.set("search", deferredSearch);
    }
    if (assetCategory) {
      wsUrl.searchParams.set("asset_category", assetCategory);
    }

    const socket = new WebSocket(wsUrl.toString());
    socket.onopen = () => setSocketConnected(true);
    socket.onclose = () => setSocketConnected(false);
    socket.onerror = () => setSocketConnected(false);
    // The socket only publishes new positions, so the page keeps its initial snapshot and upserts updates.
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data) as LiveLocationStreamEvent;
      const nextLocation = payload.location;
      if (!matchesClientFilters(nextLocation, { confidenceLevel, locationType })) {
        return;
      }
      setLocations((currentLocations) => {
        const remaining = currentLocations.filter(
          (location) => location.asset_tag_id !== nextLocation.asset_tag_id
        );
        return [...remaining, nextLocation].sort((left, right) =>
          left.display_name.localeCompare(right.display_name)
        );
      });
    };

    return () => {
      socket.close();
    };
  }, [accessToken, apiBaseUrl, assetCategory, confidenceLevel, deferredSearch, locationType, selectedFloor?.id]);

  useEffect(() => {
    if (!selectedFloor?.id) {
      setShellFeed("empty", null);
      return;
    }
    if (locations.length === 0) {
      setShellFeed(error ? "degraded" : "empty", null);
      return;
    }
    const updatedAt = latestObservedAt(locations);
    const stale = updatedAt ? Date.now() - Date.parse(updatedAt) > 120000 : true;
    if (!socketConnected || stale) {
      setShellFeed("degraded", updatedAt);
      return;
    }
    setShellFeed("live", updatedAt);
  }, [error, locations, selectedFloor?.id, setShellFeed, socketConnected]);

  const selectedAsset = locations.find((location) => location.asset_tag_id === selectedAssetId) ?? null;
  const categoryOptions = uniqueValues(locations.map((location) => location.asset_category));

  return (
    <div className="live-map-layout">
      <header className="panel live-map-header">
        <div>
          <p className="eyebrow">Live Map</p>
          <h2>{selectedFloor?.name ?? "Awaiting mapped floor"}</h2>
          <p className="muted-text">
            Search tracked assets, filter confidence, and inspect live floor activity without leaving the map.
          </p>
        </div>
        <div className="live-map-controls">
          <input
            aria-label="Search assets"
            placeholder="Search asset, zone, or tag ID"
            type="search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
          />
          <select
            aria-label="Asset category"
            value={assetCategory ?? ""}
            onChange={(event) => setSearchParam("asset_category", event.target.value || null)}
          >
            <option value="">All categories</option>
            {categoryOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
          <select
            aria-label="Confidence level"
            value={confidenceLevel ?? ""}
            onChange={(event) => setSearchParam("confidence_level", event.target.value || null)}
          >
            <option value="">All confidence</option>
            <option value="high">High confidence</option>
            <option value="medium">Medium confidence</option>
            <option value="low">Low confidence</option>
          </select>
          <select
            aria-label="Location type"
            value={locationType ?? ""}
            onChange={(event) => setSearchParam("location_type", event.target.value || null)}
          >
            <option value="">All location types</option>
            <option value="point">Point markers</option>
            <option value="zone">Zone fallback</option>
          </select>
        </div>
      </header>

      <div className="live-map-grid">
        <aside className="panel live-map-sidebar">
          <div className="stack-card__header">
            <div>
              <p className="eyebrow">Filters</p>
              <h2>Visible context</h2>
            </div>
          </div>
          <dl className="definition-list">
            <div>
              <dt>Floor</dt>
              <dd>{selectedFloor?.name ?? "No floor selected"}</dd>
            </div>
            <div>
              <dt>Locations</dt>
              <dd>{locations.length}</dd>
            </div>
            <div>
              <dt>Socket</dt>
              <dd>{socketConnected ? "Connected" : "Disconnected"}</dd>
            </div>
          </dl>
          <div className="legend-list">
            <LegendItem label="High confidence point" tone="high" />
            <LegendItem label="Medium confidence radius" tone="medium" />
            <LegendItem label="Low-confidence zone fallback" tone="low" />
            <LegendItem label="Gateway placement" tone="gateway" />
          </div>
        </aside>

        <section className="panel live-map-canvas-panel">
          {loading ? (
            <div className="map-state">
              <h3>Loading live map</h3>
              <p className="muted-text">Resolving the mapped floor and current asset positions.</p>
            </div>
          ) : error ? (
            <div className="map-state">
              <h3>Map unavailable</h3>
              <p className="muted-text">{error}</p>
            </div>
          ) : (
            <MapCanvas
              areas={floorDetail?.areas ?? []}
              floorImageUrl={floorImageUrl}
              floorPlan={floorDetail?.floor_plan ?? null}
              gateways={floorDetail?.gateways ?? []}
              locations={locations}
              onSelectAsset={(assetTagId) => setSearchParam("asset_tag_id", assetTagId)}
              selectedAssetId={selectedAssetId}
              showGateways
              showZones
            />
          )}
        </section>

        <aside className="live-map-right-column">
          <section className="panel asset-drawer">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Selected Asset</p>
                <h2>{selectedAsset?.display_name ?? "Nothing selected"}</h2>
              </div>
              {selectedAsset ? (
                <button className="secondary-button" onClick={() => setSearchParam("asset_tag_id", null)} type="button">
                  Clear
                </button>
              ) : null}
            </div>
            {selectedAsset ? (
              <dl className="definition-list">
                <div>
                  <dt>Tag ID</dt>
                  <dd>{selectedAsset.tag_identifier}</dd>
                </div>
                <div>
                  <dt>Category</dt>
                  <dd>{selectedAsset.asset_category}</dd>
                </div>
                <div>
                  <dt>Current Zone</dt>
                  <dd>{selectedAsset.zone_name ?? "Point-only context"}</dd>
                </div>
                <div>
                  <dt>Confidence</dt>
                  <dd>{selectedAsset.confidence_level}</dd>
                </div>
                <div>
                  <dt>Last Seen</dt>
                  <dd>{relativeTime(selectedAsset.observed_at)}</dd>
                </div>
              </dl>
            ) : (
              <p className="empty-copy">Select an asset from the map or recent activity to inspect its latest known context.</p>
            )}
          </section>

          <section className="panel activity-panel">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Recent Activity</p>
                <h2>Latest movements</h2>
              </div>
            </div>
            <div className="activity-list">
              {locations
                .slice()
                .sort((left, right) => Date.parse(right.observed_at) - Date.parse(left.observed_at))
                .slice(0, 6)
                .map((location) => (
                  <button
                    key={location.asset_tag_id}
                    className={
                      location.asset_tag_id === selectedAssetId
                        ? "activity-row activity-row--active"
                        : "activity-row"
                    }
                    onClick={() => setSearchParam("asset_tag_id", location.asset_tag_id)}
                    type="button"
                  >
                    <div>
                      <strong>{location.display_name}</strong>
                      <span>{location.zone_name ?? location.floor_name}</span>
                    </div>
                    <span className={`status-badge status-badge--${location.confidence_level}`}>
                      {location.confidence_level}
                    </span>
                  </button>
                ))}
            </div>
          </section>
        </aside>
      </div>
    </div>
  );
}

function KpiCard({
  label,
  value,
  tone
}: {
  label: string;
  value: number;
  tone: "live" | "warning" | "critical";
}) {
  return (
    <article className={`panel kpi-card kpi-card--${tone}`}>
      <p className="eyebrow">{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function LegendItem({ label, tone }: { label: string; tone: "high" | "medium" | "low" | "gateway" }) {
  return (
    <div className="legend-item">
      <span className={`legend-swatch legend-swatch--${tone}`} />
      <span>{label}</span>
    </div>
  );
}

function MapCanvas({
  areas,
  compact = false,
  floorImageUrl,
  floorPlan,
  gateways,
  locations,
  onSelectAsset,
  selectedAssetId,
  showGateways,
  showZones
}: {
  areas: SpatialAreaRecord[];
  compact?: boolean;
  floorImageUrl: string | null;
  floorPlan: FloorPlanAsset | null;
  gateways: GatewayRecord[];
  locations: AssetLocationRecord[];
  onSelectAsset: (assetTagId: string) => void;
  selectedAssetId: string | null;
  showGateways: boolean;
  showZones: boolean;
}) {
  const width = floorPlan?.width_px ?? DEFAULT_MAP_WIDTH;
  const height = floorPlan?.height_px ?? DEFAULT_MAP_HEIGHT;
  const areasById = new Map(areas.map((area) => [area.id, area] as const));

  return (
    <div className={compact ? "map-surface map-surface--compact" : "map-surface"}>
      <svg viewBox={`0 0 ${width} ${height}`} aria-label="Floor map">
        <rect className="map-surface__background" height={height} rx={20} ry={20} width={width} x={0} y={0} />
        {floorImageUrl ? <image height={height} href={floorImageUrl} preserveAspectRatio="none" width={width} x={0} y={0} /> : null}
        {showZones
          ? areas.map((area) => (
              <polygon
                key={area.id}
                className={`map-area map-area--${area.area_type}`}
                points={area.points.map((point) => `${point.x * width},${point.y * height}`).join(" ")}
              />
            ))
          : null}
        {locations
          .filter((location) => location.location_type === "zone" && location.zone_id)
          .map((location) => {
            const zone = areasById.get(location.zone_id ?? "");
            if (!zone) {
              return null;
            }
            return (
              <polygon
                key={`zone-${location.asset_tag_id}`}
                className={
                  location.asset_tag_id === selectedAssetId
                    ? "map-area map-area--fallback-selected"
                    : "map-area map-area--fallback"
                }
                points={zone.points.map((point) => `${point.x * width},${point.y * height}`).join(" ")}
              />
            );
          })}
        {showGateways
          ? gateways.map((gateway) => (
              <g key={gateway.id} className="map-gateway">
                <circle cx={gateway.placement.x * width} cy={gateway.placement.y * height} r={10} />
                {!compact ? (
                  <text x={gateway.placement.x * width + 14} y={gateway.placement.y * height + 4}>
                    {gateway.display_name}
                  </text>
                ) : null}
              </g>
            ))
          : null}
        {locations.map((location) => {
          const marker = location.point
            ? { x: location.point.x * width, y: location.point.y * height }
            : centroidForZone(location.zone_id, areasById, width, height);
          if (!marker) {
            return null;
          }
          return (
            <g
              key={location.asset_tag_id}
              className={`map-marker map-marker--${location.confidence_level} ${
                location.asset_tag_id === selectedAssetId ? "map-marker--selected" : ""
              }`}
              onClick={() => onSelectAsset(location.asset_tag_id)}
            >
              {location.confidence_level === "medium" ? (
                <circle cx={marker.x} cy={marker.y} r={20} className="map-marker__halo" />
              ) : null}
              <circle cx={marker.x} cy={marker.y} r={10} className="map-marker__dot" />
              {!compact ? (
                <text x={marker.x + 14} y={marker.y + 4}>
                  {location.display_name}
                </text>
              ) : null}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function useAuthorizedFloorPlan(
  floorPlan: FloorPlanAsset | null,
  fetchWithAuth: ReturnType<typeof useAuth>["fetchWithAuth"]
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

function centroidForZone(
  zoneId: string | null,
  areasById: Map<string, SpatialAreaRecord>,
  width: number,
  height: number
) {
  if (!zoneId) {
    return null;
  }
  const area = areasById.get(zoneId);
  if (!area || area.points.length === 0) {
    return null;
  }
  const total = area.points.reduce(
    (accumulator, point) => ({
      x: accumulator.x + point.x,
      y: accumulator.y + point.y
    }),
    { x: 0, y: 0 }
  );
  return {
    x: (total.x / area.points.length) * width,
    y: (total.y / area.points.length) * height
  };
}

function latestObservedAt(locations: AssetLocationRecord[]) {
  if (locations.length === 0) {
    return null;
  }
  return locations.reduce((latest, location) =>
    Date.parse(location.observed_at) > Date.parse(latest) ? location.observed_at : latest
  , locations[0].observed_at);
}

function feedStatusLabel(status: OperationsFeedStatus) {
  if (status === "live") {
    return "Live Feed Stable";
  }
  if (status === "degraded") {
    return "Feed Degraded";
  }
  return "Awaiting Telemetry";
}

function relativeTime(value: string) {
  const deltaMs = Date.now() - Date.parse(value);
  const deltaMinutes = Math.round(deltaMs / 60000);
  if (Math.abs(deltaMinutes) < 1) {
    return "just now";
  }
  if (Math.abs(deltaMinutes) < 60) {
    return `${Math.abs(deltaMinutes)} min ago`;
  }
  const deltaHours = Math.round(deltaMinutes / 60);
  if (Math.abs(deltaHours) < 24) {
    return `${Math.abs(deltaHours)} h ago`;
  }
  const deltaDays = Math.round(deltaHours / 24);
  return `${Math.abs(deltaDays)} d ago`;
}

function uniqueValues(values: string[]) {
  return [...new Set(values.filter(Boolean))].sort((left, right) => left.localeCompare(right));
}

function matchesClientFilters(
  location: AssetLocationRecord,
  filters: {
    confidenceLevel: LocationConfidenceLevel | null;
    locationType: string | null;
  }
) {
  if (filters.confidenceLevel && location.confidence_level !== filters.confidenceLevel) {
    return false;
  }
  if (filters.locationType && location.location_type !== filters.locationType) {
    return false;
  }
  return true;
}
