import type { LeakageCategory } from "./types";

export function fmtKes(value: number): string {
  if (Math.abs(value) >= 1e9) return `KES ${(value / 1e9).toFixed(2)}B`;
  if (Math.abs(value) >= 1e6) return `KES ${(value / 1e6).toFixed(1)}M`;
  if (Math.abs(value) >= 1e3) return `KES ${(value / 1e3).toFixed(1)}K`;
  return `KES ${value.toFixed(0)}`;
}

export function fmtPct(value: number, digits = 1): string {
  return `${value.toFixed(digits)}%`;
}

export function fmtCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-KE").format(value);
}

export const CATEGORY_LABELS: Record<LeakageCategory, string> = {
  dispatch_capture_gap_kes: "Dispatch capture gap",
  shrinkage_kes: "Shrinkage",
  billing_gap_kes: "Billing gap",
  underbilling_kes: "Underbilling",
  collections_gap_kes: "Collections gap",
};

export const CATEGORY_SHORT_LABELS: Record<string, string> = {
  dispatch_capture_gap: "Dispatch capture gap",
  shrinkage: "Shrinkage",
  billing_gap: "Billing gap",
  underbilling: "Underbilling",
  collections_gap: "Collections gap",
  none: "None",
};

// CSS custom-property references -- resolved at paint time so charts
// automatically follow the active light/dark theme without re-render.
export const CATEGORY_COLOR_VARS: Record<LeakageCategory, string> = {
  dispatch_capture_gap_kes: "var(--series-1)",
  shrinkage_kes: "var(--series-2)",
  billing_gap_kes: "var(--series-3)",
  underbilling_kes: "var(--series-4)",
  collections_gap_kes: "var(--series-5)",
};
