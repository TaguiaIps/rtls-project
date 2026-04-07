import type {
  AdminSummary,
  AssetBatteryProfile,
  AssetTagImportConfirmResult,
  AssetTagImportValidateResult,
  AssetTagRecord,
  AssetUpdateRateProfile,
  FloorDetail,
  FloorSummary,
  GatewayHardwareTier,
  GatewayRecord,
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
import { CommandInput, FormMessage } from "../components/FormErgonomics";
import { inputMasks, useTechnicalValidation } from "../components/formUtils";
import { IconCheckCircle } from "../components/Icons";

type ScaleTarget = "point_a" | "point_b" | null;
type EditorMode = ScaleTarget | "polygon" | "gateway";

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

type GatewayDraftState = {
  id: string | null;
  gatewayIdentifier: string;
  displayName: string;
  hardwareTier: GatewayHardwareTier;
  placement: SpatialPoint | null;
  notes: string;
};

type AssetDraftState = {
  id: string | null;
  tagIdentifier: string;
  displayName: string;
  assetCategory: string;
  updateRateProfile: AssetUpdateRateProfile;
  batteryProfile: AssetBatteryProfile;
};

const DEFAULT_SCALE_FORM: ScaleFormState = {
  pointA: null,
  pointB: null,
  realWorldDistanceM: "10"
};

const DEFAULT_AREA_DRAFT: AreaDraftState = {
  id: null,
  name: "",
  areaType: "zone",
  points: [],
  slaEligible: false,
  alertParticipation: true
};

const DEFAULT_GATEWAY_DRAFT: GatewayDraftState = {
  id: null,
  gatewayIdentifier: "",
  displayName: "",
  hardwareTier: "Economic",
  placement: null,
  notes: ""
};

const DEFAULT_ASSET_DRAFT: AssetDraftState = {
  id: null,
  tagIdentifier: "",
  displayName: "",
  assetCategory: "",
  updateRateProfile: "balanced",
  batteryProfile: "standard"
};

const AREA_TYPE_LABELS: Record<SpatialAreaType, string> = {
  zone: "Zone",
  table: "Table",
  restricted_zone: "Restricted Zone",
  poi: "Point of Interest"
};

const GATEWAY_TIER_LABELS: Record<GatewayHardwareTier, string> = {
  Economic: "Economic",
  Premium: "Premium"
};

const UPDATE_RATE_LABELS: Record<AssetUpdateRateProfile, string> = {
  slow: "Slow",
  balanced: "Balanced",
  realtime: "Realtime"
};

const BATTERY_PROFILE_LABELS: Record<AssetBatteryProfile, string> = {
  long_life: "Long Life",
  standard: "Standard",
  performance: "Performance"
};

const ASSET_IMPORT_COLUMNS = [
  "tag_identifier",
  "display_name",
  "asset_category",
  "update_rate_profile",
  "battery_profile"
] as const;

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

function normalizePoint(point: SpatialPoint) {
  return {
    x: Number(point.x.toFixed(4)),
    y: Number(point.y.toFixed(4))
  };
}

function toSvgX(point: SpatialPoint, width: number) {
  return point.x * width;
}

function toSvgY(point: SpatialPoint, height: number) {
  return point.y * height;
}

function pointsToSvg(points: SpatialPoint[], width: number, height: number) {
  return points
    .map((point) => `${toSvgX(point, width)},${toSvgY(point, height)}`)
    .join(" ");
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

function cloneGatewayDraft(gateway: GatewayRecord): GatewayDraftState {
  return {
    id: gateway.id,
    gatewayIdentifier: gateway.gateway_identifier,
    displayName: gateway.display_name,
    hardwareTier: gateway.hardware_tier,
    placement: { ...gateway.placement },
    notes: gateway.notes ?? ""
  };
}

function cloneAssetDraft(asset: AssetTagRecord): AssetDraftState {
  return {
    id: asset.id,
    tagIdentifier: asset.tag_identifier,
    displayName: asset.display_name,
    assetCategory: asset.asset_category,
    updateRateProfile: asset.update_rate_profile,
    batteryProfile: asset.battery_profile
  };
}

function getCanvasToolLabel(editorMode: EditorMode) {
  switch (editorMode) {
    case "point_a":
      return "Scale Point A";
    case "point_b":
      return "Scale Point B";
    case "polygon":
      return "Polygon Draft";
    case "gateway":
      return "Gateway Placement";
    default:
      return "No active targeting tool";
  }
}

function getContainedImageBounds(
  bounds: DOMRect,
  imageWidth: number,
  imageHeight: number
) {
  const imageAspect = imageWidth / imageHeight;
  const boundsAspect = bounds.width / bounds.height;

  if (boundsAspect > imageAspect) {
    const height = bounds.height;
    const width = height * imageAspect;
    return {
      left: bounds.left + (bounds.width - width) / 2,
      top: bounds.top,
      width,
      height
    };
  }

  const width = bounds.width;
  const height = width / imageAspect;
  return {
    left: bounds.left,
    top: bounds.top + (bounds.height - height) / 2,
    width,
    height
  };
}

function getNormalizedCanvasPoint(
  event: MouseEvent<HTMLDivElement>,
  imageWidth: number,
  imageHeight: number
) {
  const bounds = event.currentTarget.getBoundingClientRect();
  if (bounds.width <= 0 || bounds.height <= 0) {
    return null;
  }

  const imageBounds = getContainedImageBounds(bounds, imageWidth, imageHeight);
  if (imageBounds.width <= 0 || imageBounds.height <= 0) {
    return null;
  }

  const x = (event.clientX - imageBounds.left) / imageBounds.width;
  const y = (event.clientY - imageBounds.top) / imageBounds.height;
  if (x < 0 || x > 1 || y < 0 || y > 1) {
    return null;
  }

  return normalizePoint({ x, y });
}

export function AdminSpatialWorkspace() {
  const { fetchWithAuth, user } = useAuth();
  const [managedRoles, setManagedRoles] = useState<string[]>([]);
  const [sites, setSites] = useState<SiteRecord[]>([]);
  const [assetTags, setAssetTags] = useState<AssetTagRecord[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<string | null>(null);
  const [selectedFloorId, setSelectedFloorId] = useState<string | null>(null);
  const [selectedAreaId, setSelectedAreaId] = useState<string | null>(null);
  const [selectedGatewayId, setSelectedGatewayId] = useState<string | null>(
    null
  );
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [floorDetail, setFloorDetail] = useState<FloorDetail | null>(null);
  const [floorPlanUrl, setFloorPlanUrl] = useState<string | null>(null);
  const [siteName, setSiteName] = useState("");
  const [siteTimezone, setSiteTimezone] = useState("America/Bahia");
  const [floorName, setFloorName] = useState("");
  const [floorLevelLabel, setFloorLevelLabel] = useState("");
  const [floorPlanFile, setFloorPlanFile] = useState<File | null>(null);
  const [assetImportFile, setAssetImportFile] = useState<File | null>(null);
  const [assetImportInputKey, setAssetImportInputKey] = useState(0);
  const [assetImportValidation, setAssetImportValidation] =
    useState<AssetTagImportValidateResult | null>(null);
  const [scaleForm, setScaleForm] =
    useState<ScaleFormState>(DEFAULT_SCALE_FORM);
  const [areaDraft, setAreaDraft] =
    useState<AreaDraftState>(DEFAULT_AREA_DRAFT);
  const [gatewayDraft, setGatewayDraft] = useState<GatewayDraftState>(
    DEFAULT_GATEWAY_DRAFT
  );
  const [assetDraft, setAssetDraft] =
    useState<AssetDraftState>(DEFAULT_ASSET_DRAFT);
  const [editorMode, setEditorMode] = useState<EditorMode>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [isFloorLoading, setIsFloorLoading] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackState>(null);
  const { errors, validateTagId, validateMacAddress, clearError, setError: setValidationError } = useTechnicalValidation();

  const selectedSite =
    sites.find((site) => site.id === selectedSiteId) ??
    (sites.length > 0 ? sites[0] : null);
  const selectedFloor =
    selectedSite?.floors.find((floor) => floor.id === selectedFloorId) ??
    selectedSite?.floors[0] ??
    null;
  const selectedGateway =
    floorDetail?.gateways.find((gateway) => gateway.id === selectedGatewayId) ??
    null;

  const requestJson = useCallback(
    async <T,>(path: string, init?: RequestInit): Promise<T> => {
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
    },
    [fetchWithAuth]
  );

  const loadSites = useCallback(
    async (
      preferredSiteId?: string | null,
      preferredFloorId?: string | null
    ) => {
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
    },
    [requestJson, selectedFloorId, selectedSiteId]
  );

  const loadAssetTags = useCallback(async () => {
    const nextAssets = await requestJson<AssetTagRecord[]>("/api/admin/assets");
    setAssetTags(nextAssets);
  }, [requestJson]);

  const loadFloorDetail = useCallback(
    async (floorId: string) => {
      setIsFloorLoading(true);
      try {
        const detail = await requestJson<FloorDetail>(
          `/api/admin/floors/${floorId}`
        );
        setFloorDetail(detail);
        setSelectedFloorId(detail.id);
        setSelectedAreaId((current) =>
          detail.areas.some((area) => area.id === current) ? current : null
        );
        setSelectedGatewayId((current) =>
          detail.gateways.some((gateway) => gateway.id === current)
            ? current
            : null
        );
      } finally {
        setIsFloorLoading(false);
      }
    },
    [requestJson]
  );

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      setIsBusy(true);
      try {
        const [summary, siteRecords, assets] = await Promise.all([
          requestJson<AdminSummary>("/api/admin/summary"),
          requestJson<SiteRecord[]>("/api/admin/sites"),
          requestJson<AssetTagRecord[]>("/api/admin/assets")
        ]);
        if (!active) {
          return;
        }

        setManagedRoles(summary.managed_roles);
        setSites(siteRecords);
        setAssetTags(assets);
        setSelectedSiteId(siteRecords[0]?.id ?? null);
        setSelectedFloorId(siteRecords[0]?.floors[0]?.id ?? null);
      } catch (error) {
        if (active) {
          setFeedback({
            tone: "error",
            message:
              (error as Error).message || "Unable to load the Admin Console."
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
      setSelectedAreaId(null);
      setSelectedGatewayId(null);
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
      setScaleForm(DEFAULT_SCALE_FORM);
      setAreaDraft(DEFAULT_AREA_DRAFT);
      setGatewayDraft(DEFAULT_GATEWAY_DRAFT);
      setFloorPlanFile(null);
      setEditorMode(null);
      return;
    }

    setScaleForm({
      pointA: floorDetail.scale?.point_a ?? null,
      pointB: floorDetail.scale?.point_b ?? null,
      realWorldDistanceM: floorDetail.scale
        ? String(floorDetail.scale.real_world_distance_m)
        : DEFAULT_SCALE_FORM.realWorldDistanceM
    });

    setAreaDraft(() => {
      const existingArea = floorDetail.areas.find(
        (area) => area.id === selectedAreaId
      );
      return existingArea ? cloneAreaDraft(existingArea) : DEFAULT_AREA_DRAFT;
    });

    setGatewayDraft(() => {
      const existingGateway = floorDetail.gateways.find(
        (gateway) => gateway.id === selectedGatewayId
      );
      return existingGateway
        ? cloneGatewayDraft(existingGateway)
        : DEFAULT_GATEWAY_DRAFT;
    });
  }, [floorDetail, selectedAreaId, selectedGatewayId]);

  useEffect(() => {
    setAssetDraft(() => {
      const existingAsset = assetTags.find(
        (asset) => asset.id === selectedAssetId
      );
      return existingAsset
        ? cloneAssetDraft(existingAsset)
        : DEFAULT_ASSET_DRAFT;
    });
  }, [assetTags, selectedAssetId]);

  useEffect(() => {
    let objectUrl: string | null = null;
    let active = true;

    async function loadFloorPlanImage() {
      if (!floorDetail?.floor_plan) {
        setFloorPlanUrl(null);
        return;
      }

      try {
        const response = await fetchWithAuth(
          floorDetail.floor_plan.file_download_path
        );
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
            message:
              (error as Error).message || "Unable to load the floor-plan image."
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
      const floor = await requestJson<FloorSummary>(
        `/api/admin/sites/${selectedSite.id}/floors`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: floorName.trim(),
            level_label: floorLevelLabel.trim() || null
          })
        }
      );
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
      setFeedback({
        tone: "error",
        message: "Choose a PNG or JPG floor plan first."
      });
      return;
    }

    const formData = new FormData();
    formData.append("floor_plan", floorPlanFile);

    setIsBusy(true);
    setFeedback(null);
    try {
      const response = await fetchWithAuth(
        `/api/admin/floors/${selectedFloorId}/floor-plan`,
        {
          method: "POST",
          body: formData
        }
      );
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
      await requestJson<FloorDetail>(
        `/api/admin/floors/${selectedFloorId}/scale`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            point_a: scaleForm.pointA,
            point_b: scaleForm.pointB,
            real_world_distance_m: Number(scaleForm.realWorldDistanceM)
          })
        }
      );
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
    if (editorMode === "polygon") {
      setEditorMode(null);
    }
  }

  function resetGatewayDraft() {
    setGatewayDraft(DEFAULT_GATEWAY_DRAFT);
    setSelectedGatewayId(null);
    if (editorMode === "gateway") {
      setEditorMode(null);
    }
  }

  function resetAssetDraft() {
    setAssetDraft(DEFAULT_ASSET_DRAFT);
    setSelectedAssetId(null);
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
      let areaId = areaDraft.id;
      if (areaDraft.id) {
        const area = await requestJson<SpatialAreaRecord>(
          `/api/admin/areas/${areaDraft.id}`,
          {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          }
        );
        areaId = area.id;
      } else {
        const area = await requestJson<SpatialAreaRecord>(
          `/api/admin/floors/${selectedFloorId}/areas`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
          }
        );
        areaId = area.id;
      }

      await loadFloorDetail(selectedFloorId);
      setSelectedAreaId(areaId);
      setEditorMode(null);
      setFeedback({
        tone: "success",
        message: areaDraft.id
          ? "Operational area updated."
          : "Operational area created."
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

  async function handleSaveGateway() {
    if (!selectedFloorId) {
      return;
    }
    if (!gatewayDraft.gatewayIdentifier.trim()) {
      setFeedback({
        tone: "error",
        message: "Gateway identifier is required."
      });
      return;
    }
    if (!gatewayDraft.displayName.trim()) {
      setFeedback({
        tone: "error",
        message: "Gateway display name is required."
      });
      return;
    }
    if (!gatewayDraft.placement) {
      setFeedback({
        tone: "error",
        message: "Place the gateway on the floor plan before saving it."
      });
      return;
    }

    const createPayload = {
      gateway_identifier: gatewayDraft.gatewayIdentifier.trim(),
      display_name: gatewayDraft.displayName.trim(),
      hardware_tier: gatewayDraft.hardwareTier,
      placement: gatewayDraft.placement,
      notes: gatewayDraft.notes.trim() || null
    };

    const updatePayload = {
      display_name: gatewayDraft.displayName.trim(),
      hardware_tier: gatewayDraft.hardwareTier,
      placement: gatewayDraft.placement,
      notes: gatewayDraft.notes.trim() || null
    };

    setIsBusy(true);
    setFeedback(null);
    try {
      const gateway = gatewayDraft.id
        ? await requestJson<GatewayRecord>(
            `/api/admin/gateways/${gatewayDraft.id}`,
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(updatePayload)
            }
          )
        : await requestJson<GatewayRecord>(
            `/api/admin/floors/${selectedFloorId}/gateways`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(createPayload)
            }
          );

      await loadFloorDetail(selectedFloorId);
      setSelectedGatewayId(gateway.id);
      setEditorMode(null);
      setFeedback({
        tone: "success",
        message: gatewayDraft.id
          ? "Gateway placement updated."
          : "Gateway created."
      });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteGateway() {
    if (!gatewayDraft.id) {
      return;
    }

    setIsBusy(true);
    setFeedback(null);
    try {
      const response = await fetchWithAuth(
        `/api/admin/gateways/${gatewayDraft.id}`,
        {
          method: "DELETE"
        }
      );
      if (!response.ok) {
        throw new Error(parseErrorMessage(await response.json()));
      }

      if (selectedFloorId) {
        await loadFloorDetail(selectedFloorId);
      }
      resetGatewayDraft();
      setFeedback({ tone: "success", message: "Gateway deleted." });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSaveAsset() {
    if (!assetDraft.tagIdentifier.trim()) {
      setFeedback({
        tone: "error",
        message: "Asset tag identifier is required."
      });
      return;
    }
    if (!assetDraft.displayName.trim()) {
      setFeedback({
        tone: "error",
        message: "Asset display name is required."
      });
      return;
    }
    if (!assetDraft.assetCategory.trim()) {
      setFeedback({ tone: "error", message: "Asset category is required." });
      return;
    }

    const createPayload = {
      tag_identifier: assetDraft.tagIdentifier.trim(),
      display_name: assetDraft.displayName.trim(),
      asset_category: assetDraft.assetCategory.trim(),
      update_rate_profile: assetDraft.updateRateProfile,
      battery_profile: assetDraft.batteryProfile
    };

    const updatePayload = {
      display_name: assetDraft.displayName.trim(),
      asset_category: assetDraft.assetCategory.trim(),
      update_rate_profile: assetDraft.updateRateProfile,
      battery_profile: assetDraft.batteryProfile
    };

    setIsBusy(true);
    setFeedback(null);
    try {
      const asset = assetDraft.id
        ? await requestJson<AssetTagRecord>(
            `/api/admin/assets/${assetDraft.id}`,
            {
              method: "PATCH",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify(updatePayload)
            }
          )
        : await requestJson<AssetTagRecord>("/api/admin/assets", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(createPayload)
          });

      setSelectedAssetId(asset.id);
      await loadAssetTags();
      setFeedback({
        tone: "success",
        message: assetDraft.id ? "Asset tag updated." : "Asset tag created."
      });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteAsset() {
    if (!assetDraft.id) {
      return;
    }

    setIsBusy(true);
    setFeedback(null);
    try {
      const response = await fetchWithAuth(
        `/api/admin/assets/${assetDraft.id}`,
        {
          method: "DELETE"
        }
      );
      if (!response.ok) {
        throw new Error(parseErrorMessage(await response.json()));
      }

      await loadAssetTags();
      resetAssetDraft();
      setAssetImportValidation(null);
      setFeedback({ tone: "success", message: "Asset tag deleted." });
    } catch (error) {
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleValidateAssetImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assetImportFile) {
      setFeedback({
        tone: "error",
        message: "Choose a CSV file before validating."
      });
      return;
    }

    const formData = new FormData();
    formData.append("import_file", assetImportFile);

    setIsBusy(true);
    setFeedback(null);
    try {
      const response = await fetchWithAuth(
        "/api/admin/assets/imports/validate",
        {
          method: "POST",
          body: formData
        }
      );
      if (!response.ok) {
        throw new Error(parseErrorMessage(await response.json()));
      }

      const result = (await response.json()) as AssetTagImportValidateResult;
      setAssetImportValidation(result);
      setFeedback({
        tone: result.import_id ? "success" : "neutral",
        message: result.import_id
          ? `Import validated. ${result.valid_row_count} asset tags are ready to confirm.`
          : `Import review found ${result.invalid_row_count} invalid row(s).`
      });
    } catch (error) {
      setAssetImportValidation(null);
      setFeedback({ tone: "error", message: (error as Error).message });
    } finally {
      setIsBusy(false);
    }
  }

  async function handleConfirmAssetImport() {
    if (!assetImportValidation?.import_id) {
      return;
    }

    setIsBusy(true);
    setFeedback(null);
    try {
      const result = await requestJson<AssetTagImportConfirmResult>(
        "/api/admin/assets/imports/confirm",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ import_id: assetImportValidation.import_id })
        }
      );
      await loadAssetTags();
      setAssetImportValidation(null);
      setAssetImportFile(null);
      setAssetImportInputKey((current) => current + 1);
      setFeedback({
        tone: "success",
        message: `${result.created_count} asset tag(s) imported into the registry.`
      });
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

    const point = getNormalizedCanvasPoint(
      event,
      floorDetail.floor_plan.width_px,
      floorDetail.floor_plan.height_px
    );
    if (!point) {
      return;
    }

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
    if (editorMode === "gateway") {
      setGatewayDraft((current) => ({ ...current, placement: point }));
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

  function beginNewGateway() {
    setGatewayDraft(DEFAULT_GATEWAY_DRAFT);
    setSelectedGatewayId(null);
    setEditorMode("gateway");
  }

  function selectExistingGateway(gateway: GatewayRecord) {
    setSelectedGatewayId(gateway.id);
    setGatewayDraft(cloneGatewayDraft(gateway));
    setEditorMode(null);
  }

  function beginNewAsset() {
    resetAssetDraft();
  }

  function selectExistingAsset(asset: AssetTagRecord) {
    setSelectedAssetId(asset.id);
    setAssetDraft(cloneAssetDraft(asset));
  }

  function updateDraftPoint(
    index: number,
    axis: keyof SpatialPoint,
    value: string
  ) {
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

  function updateScalePoint(
    target: "pointA" | "pointB",
    axis: keyof SpatialPoint,
    value: string
  ) {
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

  function updateGatewayPlacement(axis: keyof SpatialPoint, value: string) {
    const nextValue = Number(value);
    if (Number.isNaN(nextValue)) {
      return;
    }

    setGatewayDraft((current) => ({
      ...current,
      placement: normalizePoint({
        ...(current.placement ?? { x: 0, y: 0 }),
        [axis]: Math.min(1, Math.max(0, nextValue))
      })
    }));
  }

  function renderAreaLayer(
    area: SpatialAreaRecord,
    width: number,
    height: number
  ) {
    const isSelected = area.id === selectedAreaId;
    const firstPoint = area.points[0];
    return (
      <g key={area.id}>
        <polygon
          className={`map-area map-area--${area.area_type}${isSelected ? " map-area--selected" : ""}`}
          points={pointsToSvg(area.points, width, height)}
        />
        {firstPoint ? (
          <text
            className="map-area__label"
            x={toSvgX(firstPoint, width)}
            y={Math.max(24, toSvgY(firstPoint, height) - 18)}
          >
            {area.name}
          </text>
        ) : null}
      </g>
    );
  }

  function renderGatewayLayer(
    gateway: GatewayRecord,
    width: number,
    height: number
  ) {
    const isSelected = gateway.id === selectedGatewayId;
    const labelY = Math.max(28, toSvgY(gateway.placement, height) - 24);
    return (
      <g key={gateway.id}>
        <circle
          className={`map-gateway${isSelected ? " map-gateway--selected" : ""}`}
          cx={toSvgX(gateway.placement, width)}
          cy={toSvgY(gateway.placement, height)}
          r="14"
        />
        <text
          className="map-gateway__label"
          x={toSvgX(gateway.placement, width)}
          y={labelY}
        >
          {gateway.display_name}
        </text>
      </g>
    );
  }

  const floorPlanWidth = floorDetail?.floor_plan?.width_px ?? 100;
  const floorPlanHeight = floorDetail?.floor_plan?.height_px ?? 100;

  return (
    <section className="admin-spatial-shell">
      <div className="admin-spatial-header">
        <div>
          <p className="eyebrow">RTLS Admin Setup</p>
          <h1>Admin Spatial Workspace</h1>
          <p className="panel-copy">
            Configure sites, floors, floor plans, scale, zones, gateway
            placement, and the asset registry before ingestion, calibration, and
            live map workflows are enabled.
          </p>
        </div>
        <div className="status-strip">
          <span>{user?.email}</span>
          <span>{managedRoles.join(" / ") || "Administrator"}</span>
          <span>
            {floorDetail?.floor_plan
              ? "Floor plan ready"
              : "Awaiting floor plan"}
          </span>
        </div>
      </div>

      {feedback ? (
        <div className={`feedback-banner feedback-banner--${feedback.tone}`}>
          {feedback.message}
        </div>
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
              <button
                className="primary-button"
                disabled={isBusy || !siteName.trim()}
                type="submit"
              >
                Create Site
              </button>
            </form>

            <div className="selection-list">
              {sites.length === 0 ? (
                <p className="empty-copy">
                  Create the first site to unlock floor planning.
                </p>
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
              <span className="metric-chip">
                {selectedSite?.floors.length ?? 0} floor(s)
              </span>
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
                <p className="empty-copy">
                  No floors configured for the selected site yet.
                </p>
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
                  <strong>
                    {floorDetail?.floor_plan ? "Uploaded" : "Missing"}
                  </strong>
                </div>
                <div>
                  <span className="summary-label">Scale</span>
                  <strong>
                    {floorDetail?.scale ? "Confirmed" : "Pending"}
                  </strong>
                </div>
                <div>
                  <span className="summary-label">Gateways</span>
                  <strong>{floorDetail?.gateways.length ?? 0}</strong>
                </div>
                <div>
                  <span className="summary-label">Operational Areas</span>
                  <strong>{floorDetail?.areas.length ?? 0}</strong>
                </div>
              </div>
            ) : (
              <p className="empty-copy">
                Choose a site and floor from the left rail to start the admin
                setup flow.
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

              <form
                className="admin-form admin-form--inline"
                onSubmit={handleUploadFloorPlan}
              >
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
                  <button
                    className="tool-button"
                    onClick={() => setEditorMode(null)}
                    type="button"
                  >
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
                      onChange={(event) =>
                        updateScalePoint("pointA", "x", event.target.value)
                      }
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
                      onChange={(event) =>
                        updateScalePoint("pointA", "y", event.target.value)
                      }
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
                      onChange={(event) =>
                        updateScalePoint("pointB", "x", event.target.value)
                      }
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
                      onChange={(event) =>
                        updateScalePoint("pointB", "y", event.target.value)
                      }
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
                  <h2>Map Editor</h2>
                </div>
                <span className="metric-chip">
                  {isFloorLoading
                    ? "Loading floor..."
                    : `${floorDetail?.areas.length ?? 0} areas · ${floorDetail?.gateways.length ?? 0} gateways`}
                </span>
              </div>

              <div
                className={`map-canvas${editorMode ? " map-canvas--targeting" : ""}`}
                onClick={handleCanvasClick}
                role="presentation"
              >
                {floorPlanUrl ? (
                  <>
                    <img
                      alt="Floor plan preview"
                      className="map-canvas__image"
                      src={floorPlanUrl}
                    />
                    <svg
                      className="map-canvas__overlay"
                      viewBox={`0 0 ${floorPlanWidth} ${floorPlanHeight}`}
                      preserveAspectRatio="xMidYMid meet"
                    >
                      {floorDetail?.areas.map((area) =>
                        renderAreaLayer(area, floorPlanWidth, floorPlanHeight)
                      )}
                      {floorDetail?.gateways.map((gateway) =>
                        renderGatewayLayer(
                          gateway,
                          floorPlanWidth,
                          floorPlanHeight
                        )
                      )}

                      {areaDraft.points.length >= 1 ? (
                        <g>
                          {areaDraft.points.length >= 2 ? (
                            <polyline
                              className="map-draft map-draft--line"
                              points={pointsToSvg(
                                areaDraft.points,
                                floorPlanWidth,
                                floorPlanHeight
                              )}
                            />
                          ) : null}
                          {areaDraft.points.length >= 3 ? (
                            <polygon
                              className="map-draft map-draft--polygon"
                              points={pointsToSvg(
                                areaDraft.points,
                                floorPlanWidth,
                                floorPlanHeight
                              )}
                            />
                          ) : null}
                          {areaDraft.points.map((point, index) => (
                            <circle
                              key={`${point.x}-${point.y}-${index}`}
                              className="map-point map-point--draft"
                              cx={toSvgX(point, floorPlanWidth)}
                              cy={toSvgY(point, floorPlanHeight)}
                              r="10"
                            />
                          ))}
                        </g>
                      ) : null}

                      {selectedGateway &&
                      !gatewayDraft.id ? null : gatewayDraft.placement ? (
                        <circle
                          className="map-point map-point--gateway-draft"
                          cx={toSvgX(gatewayDraft.placement, floorPlanWidth)}
                          cy={toSvgY(gatewayDraft.placement, floorPlanHeight)}
                          r="12"
                        />
                      ) : null}

                      {scaleForm.pointA && scaleForm.pointB ? (
                        <line
                          className="map-scale"
                          x1={toSvgX(scaleForm.pointA, floorPlanWidth)}
                          x2={toSvgX(scaleForm.pointB, floorPlanWidth)}
                          y1={toSvgY(scaleForm.pointA, floorPlanHeight)}
                          y2={toSvgY(scaleForm.pointB, floorPlanHeight)}
                        />
                      ) : null}
                      {scaleForm.pointA ? (
                        <circle
                          className="map-point map-point--scale"
                          cx={toSvgX(scaleForm.pointA, floorPlanWidth)}
                          cy={toSvgY(scaleForm.pointA, floorPlanHeight)}
                          r="11"
                        />
                      ) : null}
                      {scaleForm.pointB ? (
                        <circle
                          className="map-point map-point--scale"
                          cx={toSvgX(scaleForm.pointB, floorPlanWidth)}
                          cy={toSvgY(scaleForm.pointB, floorPlanHeight)}
                          r="11"
                        />
                      ) : null}
                    </svg>
                  </>
                ) : (
                  <div className="map-placeholder">
                    <p className="eyebrow">Floor Plan Pending</p>
                    <h3>
                      Upload a PNG or JPG to unlock calibration, zones, and
                      gateway placement.
                    </h3>
                    <p className="muted-text">
                      CAD and PDF parsing stay deferred until the raster-first
                      spatial foundation and registry workflows stabilize.
                    </p>
                  </div>
                )}
              </div>

              <div className="canvas-guidance">
                <span>
                  Click the rendered floor plan to place scale targets, polygon
                  vertices, or gateways.
                </span>
                <span>{getCanvasToolLabel(editorMode)}</span>
              </div>
            </article>
          </div>

          <div className="admin-workspace-grid admin-workspace-grid--triad">
            <article className="panel panel--compact stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Area Library</p>
                  <h2>Operational Areas</h2>
                </div>
                <span className="metric-chip">
                  {floorDetail?.areas.length ?? 0}
                </span>
              </div>

              <div className="toolbar-row">
                <button
                  className="tool-button"
                  onClick={() => beginNewArea("zone")}
                  type="button"
                >
                  New Zone
                </button>
                <button
                  className="tool-button"
                  onClick={() => beginNewArea("table")}
                  type="button"
                >
                  New Table
                </button>
                <button
                  className="tool-button"
                  onClick={() => beginNewArea("restricted_zone")}
                  type="button"
                >
                  New Restricted Zone
                </button>
                <button
                  className="tool-button"
                  onClick={() => beginNewArea("poi")}
                  type="button"
                >
                  New POI
                </button>
              </div>

              <div className="selection-list">
                {floorDetail?.areas.length ? null : (
                  <p className="empty-copy">
                    Define at least one zone, table, restricted zone, or point
                    of interest for this floor.
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
                      {area.alert_participation
                        ? "Alert participant"
                        : "Alert excluded"}
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
                  {AREA_TYPE_LABELS[areaDraft.areaType]} ·{" "}
                  {areaDraft.points.length} point(s)
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
                  <button
                    className="tool-button"
                    onClick={resetAreaDraft}
                    type="button"
                  >
                    Reset Draft
                  </button>
                </div>

                <div className="point-editor-list">
                  {areaDraft.points.length === 0 ? (
                    <p className="empty-copy">
                      Click the floor plan to add polygon points, or edit them
                      numerically here.
                    </p>
                  ) : null}
                  {areaDraft.points.map((point, index) => (
                    <div
                      className="point-editor-row"
                      key={`${point.x}-${point.y}-${index}`}
                    >
                      <strong>P{index + 1}</strong>
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.001"
                        value={point.x}
                        onChange={(event) =>
                          updateDraftPoint(index, "x", event.target.value)
                        }
                      />
                      <input
                        type="number"
                        min="0"
                        max="1"
                        step="0.001"
                        value={point.y}
                        onChange={(event) =>
                          updateDraftPoint(index, "y", event.target.value)
                        }
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

            <article className="panel panel--compact stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Step 06</p>
                  <h2>Gateway Placement</h2>
                </div>
                <span className="metric-chip">
                  {floorDetail?.gateways.length ?? 0} placed
                </span>
              </div>

              <div className="toolbar-row">
                <button
                  className="tool-button"
                  onClick={beginNewGateway}
                  type="button"
                >
                  New Gateway
                </button>
                <button
                  className={`tool-button${editorMode === "gateway" ? " tool-button--active" : ""}`}
                  disabled={!floorDetail?.floor_plan}
                  onClick={() => setEditorMode("gateway")}
                  type="button"
                >
                  Target Placement
                </button>
                <button
                  className="tool-button"
                  onClick={resetGatewayDraft}
                  type="button"
                >
                  Reset Draft
                </button>
              </div>

              <div className="selection-list">
                {floorDetail?.gateways.length ? null : (
                  <p className="empty-copy">
                    Place Economic or Premium gateways after the floor plan is
                    configured.
                  </p>
                )}
                {floorDetail?.gateways.map((gateway) => (
                  <button
                    key={gateway.id}
                    className={`selection-card${gateway.id === selectedGatewayId ? " selection-card--active" : ""}`}
                    onClick={() => selectExistingGateway(gateway)}
                    type="button"
                  >
                    <strong>{gateway.display_name}</strong>
                    <span>
                      {gateway.gateway_identifier} ·{" "}
                      {GATEWAY_TIER_LABELS[gateway.hardware_tier]}
                    </span>
                    <small>{formatPointLabel(gateway.placement)}</small>
                  </button>
                ))}
              </div>

              <div className="admin-form">
                <CommandInput
                  disabled={Boolean(gatewayDraft.id)}
                  error={errors.gatewayIdentifier}
                  label="Gateway Identifier"
                  placeholder="AA:BB:CC:DD:EE:FF"
                  value={gatewayDraft.gatewayIdentifier}
                  onBlur={() => {
                    const err = validateMacAddress(gatewayDraft.gatewayIdentifier);
                    setValidationError("gatewayIdentifier", err);
                  }}
                  onChange={(event) => {
                    const val = inputMasks.macAddress(event.target.value);
                    setGatewayDraft((current) => ({
                      ...current,
                      gatewayIdentifier: val
                    }));
                    if (errors.gatewayIdentifier) clearError("gatewayIdentifier");
                  }}
                />

                <CommandInput
                  label="Display Name"
                  placeholder="Dining Gateway"
                  value={gatewayDraft.displayName}
                  onChange={(event) =>
                    setGatewayDraft((current) => ({
                      ...current,
                      displayName: event.target.value
                    }))
                  }
                />

                <label>
                  <span>Hardware Tier</span>
                  <select
                    value={gatewayDraft.hardwareTier}
                    onChange={(event) =>
                      setGatewayDraft((current) => ({
                        ...current,
                        hardwareTier: event.target.value as GatewayHardwareTier
                      }))
                    }
                  >
                    {Object.entries(GATEWAY_TIER_LABELS).map(
                      ([value, label]) => (
                        <option key={value} value={value}>
                          {label}
                        </option>
                      )
                    )}
                  </select>
                </label>

                <div className="coordinate-grid">                  <label>
                    <span>Placement X</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.001"
                      value={gatewayDraft.placement?.x ?? 0}
                      onChange={(event) =>
                        updateGatewayPlacement("x", event.target.value)
                      }
                    />
                  </label>
                  <label>
                    <span>Placement Y</span>
                    <input
                      type="number"
                      min="0"
                      max="1"
                      step="0.001"
                      value={gatewayDraft.placement?.y ?? 0}
                      onChange={(event) =>
                        updateGatewayPlacement("y", event.target.value)
                      }
                    />
                  </label>
                </div>

                <label>
                  <span>Notes</span>
                  <textarea
                    placeholder="Mounted near the kitchen pass"
                    rows={3}
                    value={gatewayDraft.notes}
                    onChange={(event) =>
                      setGatewayDraft((current) => ({
                        ...current,
                        notes: event.target.value
                      }))
                    }
                  />
                </label>

                <div className="status-grid">
                  <div>
                    <span className="summary-label">Placement</span>
                    <strong>{formatPointLabel(gatewayDraft.placement)}</strong>
                  </div>
                  <div>
                    <span className="summary-label">Tier Profile</span>
                    <strong>
                      {GATEWAY_TIER_LABELS[gatewayDraft.hardwareTier]}
                    </strong>
                  </div>
                </div>

                <div className="toolbar-row">
                  <button
                    className="primary-button"
                    disabled={
                      isBusy ||
                      !gatewayDraft.gatewayIdentifier.trim() ||
                      !gatewayDraft.displayName.trim()
                    }
                    onClick={() => void handleSaveGateway()}
                    type="button"
                  >
                    {gatewayDraft.id ? "Update Gateway" : "Create Gateway"}
                  </button>
                  <button
                    className="secondary-button"
                    disabled={!gatewayDraft.id || isBusy}
                    onClick={() => void handleDeleteGateway()}
                    type="button"
                  >
                    Delete Gateway
                  </button>
                </div>
              </div>
            </article>
          </div>

          <div className="asset-registry-grid">
            <article className="panel panel--compact stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Step 07</p>
                  <h2>Asset Registry</h2>
                </div>
                <span className="metric-chip">
                  {assetTags.length} asset tags
                </span>
              </div>

              <div className="toolbar-row">
                <button
                  className="tool-button"
                  onClick={beginNewAsset}
                  type="button"
                >
                  New Asset Tag
                </button>
                <button
                  className="tool-button"
                  onClick={resetAssetDraft}
                  type="button"
                >
                  Reset Form
                </button>
              </div>

              <div className="selection-list asset-selection-list">
                {assetTags.length ? null : (
                  <p className="empty-copy">
                    Add asset tags manually or import them from CSV before
                    telemetry onboarding begins.
                  </p>
                )}
                {assetTags.map((asset) => (
                  <button
                    key={asset.id}
                    className={`selection-card${asset.id === selectedAssetId ? " selection-card--active" : ""}`}
                    onClick={() => selectExistingAsset(asset)}
                    type="button"
                  >
                    <strong>{asset.display_name}</strong>
                    <span>{asset.tag_identifier}</span>
                    <small>
                      {asset.asset_category} ·{" "}
                      {UPDATE_RATE_LABELS[asset.update_rate_profile]} ·{" "}
                      {BATTERY_PROFILE_LABELS[asset.battery_profile]}
                    </small>
                  </button>
                ))}
              </div>
            </article>

            <article className="panel panel--compact stack-card">
              <div className="stack-card__header">
                <div>
                  <p className="eyebrow">Registry Editor</p>
                  <h2>
                    {assetDraft.id ? "Edit Asset Tag" : "Create Asset Tag"}
                  </h2>
                </div>
                <span className="metric-chip">
                  {assetDraft.id ? "Manual update" : "Manual entry"}
                </span>
              </div>

              <div className="admin-form">
                <CommandInput
                  disabled={Boolean(assetDraft.id)}
                  error={errors.tagIdentifier}
                  label="Tag Identifier"
                  placeholder="waiter-tag-01"
                  value={assetDraft.tagIdentifier}
                  onBlur={() => {
                    const err = validateTagId(assetDraft.tagIdentifier);
                    setValidationError("tagIdentifier", err);
                  }}
                  onChange={(event) => {
                    const val = event.target.value;
                    setAssetDraft((current) => ({
                      ...current,
                      tagIdentifier: val
                    }));
                    if (errors.tagIdentifier) clearError("tagIdentifier");
                  }}
                />
                <CommandInput
                  label="Display Name"
                  placeholder="Waiter Tag 01"
                  value={assetDraft.displayName}
                  onChange={(event) =>
                    setAssetDraft((current) => ({
                      ...current,
                      displayName: event.target.value
                    }))
                  }
                />
                <CommandInput
                  label="Asset Category"
                  placeholder="staff"
                  value={assetDraft.assetCategory}
                  onChange={(event) =>
                    setAssetDraft((current) => ({
                      ...current,
                      assetCategory: event.target.value
                    }))
                  }
                />

                <div className="coordinate-grid">                  <label>
                    <span>Update Rate Profile</span>
                    <select
                      value={assetDraft.updateRateProfile}
                      onChange={(event) =>
                        setAssetDraft((current) => ({
                          ...current,
                          updateRateProfile: event.target
                            .value as AssetUpdateRateProfile
                        }))
                      }
                    >
                      {Object.entries(UPDATE_RATE_LABELS).map(
                        ([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        )
                      )}
                    </select>
                  </label>
                  <label>
                    <span>Battery Profile</span>
                    <select
                      value={assetDraft.batteryProfile}
                      onChange={(event) =>
                        setAssetDraft((current) => ({
                          ...current,
                          batteryProfile: event.target
                            .value as AssetBatteryProfile
                        }))
                      }
                    >
                      {Object.entries(BATTERY_PROFILE_LABELS).map(
                        ([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        )
                      )}
                    </select>
                  </label>
                </div>

                <div className="toolbar-row">
                  <button
                    className="primary-button"
                    disabled={
                      isBusy ||
                      !assetDraft.tagIdentifier.trim() ||
                      !assetDraft.displayName.trim()
                    }
                    onClick={() => void handleSaveAsset()}
                    type="button"
                  >
                    {assetDraft.id ? "Update Asset Tag" : "Create Asset Tag"}
                  </button>
                  <button
                    className="secondary-button"
                    disabled={!assetDraft.id || isBusy}
                    onClick={() => void handleDeleteAsset()}
                    type="button"
                  >
                    Delete Asset Tag
                  </button>
                </div>
              </div>
            </article>
          </div>

          <article className="panel panel--compact stack-card">
            <div className="stack-card__header">
              <div>
                <p className="eyebrow">Step 08</p>
                <h2>CSV Import Review</h2>
              </div>
              <span className="metric-chip">Validate before commit</span>
            </div>

            <div className="asset-import-grid">
              <form className="admin-form" onSubmit={handleValidateAssetImport}>
                <label className="file-input">
                  <span>Asset Registry CSV</span>
                  <input
                    key={assetImportInputKey}
                    accept=".csv,text/csv"
                    onChange={(event: ChangeEvent<HTMLInputElement>) =>
                      setAssetImportFile(event.target.files?.[0] ?? null)
                    }
                    type="file"
                  />
                </label>
                <div className="import-column-list">
                  {ASSET_IMPORT_COLUMNS.map((column) => (
                    <span
                      key={column}
                      className="metric-chip metric-chip--subtle"
                    >
                      {column}
                    </span>
                  ))}
                </div>
                <p className="muted-text">
                  Bulk import supports only UTF-8 CSV files with the required
                  columns shown above. Invalid rows block confirmation and are
                  returned with inline errors instead of partial inserts.
                </p>
                <div className="toolbar-row">
                  <button
                    className="primary-button"
                    disabled={isBusy || !assetImportFile}
                    type="submit"
                  >
                    Validate CSV
                  </button>
                  <button
                    className="secondary-button"
                    disabled={isBusy || !assetImportValidation?.import_id}
                    onClick={() => void handleConfirmAssetImport()}
                    type="button"
                  >
                    Confirm Import
                  </button>
                </div>
              </form>

              <div className="stack-card import-review-column">
                <div className="status-grid">
                  <div>
                    <span className="summary-label">Rows</span>
                    <strong>{assetImportValidation?.total_rows ?? 0}</strong>
                  </div>
                  <div>
                    <span className="summary-label">Valid</span>
                    <strong>
                      {assetImportValidation?.valid_row_count ?? 0}
                    </strong>
                  </div>
                  <div>
                    <span className="summary-label">Invalid</span>
                    <strong>
                      {assetImportValidation?.invalid_row_count ?? 0}
                    </strong>
                  </div>
                </div>

                {!assetImportValidation ? (
                  <p className="empty-copy">
                    Validate a CSV file to preview accepted asset tags and
                    review row-level errors before commit.
                  </p>
                ) : (
                  <>
                    <div className="import-review-list">
                      {assetImportValidation.valid_rows.length > 0 ? (
                        <>
                          <h3 className="import-section-title">Valid Rows</h3>
                          {assetImportValidation.valid_rows.map((row) => (
                            <div
                              className="import-review-card"
                              key={row.tag_identifier}
                            >
                              <strong>{row.display_name}</strong>
                              <span>{row.tag_identifier}</span>
                              <small>
                                {row.asset_category} ·{" "}
                                {UPDATE_RATE_LABELS[row.update_rate_profile]} ·{" "}
                                {BATTERY_PROFILE_LABELS[row.battery_profile]}
                              </small>
                            </div>
                          ))}
                        </>
                      ) : null}

                      {assetImportValidation.invalid_rows.length > 0 ? (
                        <>
                          <h3 className="import-section-title">Invalid Rows</h3>
                          {assetImportValidation.invalid_rows.map((row) => (
                            <div
                              className="import-validation-card"
                              key={row.row_number}
                            >
                              <strong>Row {row.row_number}</strong>
                              <span>
                                {row.values.tag_identifier ||
                                  "Missing tag_identifier"}{" "}
                                ·{" "}
                                {row.values.display_name ||
                                  "Missing display_name"}
                              </span>
                              <small>{row.errors.join(" · ")}</small>
                            </div>
                          ))}
                        </>
                      ) : null}
                    </div>
                    {assetImportValidation.import_id ? (
                      <p className="muted-text">
                        Validation is clean. Confirm import to create the staged
                        asset tags in the registry.
                      </p>
                    ) : (
                      <p className="muted-text">
                        Resolve invalid rows and validate again. Confirmation
                        stays disabled until every row is valid.
                      </p>
                    )}
                  </>
                )}
              </div>
            </div>
          </article>
        </div>
      </div>

      {isBusy ? <p className="muted-text">Saving changes...</p> : null}
    </section>
  );
}
