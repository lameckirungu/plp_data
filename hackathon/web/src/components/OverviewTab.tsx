import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Kpis, TrendPoint } from "../types";
import { LEAKAGE_CATEGORIES } from "../types";
import { CATEGORY_COLOR_VARS, CATEGORY_LABELS, fmtKes } from "../format";
import { Card } from "./ui/Card";
import { ChartTooltip } from "./ChartTooltip";

const AXIS_STYLE = { fontSize: 11, fill: "var(--text-muted)" };

function LabeledHBar({
  data,
  dataKey,
  nameKey,
  colorFn,
  seriesName,
}: {
  data: Record<string, string | number>[];
  dataKey: string;
  nameKey: string;
  colorFn: (row: Record<string, string | number>, i: number) => string;
  seriesName: string;
}) {
  const height = Math.max(data.length * 42, 120);
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 32, top: 4, bottom: 4 }}>
        <CartesianGrid horizontal={false} stroke="var(--gridline)" />
        <XAxis type="number" tick={AXIS_STYLE} tickFormatter={(v) => fmtKes(v)} axisLine={{ stroke: "var(--baseline)" }} tickLine={false} />
        <YAxis
          type="category"
          dataKey={nameKey}
          width={110}
          tick={AXIS_STYLE}
          axisLine={{ stroke: "var(--baseline)" }}
          tickLine={false}
        />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ fill: "color-mix(in srgb, var(--text-primary) 4%, transparent)" }}
        />
        <Bar dataKey={dataKey} name={seriesName} radius={[0, 4, 4, 0]} maxBarSize={22}>
          {data.map((row, i) => (
            <Cell key={i} fill={colorFn(row, i)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function OverviewTab({ kpis, trend }: { kpis: Kpis; trend: TrendPoint[] }) {
  const categoryData = LEAKAGE_CATEGORIES.map((c) => ({
    name: CATEGORY_LABELS[c],
    value: kpis.leakage_by_category_kes[c],
    _cat: c,
  })).sort((a, b) => a.value - b.value);

  const depotData = [...kpis.by_depot]
    .sort((a, b) => (a.total_leakage_kes as number) - (b.total_leakage_kes as number))
    .map((r) => ({ depot: r.depot, total_leakage_kes: r.total_leakage_kes }));

  const customerData = [...kpis.by_customer]
    .sort((a, b) => (a.total_leakage_kes as number) - (b.total_leakage_kes as number))
    .slice(-8)
    .map((r) => ({ customer: r.customer, total_leakage_kes: r.total_leakage_kes }));

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card title="Leakage by category" subtitle="Fixed color per category, sorted by size">
        <LabeledHBar
          data={categoryData}
          dataKey="value"
          nameKey="name"
          seriesName="Leakage"
          colorFn={(row) => CATEGORY_COLOR_VARS[row._cat as keyof typeof CATEGORY_COLOR_VARS]}
        />
      </Card>

      <Card title="Leakage by depot">
        <LabeledHBar
          data={depotData}
          dataKey="total_leakage_kes"
          nameKey="depot"
          seriesName="Leakage"
          colorFn={() => "var(--series-1)"}
        />
      </Card>

      <Card title="Daily leakage trend" subtitle="Sum of total_leakage_kes by loading date">
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={trend} margin={{ left: 4, right: 12, top: 8, bottom: 4 }}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--series-1)" stopOpacity={0.25} />
                <stop offset="100%" stopColor="var(--series-1)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="var(--gridline)" />
            <XAxis
              dataKey="day"
              tick={AXIS_STYLE}
              axisLine={{ stroke: "var(--baseline)" }}
              tickLine={false}
              minTickGap={24}
            />
            <YAxis tick={AXIS_STYLE} tickFormatter={(v) => fmtKes(v)} axisLine={false} tickLine={false} width={64} />
            <Tooltip content={<ChartTooltip />} />
            <Area
              type="monotone"
              dataKey="total_leakage_kes"
              name="Daily leakage"
              stroke="var(--series-1)"
              strokeWidth={2}
              fill="url(#trendFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </Card>

      <Card title="Top customers by leakage exposure">
        <LabeledHBar
          data={customerData}
          dataKey="total_leakage_kes"
          nameKey="customer"
          seriesName="Leakage"
          colorFn={() => "var(--series-1)"}
        />
      </Card>
    </div>
  );
}
