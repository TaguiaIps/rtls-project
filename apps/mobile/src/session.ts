export function normalizeApiBaseUrl(value: string) {
  const trimmed = value.trim();
  if (!trimmed) {
    return "";
  }
  return trimmed.endsWith("/") ? trimmed.slice(0, -1) : trimmed;
}

export function buildSearchUrl(apiBaseUrl: string, query: string) {
  const url = new URL("/api/locations/search", `${normalizeApiBaseUrl(apiBaseUrl)}/`);
  url.searchParams.set("query", query.trim());
  return url.toString();
}
