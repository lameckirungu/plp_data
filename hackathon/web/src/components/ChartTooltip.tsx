import { fmtKes } from "../format";

export function ChartTooltip({
  active,
  payload,
  label,
  labelFormatter,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color?: string }[];
  label?: string;
  labelFormatter?: (label: string) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs shadow-lg"
      style={{
        background: "var(--surface-raised)",
        borderColor: "var(--border)",
        color: "var(--text-primary)",
      }}
    >
      {label && (
        <p className="mb-1 font-medium" style={{ color: "var(--text-secondary)" }}>
          {labelFormatter ? labelFormatter(label) : label}
        </p>
      )}
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2">
          {entry.color && (
            <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: entry.color }} />
          )}
          <span style={{ color: "var(--text-secondary)" }}>{entry.name}:</span>
          <span className="tabular-nums font-medium">{fmtKes(entry.value)}</span>
        </div>
      ))}
    </div>
  );
}
