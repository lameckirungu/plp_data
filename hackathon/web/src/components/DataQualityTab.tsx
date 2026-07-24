import type { DataQuality } from "../types";
import { Badge } from "./ui/Badge";
import { Card } from "./ui/Card";

const SEVERITY_STATUS = {
  critical: "critical",
  warning: "warning",
  exception: "neutral",
} as const;

export function DataQualityTab({ dq }: { dq: DataQuality }) {
  return (
    <div className="flex flex-col gap-4">
      <Card title="Quality gate status">
        <Badge status={dq.overall_status === "PASS" ? "good" : "critical"}>{dq.overall_status}</Badge>

        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr style={{ color: "var(--text-muted)" }}>
                {["Check", "Status", "Detail"].map((h) => (
                  <th key={h} className="whitespace-nowrap pb-2 pr-4 text-xs font-medium uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dq.checks.map((check) => (
                <tr key={check.name} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                  <td className="whitespace-nowrap py-2 pr-4 font-mono text-xs">{check.name}</td>
                  <td className="py-2 pr-4">
                    <Badge status={check.status === "PASS" ? "good" : "critical"}>{check.status}</Badge>
                  </td>
                  <td className="py-2 pr-4 text-xs" style={{ color: "var(--text-secondary)" }}>
                    {check.detail}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card
        title="Cleaning issues log"
        subtitle="'critical' issues fail the gate above threshold; 'warning' and 'exception' never do"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr style={{ color: "var(--text-muted)" }}>
                {["Table", "Check", "Severity", "Count"].map((h) => (
                  <th key={h} className="whitespace-nowrap pb-2 pr-4 text-xs font-medium uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dq.issues.map((issue, i) => (
                <tr key={i} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                  <td className="py-2 pr-4">{issue.table}</td>
                  <td className="py-2 pr-4 font-mono text-xs">{issue.check}</td>
                  <td className="py-2 pr-4">
                    <Badge status={SEVERITY_STATUS[issue.severity]}>{issue.severity}</Badge>
                  </td>
                  <td className="tabular-nums py-2 pr-4">{issue.count.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
