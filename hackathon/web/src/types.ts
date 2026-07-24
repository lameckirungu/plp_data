export const LEAKAGE_CATEGORIES = [
  "dispatch_capture_gap_kes",
  "shrinkage_kes",
  "billing_gap_kes",
  "underbilling_kes",
  "collections_gap_kes",
] as const;

export type LeakageCategory = (typeof LEAKAGE_CATEGORIES)[number];

export interface ByGroupRow {
  [key: string]: string | number;
  loadings: number;
  expected_revenue_kes: number;
  collected_revenue_kes: number;
  total_leakage_kes: number;
  leakage_pct_of_expected: number;
}

export interface Kpis {
  total_loadings: number;
  total_expected_revenue_kes: number;
  total_collected_revenue_kes: number;
  total_leakage_kes: number;
  leakage_pct_of_expected_revenue: number;
  leakage_by_category_kes: Record<LeakageCategory, number>;
  exception_count: number;
  exception_rate_pct: number;
  simulation_window_days: number;
  avg_daily_leakage_kes: number;
  annualized_leakage_kes: number;
  by_depot: ByGroupRow[];
  by_product: ByGroupRow[];
  by_customer: ByGroupRow[];
}

export interface TrendPoint {
  day: string;
  total_leakage_kes: number;
}

export interface ExceptionRow {
  loading_id: string;
  depot: string;
  product: string;
  customer: string;
  leakage_category: string;
  total_leakage_kes: number;
  dispatch_capture_gap_kes: number;
  shrinkage_kes: number;
  billing_gap_kes: number;
  underbilling_kes: number;
  collections_gap_kes: number;
  loading_ts: string;
}

export interface ExceptionsResponse {
  total: number;
  offset: number;
  limit: number;
  rows: ExceptionRow[];
}

export interface RoiCategoryBreakdown {
  category: LeakageCategory;
  annualized_leakage_kes: number;
  recovery_rate: number;
  recoverable_kes: number;
  rationale: string;
}

export interface Roi {
  implementation_cost_kes: number;
  total_annualized_leakage_kes: number;
  steady_state_recoverable_annual_kes: number;
  year1_adoption_ramp_factor: number;
  year1_realized_benefit_kes: number;
  net_benefit_year1_kes: number;
  roi_multiple_year1: number;
  payback_period_months: number;
  category_breakdown: RoiCategoryBreakdown[];
  note: string;
}

export interface AlertNarrative {
  loading_id: string;
  depot: string;
  customer: string;
  leakage_category: string;
  total_leakage_kes: number;
  narrative: string;
}

export interface NarrativeResponse {
  executive_narrative: string;
  alert_narratives: AlertNarrative[];
}

export interface DqCheck {
  name: string;
  status: "PASS" | "FAIL";
  detail: string;
}

export interface DqIssue {
  table: string;
  check: string;
  severity: "critical" | "warning" | "exception";
  count: number;
  detail: string;
}

export interface DataQuality {
  overall_status: "PASS" | "FAIL" | "N/A";
  checks: DqCheck[];
  issues: DqIssue[];
}

export interface FilterOptions {
  depots: string[];
  products: string[];
  min_date: string;
  max_date: string;
}

export interface RunLog {
  run_at?: string;
  status?: "SUCCESS" | "FAILED" | "RUNNING";
  duration_seconds?: number;
  quality_gate_status?: string;
  total_leakage_kes?: number;
  exception_count?: number;
}

export interface Filters {
  depot: string[];
  product: string[];
  customer: string;
  startDate: string;
  endDate: string;
}
