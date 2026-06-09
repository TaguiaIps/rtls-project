import type { AssetLocationRecord } from "@rtls/contracts";

export function buildLiveMapHandoffUrl(
  webBaseUrl: string,
  asset: AssetLocationRecord
) {
  const url = new URL("/operations/live-map", normalizeBaseUrl(webBaseUrl));
  url.searchParams.set("site_id", asset.site_id);
  url.searchParams.set("floor_id", asset.floor_id);
  url.searchParams.set("asset_tag_id", asset.asset_tag_id);
  return url.toString();
}

function normalizeBaseUrl(baseUrl: string) {
  return baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
}
