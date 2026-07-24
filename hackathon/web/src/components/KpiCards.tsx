import type { Kpis, RunLog } from "../types";
import { fmtKes, fmtPct } from "../format";
import { Card } from "./ui/Card";

function Tile({
  label,
  value,
  hint,
  accent,
}: {
  label: string;
  value: string;
  hint?: string;
  accent?: string;
}) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
      <p
        className="tabular-nums mt-2 text-2xl font-semibold"
        style={{ color: accent ?? "var(--text-primary)" }}
      >
        {value}
      </p>
      {hint && (
        <p className="mt-1 text-xs" style={{ color: "var(--text-secondary)" }}>
          {hint}
        </p>
      )}
    </Card>
  );
}

export function KpiCards({ kpis, runLog }: { kpis: Kpis; runLog: RunLog | null }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
      <Tile
        label="Total leakage"
        value={fmtKes(kpis.total_leakage_kes)}
        accent="var(--status-critical)"
        hint={`of ${fmtKes(kpis.total_expected_revenue_kes)} expected`}
      />
      <Tile label="% of expected revenue" value={fmtPct(kpis.leakage_pct_of_expected_revenue)} />
      <Tile
        label="Exception rate"
        value={fmtPct(kpis.exception_rate_pct)}
        hint={`${kpis.exception_count.toLocaleString()} of ${kpis.total_loadings.toLocaleString()} loadings`}
      />
      <Tile label="Annualized leakage" value={fmtKes(kpis.annualized_leakage_kes)} />
      <Tile
        label="Data-quality gate"
        value={runLog?.quality_gate_status ?? "N/A"}
        accent={runLog?.quality_gate_status === "PASS" ? "var(--status-good)" : "var(--status-critical)"}
      />
    </div>
  );
}
