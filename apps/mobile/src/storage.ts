import AsyncStorage from "@react-native-async-storage/async-storage";

import type { RecentSearchEntry } from "./assetFinder";
import type { CommissioningSessionSummary } from "./commissioning";

export const RECENT_SEARCHES_KEY = "rtls-mobile-recent-searches";
export const COMMISSIONING_SUMMARIES_KEY = "rtls-mobile-commissioning-summaries";

export async function loadRecentSearches() {
  return loadStoredArray<RecentSearchEntry>(RECENT_SEARCHES_KEY);
}

export async function saveRecentSearches(entries: RecentSearchEntry[]) {
  await AsyncStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(entries));
}

export async function loadCommissioningSummaries() {
  return loadStoredArray<CommissioningSessionSummary>(COMMISSIONING_SUMMARIES_KEY);
}

export async function saveCommissioningSummaries(entries: CommissioningSessionSummary[]) {
  await AsyncStorage.setItem(COMMISSIONING_SUMMARIES_KEY, JSON.stringify(entries));
}

async function loadStoredArray<T>(storageKey: string) {
  const payload = await AsyncStorage.getItem(storageKey);
  if (!payload) {
    return [] as T[];
  }

  try {
    return JSON.parse(payload) as T[];
  } catch {
    return [] as T[];
  }
}
