import { useState } from "react";
import { Download } from "lucide-react";
import type { ExceptionsResponse, NarrativeResponse } from "../types";
import { CATEGORY_SHORT_LABELS, fmtKes } from "../format";
import { Card } from "./ui/Card";
import { FullPageSpinner } from "./ui/Spinner";
import { RichText } from "./RichText";

const PAGE_SIZE = 20;

function toCsv(rows: ExceptionsResponse["rows"]): string {
  if (rows.length === 0) return "";
  const headers = Object.keys(rows[0]) as (keyof ExceptionsResponse["rows"][number])[];
  const lines = [headers.join(",")];
  for (const row of rows) {
    lines.push(headers.map((h) => JSON.stringify(row[h] ?? "")).join(","));
  }
  return lines.join("\n");
}

export function ExceptionsTab({
  data,
  narrative,
  loading,
  onPageChange,
}: {
  data: ExceptionsResponse | null;
  narrative: NarrativeResponse | null;
  loading: boolean;
  onPageChange: (offset: number) => void;
}) {
  const [page, setPage] = useState(0);

  const handlePage = (next: number) => {
    setPage(next);
    onPageChange(next * PAGE_SIZE);
  };

  const downloadCsv = () => {
    if (!data) return;
    const blob = new Blob([toCsv(data.rows)], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "o2c_exceptions.csv";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-4">
      {narrative && (
        <Card title="Executive narrative" subtitle="Generated from the current pipeline run">
          <div className="space-y-2 text-sm leading-relaxed" style={{ color: "var(--text-secondary)" }}>
            {narrative.executive_narrative.split("\n\n").map((para, i) => (
              <p key={i}>
                <RichText text={para} />
              </p>
            ))}
          </div>
        </Card>
      )}

      <Card
        title="Exceptions / audit trail"
        subtitle={data ? `${data.total.toLocaleString()} exceptions match the current filters` : undefined}
        action={
          <button
            onClick={downloadCsv}
            disabled={!data || data.rows.length === 0}
            className="flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium disabled:opacity-50"
            style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            <Download size={13} />
            Export CSV
          </button>
        }
      >
        {loading || !data ? (
          <FullPageSpinner label="Loading exceptions…" />
        ) : data.rows.length === 0 ? (
          <p className="py-8 text-center text-sm" style={{ color: "var(--text-muted)" }}>
            No exceptions match the current filters.
          </p>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr style={{ color: "var(--text-muted)" }}>
                    {["Loading", "Depot", "Product", "Customer", "Category", "Leakage"].map((h) => (
                      <th key={h} className="whitespace-nowrap pb-2 pr-4 text-xs font-medium uppercase tracking-wide">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {data.rows.map((row) => (
                    <tr key={row.loading_id} className="border-t" style={{ borderColor: "var(--gridline)" }}>
                      <td className="py-2 pr-4 font-mono text-xs" style={{ color: "var(--text-primary)" }}>
                        {row.loading_id}
                      </td>
                      <td className="py-2 pr-4">{row.depot}</td>
                      <td className="py-2 pr-4">{row.product}</td>
                      <td className="py-2 pr-4">{row.customer}</td>
                      <td className="py-2 pr-4">{CATEGORY_SHORT_LABELS[row.leakage_category] ?? row.leakage_category}</td>
                      <td className="tabular-nums py-2 pr-4 font-medium" style={{ color: "var(--status-critical)" }}>
                        {fmtKes(row.total_leakage_kes)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                Page {page + 1} of {Math.max(1, Math.ceil(data.total / PAGE_SIZE))}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => handlePage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className="rounded-lg border px-2.5 py-1 text-xs font-medium disabled:opacity-40"
                  style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                >
                  Previous
                </button>
                <button
                  onClick={() => handlePage(page + 1)}
                  disabled={(page + 1) * PAGE_SIZE >= data.total}
                  className="rounded-lg border px-2.5 py-1 text-xs font-medium disabled:opacity-40"
                  style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </Card>
    </div>
  );
}
