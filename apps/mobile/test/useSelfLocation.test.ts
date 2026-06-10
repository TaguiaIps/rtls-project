import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { renderHook, act } from "@testing-library/react";

// Track created WebSocket instances for simulation
let wsInstances: Array<{
  onopen: ((ev: Event) => void) | null;
  onmessage: ((ev: { data: string }) => void) | null;
  onclose: ((ev: CloseEvent) => void) | null;
  onerror: ((ev: Event) => void) | null;
  close: Mock;
  simulateOpen: () => void;
  simulateMessage: (data: object) => void;
  simulateClose: () => void;
}> = [];

function createFakeWebSocket(url: string) {
  const instance = {
    onopen: null as ((ev: Event) => void) | null,
    onmessage: null as ((ev: { data: string }) => void) | null,
    onclose: null as ((ev: CloseEvent) => void) | null,
    onerror: null as ((ev: Event) => void) | null,
    close: vi.fn(),
    simulateOpen() {
      this.onopen?.(new Event("open"));
    },
    simulateMessage(data: object) {
      this.onmessage?.({ data: JSON.stringify(data) } as MessageEvent<string>);
    },
    simulateClose() {
      this.onclose?.(new CloseEvent("close"));
    }
  };
  wsInstances.push(instance);
  return instance;
}

