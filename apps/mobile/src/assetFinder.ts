import type { AssetLocationRecord } from "@rtls/contracts";

export type RecentSearchEntry = {
  asset: AssetLocationRecord;
  savedAt: string;
};

const MAX_RECENT_SEARCHES = 5;

export function upsertRecentSearch(
  entries: RecentSearchEntry[],
  asset: AssetLocationRecord,
  savedAt: string
) {
  const nextEntries = entries.filter(
    (entry) => entry.asset.asset_tag_id !== asset.asset_tag_id
  );
  nextEntries.unshift({ asset, savedAt });
  return nextEntries.slice(0, MAX_RECENT_SEARCHES);
}

export function formatLastSeen(isoString: string, now: Date = new Date()) {
  const observedAt = new Date(isoString);
  const diffMs = Math.max(0, now.getTime() - observedAt.getTime());
  const diffSeconds = Math.round(diffMs / 1000);

  if (diffSeconds < 60) {
    return `${diffSeconds}s ago`;
  }

  const diffMinutes = Math.round(diffSeconds / 60);
  if (diffMinutes < 60) {
    return `${diffMinutes}m ago`;
  }

  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) {
    return `${diffHours}h ago`;
  }

  const diffDays = Math.round(diffHours / 24);
  return `${diffDays}d ago`;
}

export function formatLocationContext(asset: AssetLocationRecord) {
  if (asset.zone_name) {
    return `${asset.floor_name} · ${asset.zone_name}`;
  }

  return `${asset.floor_name} · ${asset.site_name}`;
}

export function formatPrecisionContext(asset: AssetLocationRecord) {
  if (asset.precision_meters !== null && asset.precision_meters !== undefined) {
    return `${asset.source_modality} · ±${asset.precision_meters.toFixed(1)}m`;
  }

  return `${asset.source_modality} · ${asset.confidence_level} confidence`;
}
