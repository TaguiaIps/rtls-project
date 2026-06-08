import "@testing-library/jest-dom/vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./auth";

const STORAGE_KEY = "rtls-auth-session";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

function Harness({ onReady }: { onReady: (auth: ReturnType<typeof useAuth>) => void }) {
  const auth = useAuth();
  onReady(auth);
  return <div>{auth.status}</div>;
}

describe("AuthProvider", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("reuses a single refresh request for concurrent 401 retries", async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: "expired-access",
        refreshToken: "refresh-1"
      })
    );

    const usedRefreshTokens = new Set<string>();
    let refreshCallCount = 0;
    let authApi: ReturnType<typeof useAuth> | null = null;

    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = typeof input === "string" ? input : input.toString();
      const headers = new Headers(init?.headers);
      const authorization = headers.get("Authorization");

      if (url.endsWith("/api/auth/refresh")) {
        refreshCallCount += 1;
        const body = JSON.parse(String(init?.body)) as { refresh_token: string };
        if (usedRefreshTokens.has(body.refresh_token)) {
          return new Response(null, { status: 401 });
        }
        usedRefreshTokens.add(body.refresh_token);

        if (body.refresh_token === "refresh-1") {
          return jsonResponse({
            access_token: "access-2",
            refresh_token: "refresh-2",
            expires_in_seconds: 600,
            role: "Administrator"
          });
        }

        if (body.refresh_token === "refresh-2") {
          return jsonResponse({
            access_token: "access-3",
            refresh_token: "refresh-3",
            expires_in_seconds: 600,
            role: "Administrator"
          });
        }

        return new Response(null, { status: 401 });
      }

      if (url.endsWith("/api/me")) {
        if (authorization === "Bearer expired-access") {
          return new Response(null, { status: 401 });
        }

        return jsonResponse({
          id: "user-1",
          email: "admin@example.com",
          display_name: "Admin",
          role: "Administrator",
          status: "active"
        });
      }

      if (url.endsWith("/protected/a") || url.endsWith("/protected/b")) {
        if (authorization === "Bearer access-2") {
          return new Response(null, { status: 401 });
        }
        if (authorization === "Bearer access-3") {
          return new Response(null, { status: 200 });
        }
      }

      throw new Error(`Unexpected fetch: ${url}`);
    });

    render(
      <AuthProvider>
        <Harness onReady={(nextAuth) => {
          authApi = nextAuth;
        }}
        />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText("authenticated")).toBeInTheDocument();
    });
    expect(authApi).not.toBeNull();
    expect(refreshCallCount).toBe(1);

    const [firstResponse, secondResponse] = await Promise.all([
      authApi!.fetchWithAuth("/protected/a"),
      authApi!.fetchWithAuth("/protected/b")
    ]);

    expect(firstResponse.status).toBe(200);
    expect(secondResponse.status).toBe(200);
    expect(refreshCallCount).toBe(2);
  });
});
