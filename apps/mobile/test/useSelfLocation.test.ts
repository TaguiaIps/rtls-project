import { describe, expect, it, vi, beforeEach, afterEach } from "vitest";

describe("useSelfLocation hook", () => {
  const originalWebSocket = globalThis.WebSocket;

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    globalThis.WebSocket = originalWebSocket;
  });

  it("constructs WebSocket URL with access_token and asset_tag_id", () => {
    const connectSpy = vi.fn();
    globalThis.WebSocket = vi.fn().mockImplementation((url: string) => {
      connectSpy(url);
      return {
        onopen: null,
        onmessage: null,
        onclose: null,
        onerror: null,
        close: vi.fn()
      };
    }) as unknown as typeof WebSocket;

    const { useSelfLocation } = require("../src/useSelfLocation");

    const React = require("react");
    const renderHook = () => {
      const result: Array<unknown> = [];
      const setState = (v: unknown) => {
        result[0] = v;
      };
      const refs = {
        current: null as unknown
      };
      useRef.mockReturnValue(refs);
      useState.mockImplementation((initial: unknown) => [initial, setState]);
      useEffect.mockImplementation((fn: () => (() => void) | void) => {
        const cleanup = fn();
        return cleanup ?? vi.fn();
      });
      useCallback.mockImplementation((fn: () => void) => fn);
    };

    useSelfLocation({
      apiBaseUrl: "http://localhost:8000",
      accessToken: "test-token-123",
      enabled: true,
      assetTagId: "TAG-001",
      onLocationUpdate: vi.fn()
    });

    expect(connectSpy).toHaveBeenCalledTimes(1);
    const url = connectSpy.mock.calls[0][0] as string;
    expect(url).toContain("ws://localhost:8000/ws/locations");
    expect(url).toContain("access_token=test-token-123");
    expect(url).toContain("asset_tag_id=TAG-001");
  });

  it("parses location.updated events and invokes callback", () => {
    let messageHandler: ((event: { data: string }) => void) | null = null;

    globalThis.WebSocket = vi.fn().mockImplementation(() => ({
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      close: vi.fn()
    })) as unknown as typeof WebSocket;

    const { useSelfLocation } = require("../src/useSelfLocation");
    const onLocationUpdate = vi.fn();

    useSelfLocation({
      apiBaseUrl: "http://localhost:8000",
      accessToken: "test-token",
      enabled: true,
      assetTagId: "TAG-001",
      floorId: "floor-1",
      onLocationUpdate
    });

    const wsInstance = (globalThis.WebSocket as ReturnType<typeof vi.fn>).mock.results[0].value;
    if (wsInstance.onmessage) {
      wsInstance.onmessage({
        data: JSON.stringify({
          event: "location.updated",
          location: {
            asset_tag_id: "TAG-001",
            tag_identifier: "TAG-001",
            display_name: "Test",
            asset_category: "Tray Cart",
            floor_id: "floor-1",
            floor_name: "Dining",
            site_id: "site-1",
            site_name: "HQ",
            observed_at: "2026-06-09T12:00:00Z",
            location_type: "point",
            point: { x: 0.45, y: 0.65 },
            zone_id: null,
            zone_name: null,
            confidence_level: "high",
            confidence_score: 0.85,
            source_tier: "Premium",
            source_modality: "UWB",
            precision_meters: 0.8,
            source_gateway_count: 3,
            source_reading_count: 3
          }
        })
      });
    }

    expect(onLocationUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        x: 0.45,
        y: 0.65,
        confidenceLevel: "high",
        precisionMeters: 0.8
      })
    );
  });

  it("ignores events from other floors when floorId is set", () => {
    let messageHandler: ((event: { data: string }) => void) | null = null;

    globalThis.WebSocket = vi.fn().mockImplementation(() => ({
      onopen: null,
      onmessage: null,
      onclose: null,
      onerror: null,
      close: vi.fn()
    })) as unknown as typeof WebSocket;

    const { useSelfLocation } = require("../src/useSelfLocation");
    const onLocationUpdate = vi.fn();

    useSelfLocation({
      apiBaseUrl: "http://localhost:8000",
      accessToken: "test-token",
      enabled: true,
      assetTagId: "TAG-001",
      floorId: "floor-1",
      onLocationUpdate
    });

    const wsInstance = (globalThis.WebSocket as ReturnType<typeof vi.fn>).mock.results[0].value;
    if (wsInstance.onmessage) {
      wsInstance.onmessage({
        data: JSON.stringify({
          event: "location.updated",
          location: {
            asset_tag_id: "TAG-001",
            tag_identifier: "TAG-001",
            display_name: "Test",
            asset_category: "Tray Cart",
            floor_id: "floor-other",
            floor_name: "Other",
            site_id: "site-1",
            site_name: "HQ",
            observed_at: "2026-06-09T12:00:00Z",
            location_type: "point",
            point: { x: 0.3, y: 0.7 },
            zone_id: null,
            zone_name: null,
            confidence_level: "high",
            confidence_score: 0.9,
            source_tier: "Premium",
            source_modality: "UWB",
            precision_meters: 0.5,
            source_gateway_count: 3,
            source_reading_count: 3
          }
        })
      });
    }

    expect(onLocationUpdate).not.toHaveBeenCalled();
  });
});

// Mock React hooks for the hook tests
vi.mock("react", () => ({
  useState: vi.fn((initial: unknown) => [initial, vi.fn()]),
  useEffect: vi.fn((fn: () => (() => void) | void) => {
    const cleanup = fn();
    return cleanup ?? vi.fn();
  }),
  useCallback: vi.fn((fn: () => void) => fn),
  useRef: vi.fn(() => ({ current: null }))
}));
