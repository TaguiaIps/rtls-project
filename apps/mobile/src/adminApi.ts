import type { AssetTagRecord, FloorDetail, SiteRecord } from "@rtls/contracts";

import { normalizeApiBaseUrl } from "./session";

export type AdminContextPayload = {
  sites: SiteRecord[];
  assets: AssetTagRecord[];
};

export function buildSitesUrl(apiBaseUrl: string) {
  return new URL("/api/admin/sites", `${normalizeApiBaseUrl(apiBaseUrl)}/`).toString();
}

export function buildAssetsUrl(apiBaseUrl: string) {
  return new URL("/api/admin/assets", `${normalizeApiBaseUrl(apiBaseUrl)}/`).toString();
}

export function buildFloorDetailUrl(apiBaseUrl: string, floorId: string) {
  return new URL(
    `/api/admin/floors/${floorId}`,
    `${normalizeApiBaseUrl(apiBaseUrl)}/`
  ).toString();
}

export function buildFloorPlanFileUrl(apiBaseUrl: string, fileDownloadPath: string) {
  return new URL(fileDownloadPath, `${normalizeApiBaseUrl(apiBaseUrl)}/`).toString();
}

export async function fetchAdminContext(
  apiBaseUrl: string,
  accessToken: string
): Promise<AdminContextPayload> {
  const [sites, assets] = await Promise.all([
    fetchAuthorizedJson<SiteRecord[]>(
      buildSitesUrl(apiBaseUrl),
      accessToken,
      "The mobile session token is not authorized for commissioning context."
    ),
    fetchAuthorizedJson<AssetTagRecord[]>(
      buildAssetsUrl(apiBaseUrl),
      accessToken,
      "The mobile session token is not authorized for asset registry access."
    )
  ]);

  return { sites, assets };
}

export async function fetchFloorDetail(
  apiBaseUrl: string,
  accessToken: string,
  floorId: string
) {
  return fetchAuthorizedJson<FloorDetail>(
    buildFloorDetailUrl(apiBaseUrl, floorId),
    accessToken,
    "The mobile session token is not authorized for floor detail access."
  );
}

async function fetchAuthorizedJson<T>(
  url: string,
  accessToken: string,
  unauthorizedMessage: string
): Promise<T> {
  const response = await fetch(url, {
    headers: {
      Authorization: `Bearer ${accessToken.trim()}`
    }
  });

  if (!response.ok) {
    throw new Error(
      response.status === 401 || response.status === 403
        ? unauthorizedMessage
        : `Request failed for ${url}.`
    );
  }

  return (await response.json()) as T;
}