describe("useSelfLocation hook", () => {
  const originalWebSocket = globalThis.WebSocket;
  const originalSetTimeout = globalThis.setTimeout;

  beforeEach(() => {
    vi.useFakeTimers();
    wsInstances = [];
    globalThis.WebSocket = vi.fn().mockImplementation(createFakeWebSocket) as unknown as typeof WebSocket;
  });

  afterEach(() => {
    vi.useRealTimers();
    globalThis.WebSocket = originalWebSocket;
    wsInstances = [];
  });

  function makeOptions(overrides: Record<string, unknown> = {}) {
    return {
      apiBaseUrl: "http://localhost:8000",
      accessToken: "test-token-123",
      enabled: true,
      assetTagId: "TAG-001",
      onLocationUpdate: vi.fn(),
      ...overrides
    };
  }

  it("constructs WebSocket URL with access_token and asset_tag_id", () => {
    renderHook(() => useSelfLocation(makeOptions()));

    expect(globalThis.WebSocket).toHaveBeenCalledTimes(1);
    const url = (globalThis.WebSocket as Mock).mock.calls[0][0] as string;
    expect(url).toContain("ws://localhost:8000/ws/locations");
    expect(url).toContain("access_token=test-token-123");
    expect(url).toContain("asset_tag_id=TAG-001");
  });

  it("transitions to connected on open", () => {
    const { result } = renderHook(() => useSelfLocation(makeOptions()));

    expect(result.current.connectionStatus).toBe("connecting");
    act(() => wsInstances[0].simulateOpen());
    expect(result.current.connectionStatus).toBe("connected");
  });

  it("parses location.updated events and invokes callback", () => {
    const onLocationUpdate = vi.fn();
    const { result } = renderHook(() => useSelfLocation(makeOptions({ onLocationUpdate })));

    act(() => wsInstances[0].simulateOpen());
    act(() =>
      wsInstances[0].simulateMessage({
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
    );

    expect(onLocationUpdate).toHaveBeenCalledWith(
      expect.objectContaining({
        x: 0.45,
        y: 0.65,
        confidenceLevel: "high",
        precisionMeters: 0.8
      })
    );
    expect(result.current.location).toEqual(
      expect.objectContaining({ x: 0.45, y: 0.65 })
    );
  });

  it("ignores events from other floors when floorId is set", () => {
    const onLocationUpdate = vi.fn();
    renderHook(() =>
      useSelfLocation(makeOptions({ floorId: "floor-1", onLocationUpdate }))
    );

    act(() => wsInstances[0].simulateOpen());
    act(() =>
      wsInstances[0].simulateMessage({
        event: "location.updated",
        location: {
          asset_tag_id: "TAG-001",
          floor_id: "floor-other",
          location_type: "point",
          point: { x: 0.3, y: 0.7 },
          confidence_level: "high",
          confidence_score: 0.9,
          observed_at: "2026-06-09T12:00:00Z",
          precision_meters: 0.5
        }
      })
    );

    expect(onLocationUpdate).not.toHaveBeenCalled();
  });

  it("does not connect when enabled is false", () => {
    renderHook(() => useSelfLocation(makeOptions({ enabled: false })));

    expect(globalThis.WebSocket).not.toHaveBeenCalled();
  });

  it("reconnects with exponential backoff on disconnect", () => {
    const { result } = renderHook(() => useSelfLocation(makeOptions()));

    act(() => wsInstances[0].simulateOpen());
    expect(result.current.connectionStatus).toBe("connected");

    act(() => wsInstances[0].simulateClose());
    expect(result.current.connectionStatus).toBe("reconnecting");

    // First reconnect: 1000ms base delay
    act(() => vi.advanceTimersByTime(1000));
    expect(globalThis.WebSocket).toHaveBeenCalledTimes(2);
    expect(wsInstances[1]).toBeDefined();

    act(() => wsInstances[1].simulateOpen());
    expect(result.current.connectionStatus).toBe("connected");

    // Second disconnect: 2000ms (2^1 * 1000)
    act(() => wsInstances[1].simulateClose());
    act(() => vi.advanceTimersByTime(2000));
    expect(globalThis.WebSocket).toHaveBeenCalledTimes(3);
  });

  it("stops reconnecting after max attempts", () => {
    const { result } = renderHook(() => useSelfLocation(makeOptions()));

    act(() => wsInstances[0].simulateOpen());

    // The hook uses attempt > MAX_RECONNECT_ATTEMPTS (10), so we need 11
    // disconnects for attempt to reach 11 and trigger "disconnected"
    for (let i = 0; i < 11; i++) {
      act(() => wsInstances[i].simulateClose());
      const delay = Math.min(1000 * Math.pow(2, i), 15000);
      act(() => vi.advanceTimersByTime(delay));
    }

    // After 11 attempts (exceeds MAX_RECONNECT_ATTEMPTS), status should be disconnected
    expect(result.current.connectionStatus).toBe("disconnected");

    // No more WebSocket connections should be created
    const totalCalls = (globalThis.WebSocket as Mock).mock.calls.length;
    act(() => vi.advanceTimersByTime(20000));
    expect((globalThis.WebSocket as Mock).mock.calls.length).toBe(totalCalls);
  });

  it("ignores malformed messages without crashing", () => {
    const onLocationUpdate = vi.fn();
    renderHook(() => useSelfLocation(makeOptions({ onLocationUpdate })));

    act(() => wsInstances[0].simulateOpen());

    // Send invalid JSON
    const ws = wsInstances[0];
    act(() => {
      ws.onmessage?.({ data: "not-json" } as MessageEvent<string>);
    });

    // Send valid JSON but wrong event type
    act(() => {
      ws.onmessage?.({ data: JSON.stringify({ event: "other.event" }) } as MessageEvent<string>);
    });

    // Send location without point
    act(() => {
      ws.onmessage?.({
        data: JSON.stringify({ event: "location.updated", location: { location_type: "zone" } })
      } as MessageEvent<string>);
    });

    expect(onLocationUpdate).not.toHaveBeenCalled();
  });

  it("cleans up WebSocket on unmount", () => {
    const { unmount } = renderHook(() => useSelfLocation(makeOptions()));

    act(() => wsInstances[0].simulateOpen());
    unmount();

    expect(wsInstances[0].close).toHaveBeenCalled();
  });

  it("resets state when disabled after being connected", () => {
    const { result, rerender } = renderHook(
      ({ enabled }) => useSelfLocation(makeOptions({ enabled })),
      { initialProps: { enabled: true } }
    );

    act(() => wsInstances[0].simulateOpen());
    expect(result.current.connectionStatus).toBe("connected");

    rerender({ enabled: false });
    expect(result.current.connectionStatus).toBe("disconnected");
    expect(result.current.location).toBeNull();
    expect(wsInstances[0].close).toHaveBeenCalled();
  });
});

// Import the hook after all mocks are set up
import { useSelfLocation } from "../src/useSelfLocation";
