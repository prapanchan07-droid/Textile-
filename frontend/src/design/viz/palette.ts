/** Categorical and status colours for charts that need more than the three theme series. */
export const CAT = ['#009dd8', '#e5533d', '#4aa564', '#f0a22e', '#7c6bd6', '#0b5fa5', '#14b8a6', '#c2578f', '#8a99a8', '#b07a2a', '#3f7fbf', '#6b8e23'];
export const catColor = (i: number) => CAT[((i % CAT.length) + CAT.length) % CAT.length];

export const CATEGORY_COLORS: Record<string, string> = {
  WARP: '#009dd8',
  WEFT: '#7c6bd6',
  MECHANICAL: '#e5533d',
  ELECTRICAL: '#f0a22e',
  BEAM: '#8a99a8',
  STYLE: '#a3adb8',
  WAITING: '#14b8a6',
  YARN: '#4aa564',
  PLANNED_MAINTENANCE: '#6b7a88',
  OTHER: '#b6bec8',
};

export const BAND = { HEALTHY: '#00898f', WATCH: '#da8b18', AT_RISK: '#e12330' } as const;

const lerp = (a: number, b: number, t: number) => Math.round(a + (b - a) * t);
const mix = (c1: [number, number, number], c2: [number, number, number], t: number) => `rgb(${lerp(c1[0], c2[0], t)}, ${lerp(c1[1], c2[1], t)}, ${lerp(c1[2], c2[2], t)})`;
const RED: [number, number, number] = [225, 35, 48];
const AMBER: [number, number, number] = [240, 190, 60];
const GREEN: [number, number, number] = [0, 150, 150];
const TEAL_LIGHT: [number, number, number] = [225, 244, 250];
const TEAL_DARK: [number, number, number] = [0, 120, 180];

/** Red (low) through amber to green (high): for "higher is better" values such as efficiency. */
export const goodHigh = (v: number, lo: number, hi: number) => {
  const t = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
  return t < 0.5 ? mix(RED, AMBER, t * 2) : mix(AMBER, GREEN, (t - 0.5) * 2);
};
/** Light to deep blue: for counts and rates where there is no good or bad direction. */
export const sequential = (v: number, max: number) => mix(TEAL_LIGHT, TEAL_DARK, Math.max(0, Math.min(1, max > 0 ? v / max : 0)));
/** Pale to amber to red: higher is worse (defects, stops). */
export const badHigh = (v: number, lo: number, hi: number) => {
  const t = Math.max(0, Math.min(1, (v - lo) / (hi - lo)));
  const pale: [number, number, number] = [236, 247, 245];
  return t < 0.5 ? mix(pale, AMBER, t * 2) : mix(AMBER, RED, (t - 0.5) * 2);
};
