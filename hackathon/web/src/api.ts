import type {
  DataQuality,
  ExceptionsResponse,
  FilterOptions,
  Filters,
  Kpis,
  NarrativeResponse,
  Roi,
  RunLog,
  TrendPoint,
} from "./types";

function buildQuery(filters: Partial<Filters>, extra: Record<string, string | number> = {}): string {
  const params = new URLSearchParams();
  filters.depot?.forEach((d) => params.append("depot", d));
  filters.product?.forEach((p) => params.append("product", p));
  if (filters.customer) params.set("customer", filters.customer);
  if (filters.startDate) params.set("start_date", filters.startDate);
  if (filters.endDate) params.set("end_date", filters.endDate);
  for (const [key, value] of Object.entries(extra)) {
    params.set(key, String(value));
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  filterOptions: () => getJson<FilterOptions>("/api/filters/options"),

  kpis: (filters: Partial<Filters>) => getJson<Kpis>(`/api/kpis${buildQuery(filters)}`),

  trend: (filters: Partial<Filters>) => getJson<TrendPoint[]>(`/api/trend${buildQuery(filters)}`),

  exceptions: (filters: Partial<Filters>, limit: number, offset: number) =>
    getJson<ExceptionsResponse>(`/api/exceptions${buildQuery(filters, { limit, offset })}`),

  roi: () => getJson<Roi>("/api/roi"),

  narrative: () => getJson<NarrativeResponse>("/api/narrative"),

  dataQuality: () => getJson<DataQuality>("/api/data-quality"),

  meta: () => getJson<RunLog>("/api/meta"),

  runPipeline: async (): Promise<{ status: string; quality_gate_status: string }> => {
    const res = await fetch("/api/pipeline/run", { method: "POST" });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `Pipeline run failed: ${res.status}`);
    }
    return res.json();
  },
};
