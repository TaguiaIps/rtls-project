export type KalmanState = {
  x: number;
  y: number;
  vx: number;
  vy: number;
  px: number;
  py: number;
  pxy: number;
  pyx: number;
};

const DEFAULT_PROCESS_NOISE = 0.001;
const DEFAULT_MEASUREMENT_NOISE = 0.01;

export function createKalmanFilter(options?: {
  processNoise?: number;
  measurementNoise?: number;
}) {
  const q = options?.processNoise ?? DEFAULT_PROCESS_NOISE;
  const r = options?.measurementNoise ?? DEFAULT_MEASUREMENT_NOISE;

  let state: KalmanState | null = null;

  function init(measurement: { x: number; y: number }) {
    state = {
      x: measurement.x,
      y: measurement.y,
      vx: 0,
      vy: 0,
      px: 1,
      py: 1,
      pxy: 0,
      pyx: 0
    };
    return { x: state.x, y: state.y };
  }

  function update(measurement: { x: number; y: number }): { x: number; y: number } {
    if (!state) {
      return init(measurement);
    }

    // Predict
    state.px += q;
    state.py += q;

    // Kalman gain
    const sxx = state.px + r;
    const syy = state.py + r;
    const sxy = state.pxy;
    const sdet = sxx * syy - sxy * sxy;

    if (Math.abs(sdet) < 1e-12) {
      return { x: state.x, y: state.y };
    }

    const kxx = (state.px * syy - state.pxy * sxy) / sdet;
    const kxy = (state.pxy * syy - state.py * sxy) / sdet;
    const kyx = (sxx * state.pxy - sxy * state.px) / sdet;
    const kyy = (sxx * state.py - sxy * state.pxy) / sdet;

    // Update
    const innovationX = measurement.x - state.x;
    const innovationY = measurement.y - state.y;

    state.x += kxx * innovationX + kxy * innovationY;
    state.y += kyx * innovationX + kyy * innovationY;

    state.px = (1 - kxx) * state.px - kxy * state.pxy;
    state.py = (1 - kyy) * state.py - kyx * state.pxy;
    state.pxy = -kyx * state.px + (1 - kyy) * state.pxy;
    state.pyx = state.pxy;

    return { x: state.x, y: state.y };
  }

  function reset() {
    state = null;
  }

  return { init, update, reset };
}

export function applyMinimumMovementThreshold(
  current: { x: number; y: number },
  previous: { x: number; y: number } | null,
  threshold: number = 0.005
): { x: number; y: number } {
  if (!previous) {
    return current;
  }

  const distance = Math.hypot(current.x - previous.x, current.y - previous.y);
  if (distance < threshold) {
    return previous;
  }

  return current;
}
