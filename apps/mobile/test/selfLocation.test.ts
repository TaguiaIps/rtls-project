import { describe, expect, it } from "vitest";
import {
  applyMinimumMovementThreshold,
  createKalmanFilter
} from "../src/kalmanFilter";

describe("Kalman filter", () => {
  it("initializes with the first measurement", () => {
    const filter = createKalmanFilter();
    const result = filter.init({ x: 0.5, y: 0.5 });
    expect(result).toEqual({ x: 0.5, y: 0.5 });
  });

  it("smooths noisy sequential measurements", () => {
    const filter = createKalmanFilter();
    const measurements = [
      { x: 0.5, y: 0.5 },
      { x: 0.52, y: 0.51 },
      { x: 0.49, y: 0.53 },
      { x: 0.51, y: 0.5 },
      { x: 0.5, y: 0.49 }
    ];

    const results = measurements.map((m) => filter.update(m));

    const first = results[0];
    const last = results[results.length - 1];

    const firstNoise = Math.abs(first.x - 0.5) + Math.abs(first.y - 0.5);
    const lastNoise = Math.abs(last.x - 0.5) + Math.abs(last.y - 0.49);

    expect(firstNoise).toBeLessThan(0.02);
    expect(lastNoise).toBeLessThan(0.02);
  });

  it("tracks a moving signal", () => {
    const filter = createKalmanFilter();
    const results: Array<{ x: number; y: number }> = [];

    for (let i = 0; i < 10; i++) {
      results.push(filter.update({ x: 0.1 + i * 0.05, y: 0.5 }));
    }

    const finalX = results[results.length - 1].x;
    expect(finalX).toBeGreaterThan(0.35);
    expect(finalX).toBeLessThan(0.65);
  });

  it("initializes automatically on first update without init call", () => {
    const filter = createKalmanFilter();
    const result = filter.update({ x: 0.3, y: 0.7 });
    expect(result).toEqual({ x: 0.3, y: 0.7 });
  });

  it("resets state cleanly", () => {
    const filter = createKalmanFilter();
    filter.update({ x: 0.5, y: 0.5 });
    filter.update({ x: 0.6, y: 0.6 });
    filter.reset();

    const result = filter.update({ x: 0.1, y: 0.1 });
    expect(result.x).toBeLessThan(0.2);
    expect(result.y).toBeLessThan(0.2);
  });
});

describe("applyMinimumMovementThreshold", () => {
  it("returns current when there is no previous", () => {
    const result = applyMinimumMovementThreshold({ x: 0.5, y: 0.5 }, null);
    expect(result).toEqual({ x: 0.5, y: 0.5 });
  });

  it("returns previous when movement is below threshold", () => {
    const result = applyMinimumMovementThreshold(
      { x: 0.501, y: 0.501 },
      { x: 0.5, y: 0.5 },
      0.01
    );
    expect(result).toEqual({ x: 0.5, y: 0.5 });
  });

  it("returns current when movement exceeds threshold", () => {
    const result = applyMinimumMovementThreshold(
      { x: 0.6, y: 0.5 },
      { x: 0.5, y: 0.5 },
      0.01
    );
    expect(result).toEqual({ x: 0.6, y: 0.5 });
  });

  it("uses default threshold of 0.005", () => {
    const below = applyMinimumMovementThreshold({ x: 0.501, y: 0.5 }, { x: 0.5, y: 0.5 });
    expect(below).toEqual({ x: 0.5, y: 0.5 });

    const above = applyMinimumMovementThreshold({ x: 0.52, y: 0.5 }, { x: 0.5, y: 0.5 });
    expect(above).toEqual({ x: 0.52, y: 0.5 });
  });
});
