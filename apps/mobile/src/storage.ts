import AsyncStorage from "@react-native-async-storage/async-storage";

import type { RecentSearchEntry } from "./assetFinder";

export const RECENT_SEARCHES_KEY = "rtls-mobile-recent-searches";

export async function loadRecentSearches() {
  const payload = await AsyncStorage.getItem(RECENT_SEARCHES_KEY);
  if (!payload) {
    return [] as RecentSearchEntry[];
  }

  try {
    return JSON.parse(payload) as RecentSearchEntry[];
  } catch {
    return [] as RecentSearchEntry[];
  }
}

export async function saveRecentSearches(entries: RecentSearchEntry[]) {
  await AsyncStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(entries));
}
