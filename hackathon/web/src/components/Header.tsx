import { Moon, RefreshCw, Sun, Waves } from "lucide-react";
import type { RunLog } from "../types";
import { Badge } from "./ui/Badge";
import { Spinner } from "./ui/Spinner";

export function Header({
  theme,
  onToggleTheme,
  runLog,
  onRerun,
  rerunning,
}: {
  theme: "light" | "dark";
  onToggleTheme: () => void;
  runLog: RunLog | null;
  onRerun: () => void;
  rerunning: boolean;
}) {
  const gateStatus = runLog?.quality_gate_status;
  return (
    <header
      className="sticky top-0 z-10 border-b backdrop-blur"
      style={{
        borderColor: "var(--border)",
        background: "color-mix(in srgb, var(--surface-1) 88%, transparent)",
      }}
    >
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-3">
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg"
            style={{ background: "var(--series-1)" }}
          >
            <Waves size={18} color="white" />
          </div>
          <div>
            <h1 className="text-sm font-semibold leading-tight" style={{ color: "var(--text-primary)" }}>
              Order-to-Cash Leakage
            </h1>
            <p className="text-xs leading-tight" style={{ color: "var(--text-muted)" }}>
              KPC Problem 7D · Revenue Assurance &amp; Reconciliation
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {gateStatus && (
            <Badge status={gateStatus === "PASS" ? "good" : "critical"}>
              Quality gate: {gateStatus}
            </Badge>
          )}
          <button
            onClick={onRerun}
            disabled={rerunning}
            className="flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium disabled:opacity-60"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            {rerunning ? <Spinner size={14} /> : <RefreshCw size={14} />}
            {rerunning ? "Running…" : "Re-run pipeline"}
          </button>
          <button
            onClick={onToggleTheme}
            aria-label="Toggle theme"
            className="flex h-8 w-8 items-center justify-center rounded-lg border"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            {theme === "light" ? <Moon size={15} /> : <Sun size={15} />}
          </button>
        </div>
      </div>
    </header>
  );
}
