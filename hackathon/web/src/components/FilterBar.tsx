import type { FilterOptions, Filters } from "../types";
import clsx from "clsx";
import { Card } from "./ui/Card";

function MultiPill({
  options,
  selected,
  onToggle,
}: {
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {options.map((opt) => {
        const active = selected.length === 0 || selected.includes(opt);
        return (
          <button
            key={opt}
            onClick={() => onToggle(opt)}
            className={clsx(
              "rounded-full border px-2.5 py-1 text-xs font-medium transition-colors",
            )}
            style={{
              borderColor: active ? "var(--series-1)" : "var(--border)",
              color: active ? "var(--series-1)" : "var(--text-secondary)",
              background: active ? "color-mix(in srgb, var(--series-1) 10%, transparent)" : "transparent",
            }}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}

export function FilterBar({
  options,
  filters,
  onChange,
}: {
  options: FilterOptions;
  filters: Filters;
  onChange: (next: Filters) => void;
}) {
  const toggle = (key: "depot" | "product", value: string) => {
    const current = filters[key];
    const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
    onChange({ ...filters, [key]: next });
  };

  return (
    <Card>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-6">
          <FilterGroup label="Depot">
            <MultiPill options={options.depots} selected={filters.depot} onToggle={(v) => toggle("depot", v)} />
          </FilterGroup>
          <FilterGroup label="Product">
            <MultiPill options={options.products} selected={filters.product} onToggle={(v) => toggle("product", v)} />
          </FilterGroup>
          <FilterGroup label="Customer">
            <input
              value={filters.customer}
              onChange={(e) => onChange({ ...filters, customer: e.target.value })}
              placeholder="Search..."
              className="w-40 rounded-lg border px-2.5 py-1.5 text-sm outline-none focus:ring-2"
              style={{
                borderColor: "var(--border)",
                background: "var(--surface-raised)",
                color: "var(--text-primary)",
              }}
            />
          </FilterGroup>
          <FilterGroup label="Date range">
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={filters.startDate}
                min={options.min_date}
                max={options.max_date}
                onChange={(e) => onChange({ ...filters, startDate: e.target.value })}
                className="rounded-lg border px-2 py-1.5 text-sm outline-none"
                style={{ borderColor: "var(--border)", background: "var(--surface-raised)", color: "var(--text-primary)" }}
              />
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>
                to
              </span>
              <input
                type="date"
                value={filters.endDate}
                min={options.min_date}
                max={options.max_date}
                onChange={(e) => onChange({ ...filters, endDate: e.target.value })}
                className="rounded-lg border px-2 py-1.5 text-sm outline-none"
                style={{ borderColor: "var(--border)", background: "var(--surface-raised)", color: "var(--text-primary)" }}
              />
            </div>
          </FilterGroup>
        </div>
        <button
          onClick={() =>
            onChange({
              depot: [],
              product: [],
              customer: "",
              startDate: options.min_date,
              endDate: options.max_date,
            })
          }
          className="whitespace-nowrap rounded-lg border px-3 py-1.5 text-xs font-medium"
          style={{ borderColor: "var(--border)", color: "var(--text-secondary)" }}
        >
          Reset filters
        </button>
      </div>
    </Card>
  );
}

function FilterGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="mb-1.5 text-[11px] font-semibold uppercase tracking-wide" style={{ color: "var(--text-muted)" }}>
        {label}
      </p>
      {children}
    </div>
  );
}
