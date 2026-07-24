import type { Roi } from "../types";
import { CATEGORY_LABELS, fmtKes, fmtPct } from "../format";
import { Card } from "./ui/Card";

function Stat({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
      <p className="tabular-nums mt-1 text-xl font-semibold" style={{ color: accent ?? "var(--text-primary)" }}>
        {value}
      </p>
    </div>
  );
}

export function RoiTab({ roi }: { roi: Roi }) {
  return (
    <div className="flex flex-col gap-4">
      <Card>
        <p
          className="mb-4 rounded-lg px-3 py-2 text-xs"
          style={{
            background: "color-mix(in srgb, var(--status-warning) 14%, transparent)",
            color: "var(--text-secondary)",
          }}
        >
          {roi.note}
        </p>
        <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
          <Stat label="Year-1 build cost" value={fmtKes(roi.implementation_cost_kes)} />
          <Stat
            label="Year-1 realized benefit"
            value={fmtKes(roi.year1_realized_benefit_kes)}
            accent="var(--status-good)"
          />
          <Stat label="Payback period" value={`${roi.payback_period_months.toFixed(1)} months`} />
          <Stat label="Year-1 ROI multiple" value={`${roi.roi_multiple_year1.toFixed(1)}x`} accent="var(--series-1)" />
        </div>
        <p className="mt-4 text-sm" style={{ color: "var(--text-secondary)" }}>
          Steady-state annual recovery (full network live):{" "}
          <span className="font-medium" style={{ color: "var(--text-primary)" }}>
            {fmtKes(roi.steady_state_recoverable_annual_kes)}
          </span>{" "}
          — {fmtPct(roi.year1_adoption_ramp_factor * 100, 0)} of that is assumed realized in year one due to
          phased rollout.
        </p>
      </Card>

      <Card title="Recovery assumptions by category">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr style={{ color: "var(--text-muted)" }}>
                {["Category", "Annualized leakage", "Recovery rate", "Recoverable/year", "Why this rate"].map((h) => (
                  <th key={h} className="whitespace-nowrap pb-2 pr-4 text-xs font-medium uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {roi.category_breakdown.map((row) => (
                <tr key={row.category} className="border-t align-top" style={{ borderColor: "var(--gridline)" }}>
                  <td className="whitespace-nowrap py-2.5 pr-4 font-medium" style={{ color: "var(--text-primary)" }}>
                    {CATEGORY_LABELS[row.category]}
                  </td>
                  <td className="tabular-nums py-2.5 pr-4">{fmtKes(row.annualized_leakage_kes)}</td>
                  <td className="tabular-nums py-2.5 pr-4">{fmtPct(row.recovery_rate * 100, 0)}</td>
                  <td className="tabular-nums py-2.5 pr-4 font-medium" style={{ color: "var(--status-good)" }}>
                    {fmtKes(row.recoverable_kes)}
                  </td>
                  <td className="max-w-xs py-2.5 pr-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {row.rationale}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
