import { useEffect, useState } from "react";
import {
  ActivityIndicator,
  Linking,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View
} from "react-native";
import type { AssetLocationRecord } from "@rtls/contracts";

import {
  formatLastSeen,
  formatLocationContext,
  formatPrecisionContext,
  type RecentSearchEntry,
  upsertRecentSearch
} from "./assetFinder";
import { buildLiveMapHandoffUrl } from "./handoff";
import { buildSearchUrl, normalizeApiBaseUrl } from "./session";
import { loadRecentSearches, saveRecentSearches } from "./storage";

type AssetFinderScreenProps = {
  apiBaseUrl: string;
  webBaseUrl: string;
  accessToken: string;
};

export function AssetFinderScreen({
  apiBaseUrl,
  webBaseUrl,
  accessToken
}: AssetFinderScreenProps) {
  const [query, setQuery] = useState("");
  const [lastCompletedQuery, setLastCompletedQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<AssetLocationRecord[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<AssetLocationRecord | null>(null);
  const [recentSearches, setRecentSearches] = useState<RecentSearchEntry[]>([]);

  useEffect(() => {
    let cancelled = false;

    void loadRecentSearches().then((entries) => {
      if (!cancelled) {
        setRecentSearches(entries);
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    void saveRecentSearches(recentSearches);
  }, [recentSearches]);

  const normalizedApiBaseUrl = normalizeApiBaseUrl(apiBaseUrl);
  const canSearch = Boolean(normalizedApiBaseUrl && accessToken.trim() && query.trim());

  const handleSearch = async () => {
    if (!canSearch) {
      return;
    }

    setSearching(true);
    setError(null);
    try {
      const submittedQuery = query.trim();
      const response = await fetch(buildSearchUrl(normalizedApiBaseUrl, query), {
        headers: {
          Authorization: `Bearer ${accessToken.trim()}`
        }
      });

      if (!response.ok) {
        throw new Error(
          response.status === 401 || response.status === 403
            ? "The mobile session token is not authorized for search."
            : "Asset search failed."
        );
      }

      const payload = (await response.json()) as AssetLocationRecord[];
      setLastCompletedQuery(submittedQuery);
      setResults(payload);
      if (!payload.length) {
        setSelectedAsset(null);
      }
    } catch (searchError) {
      setLastCompletedQuery("");
      setResults([]);
      setSelectedAsset(null);
      setError(
        searchError instanceof Error
          ? searchError.message
          : "Asset search failed. Check the session and API target."
      );
    } finally {
      setSearching(false);
    }
  };

  const handleSelectAsset = (asset: AssetLocationRecord) => {
    setSelectedAsset(asset);
    setRecentSearches((current) =>
      upsertRecentSearch(current, asset, new Date().toISOString())
    );
  };

  const handleOpenInMap = async () => {
    if (!selectedAsset) {
      return;
    }

    try {
      const handoffUrl = buildLiveMapHandoffUrl(webBaseUrl, selectedAsset);
      await Linking.openURL(handoffUrl);
    } catch {
      setError("Live Map handoff failed. Check the configured web base URL.");
    }
  };

  const showNoResults =
    !error &&
    !searching &&
    query.trim().length > 0 &&
    lastCompletedQuery === query.trim() &&
    results.length === 0;

  return (
    <>
      <View style={styles.heroCard}>
        <Text style={styles.eyebrow}>Mobile Asset Finder</Text>
        <Text style={styles.title}>Find the nearest live location fast.</Text>
        <Text style={styles.body}>
          Search by asset name or tag, reopen recent results, and hand off into the delivered
          web Live Map when you need full floor context.
        </Text>
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Search</Text>
        <View style={styles.searchRow}>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            onChangeText={setQuery}
            onSubmitEditing={() => void handleSearch()}
            placeholder="Search asset name or tag"
            placeholderTextColor="#64748b"
            style={[styles.input, styles.searchInput]}
            value={query}
          />
          <Pressable
            disabled={!canSearch || searching}
            onPress={() => void handleSearch()}
            style={({ pressed }) => [
              styles.primaryButton,
              (!canSearch || searching) && styles.primaryButtonDisabled,
              pressed && canSearch && !searching ? styles.primaryButtonPressed : null
            ]}
          >
            {searching ? (
              <ActivityIndicator color="#f8fafc" />
            ) : (
              <Text style={styles.primaryButtonLabel}>Search</Text>
            )}
          </Pressable>
        </View>
        {error ? <Text style={styles.errorText}>{error}</Text> : null}
        {!error && searching ? (
          <Text style={styles.helperText}>Querying live locations...</Text>
        ) : null}
        {showNoResults ? (
          <Text style={styles.helperText}>
            No matching tracked assets were found for the current search.
          </Text>
        ) : null}

        <View style={styles.resultsList}>
          {results.map((asset) => (
            <Pressable
              key={asset.asset_tag_id}
              onPress={() => handleSelectAsset(asset)}
              style={({ pressed }) => [
                styles.resultCard,
                selectedAsset?.asset_tag_id === asset.asset_tag_id && styles.resultCardSelected,
                pressed ? styles.resultCardPressed : null
              ]}
            >
              <View style={styles.resultHeader}>
                <Text style={styles.resultTitle}>{asset.display_name}</Text>
                <Text style={styles.badge}>{asset.source_tier}</Text>
              </View>
              <Text style={styles.resultMeta}>{asset.tag_identifier}</Text>
              <Text style={styles.resultMeta}>{formatLocationContext(asset)}</Text>
              <Text style={styles.resultMeta}>Last seen {formatLastSeen(asset.observed_at)}</Text>
            </Pressable>
          ))}
        </View>
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Recent Searches</Text>
        {!recentSearches.length ? (
          <Text style={styles.helperText}>No recent searches yet.</Text>
        ) : null}
        {recentSearches.map((entry) => (
          <Pressable
            key={entry.asset.asset_tag_id}
            onPress={() => handleSelectAsset(entry.asset)}
            style={({ pressed }) => [styles.recentCard, pressed ? styles.resultCardPressed : null]}
          >
            <View style={styles.resultHeader}>
              <Text style={styles.resultTitle}>{entry.asset.display_name}</Text>
              <Text style={styles.badge}>Recent</Text>
            </View>
            <Text style={styles.resultMeta}>{formatLocationContext(entry.asset)}</Text>
            <Text style={styles.resultMeta}>Opened {formatLastSeen(entry.savedAt)}</Text>
          </Pressable>
        ))}
      </View>

      <View style={styles.panel}>
        <Text style={styles.panelTitle}>Location Sheet</Text>
        {!selectedAsset ? (
          <Text style={styles.helperText}>
            Select an asset from results or recent searches to inspect its last-known location.
          </Text>
        ) : (
          <View style={styles.locationSheet}>
            <View style={styles.resultHeader}>
              <Text style={styles.sheetTitle}>{selectedAsset.display_name}</Text>
              <Text style={styles.badge}>{selectedAsset.asset_category}</Text>
            </View>
            <Text style={styles.sheetLine}>{selectedAsset.tag_identifier}</Text>
            <Text style={styles.sheetLine}>{formatLocationContext(selectedAsset)}</Text>
            <Text style={styles.sheetLine}>
              Last seen {formatLastSeen(selectedAsset.observed_at)}
            </Text>
            <Text style={styles.sheetLine}>{formatPrecisionContext(selectedAsset)}</Text>
            <Text style={styles.sheetLine}>
              {selectedAsset.location_type === "zone"
                ? "Zone fallback is active for this asset."
                : "Point location is currently available."}
            </Text>
            <Pressable
              onPress={() => void handleOpenInMap()}
              style={({ pressed }) => [
                styles.secondaryButton,
                pressed ? styles.secondaryButtonPressed : null
              ]}
            >
              <Text style={styles.secondaryButtonLabel}>Open in Live Map</Text>
            </Pressable>
          </View>
        )}
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  heroCard: {
    backgroundColor: "#0f172a",
    borderRadius: 24,
    paddingHorizontal: 20,
    paddingVertical: 22,
    borderWidth: 1,
    borderColor: "#163047"
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
    color: "#22d3ee",
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
  searchRow: {
    flexDirection: "row",
    gap: 10,
    alignItems: "center"
  },
  searchInput: {
    flex: 1
  },
  primaryButton: {
    backgroundColor: "#0ea5e9",
    borderRadius: 14,
    minHeight: 48,
    minWidth: 96,
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
    marginTop: 8,
    backgroundColor: "#0b2537",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#1d4f6c",
    paddingHorizontal: 16,
    paddingVertical: 14,
    alignItems: "center"
  },
  secondaryButtonPressed: {
    opacity: 0.92
  },
  secondaryButtonLabel: {
    color: "#bae6fd",
    fontSize: 15,
    fontWeight: "700"
  },
  errorText: {
    color: "#fca5a5",
    fontSize: 14
  },
  resultsList: {
    gap: 10
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
  resultCardSelected: {
    borderColor: "#22d3ee"
  },
  resultCardPressed: {
    opacity: 0.92
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
  recentCard: {
    backgroundColor: "#111c31",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#1f3450",
    paddingHorizontal: 14,
    paddingVertical: 12,
    gap: 4
  },
  badge: {
    color: "#67e8f9",
    backgroundColor: "#123045",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    overflow: "hidden",
    fontSize: 12,
    fontWeight: "700"
  },
  locationSheet: {
    gap: 8
  },
  sheetTitle: {
    color: "#f8fafc",
    fontSize: 22,
    fontWeight: "700",
    flex: 1
  },
  sheetLine: {
    color: "#cbd5e1",
    fontSize: 15,
    lineHeight: 22
  }
});
