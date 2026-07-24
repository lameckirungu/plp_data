import clsx from "clsx";

type Status = "good" | "warning" | "serious" | "critical" | "neutral";

const STATUS_COLOR: Record<Status, string> = {
  good: "var(--status-good)",
  warning: "var(--status-warning)",
  serious: "var(--status-serious)",
  critical: "var(--status-critical)",
  neutral: "var(--text-muted)",
};

export function Badge({ status, children }: { status: Status; children: React.ReactNode }) {
  const color = STATUS_COLOR[status];
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
      )}
      style={{
        color,
        background: `color-mix(in srgb, ${color} 14%, transparent)`,
      }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
      {children}
    </span>
  );
}
