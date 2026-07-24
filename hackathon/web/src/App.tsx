import { useMemo, useState } from "react";
import { api } from "./api";
import { useAsync, useTheme } from "./hooks";
import type { Filters } from "./types";
import { Header } from "./components/Header";
import { FilterBar } from "./components/FilterBar";
import { KpiCards } from "./components/KpiCards";
import { Tabs, type TabDef } from "./components/Tabs";
import { OverviewTab } from "./components/OverviewTab";
import { ExceptionsTab } from "./components/ExceptionsTab";
import { RoiTab } from "./components/RoiTab";
import { DataQualityTab } from "./components/DataQualityTab";
import { FullPageSpinner, ErrorState } from "./components/ui/Spinner";

const EMPTY_FILTERS: Filters = { depot: [], product: [], customer: "", startDate: "", endDate: "" };

export default function App() {
  const { theme, toggleTheme } = useTheme();
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [activeTab, setActiveTab] = useState("overview");
  const [exceptionOffset, setExceptionOffset] = useState(0);
  const [rerunning, setRerunning] = useState(false);

  const optionsQuery = useAsync(() => api.filterOptions(), []);

  // Seed the date range from the dataset's actual bounds once options load.
  const effectiveFilters = useMemo<Filters>(() => {
    if (filters.startDate && filters.endDate) return filters;
    if (!optionsQuery.data) return filters;
    return { ...filters, startDate: optionsQuery.data.min_date, endDate: optionsQuery.data.max_date };
  }, [filters, optionsQuery.data]);

  const kpisQuery = useAsync(
    () => api.kpis(effectiveFilters),
    [JSON.stringify(effectiveFilters)],
  );
  const trendQuery = useAsync(
    () => api.trend(effectiveFilters),
    [JSON.stringify(effectiveFilters)],
  );
  const exceptionsQuery = useAsync(
    () => api.exceptions(effectiveFilters, 20, exceptionOffset),
    [JSON.stringify(effectiveFilters), exceptionOffset],
  );
  const narrativeQuery = useAsync(() => api.narrative(), []);
  const roiQuery = useAsync(() => api.roi(), []);
  const dqQuery = useAsync(() => api.dataQuality(), []);
  const metaQuery = useAsync(() => api.meta(), []);

  const handleRerun = async () => {
    setRerunning(true);
    try {
      await api.runPipeline();
      kpisQuery.refetch();
      trendQuery.refetch();
      exceptionsQuery.refetch();
      narrativeQuery.refetch();
      roiQuery.refetch();
      dqQuery.refetch();
      metaQuery.refetch();
      optionsQuery.refetch();
    } catch {
      // surfaced via metaQuery status on next poll; no extra UI needed for a hackathon demo
    } finally {
      setRerunning(false);
    }
  };

  const tabs: TabDef[] = [
    { id: "overview", label: "Overview" },
    { id: "exceptions", label: "Exceptions & Audit Trail", badge: kpisQuery.data?.exception_count },
    { id: "roi", label: "ROI & Business Case" },
    { id: "quality", label: "Data Quality" },
  ];

  if (optionsQuery.loading && !optionsQuery.data) {
    return (
      <div className="flex h-screen items-center justify-center" style={{ background: "var(--surface-2)" }}>
        <FullPageSpinner label="Loading dashboard…" />
      </div>
    );
  }

  if (optionsQuery.error || !optionsQuery.data) {
    return (
      <div className="flex h-screen items-center justify-center p-6" style={{ background: "var(--surface-2)" }}>
        <ErrorState
          message={optionsQuery.error ?? "No pipeline output found. Run the pipeline first."}
          onRetry={optionsQuery.refetch}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: "var(--surface-2)" }}>
      <Header
        theme={theme}
        onToggleTheme={toggleTheme}
        runLog={metaQuery.data}
        onRerun={handleRerun}
        rerunning={rerunning}
      />

      <main className="mx-auto flex max-w-7xl flex-col gap-4 px-6 py-6">
        <FilterBar options={optionsQuery.data} filters={effectiveFilters} onChange={setFilters} />

        {kpisQuery.loading && !kpisQuery.data ? (
          <FullPageSpinner label="Computing KPIs…" />
        ) : kpisQuery.error ? (
          <ErrorState message={kpisQuery.error} onRetry={kpisQuery.refetch} />
        ) : kpisQuery.data ? (
          <KpiCards kpis={kpisQuery.data} runLog={metaQuery.data} />
        ) : null}

        <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab} />

        <div className="pb-10">
          {activeTab === "overview" &&
            (kpisQuery.data && trendQuery.data ? (
              <OverviewTab kpis={kpisQuery.data} trend={trendQuery.data} />
            ) : (
              <FullPageSpinner label="Loading charts…" />
            ))}

          {activeTab === "exceptions" && (
            <ExceptionsTab
              data={exceptionsQuery.data}
              narrative={narrativeQuery.data}
              loading={exceptionsQuery.loading}
              onPageChange={setExceptionOffset}
            />
          )}

          {activeTab === "roi" &&
            (roiQuery.data ? <RoiTab roi={roiQuery.data} /> : <FullPageSpinner label="Loading ROI model…" />)}

          {activeTab === "quality" &&
            (dqQuery.data ? (
              <DataQualityTab dq={dqQuery.data} />
            ) : (
              <FullPageSpinner label="Loading data-quality report…" />
            ))}
        </div>
      </main>
    </div>
  );
}
