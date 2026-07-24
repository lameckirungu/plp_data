import clsx from "clsx";

export interface TabDef {
  id: string;
  label: string;
  badge?: number;
}

export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: TabDef[];
  active: string;
  onChange: (id: string) => void;
}) {
  return (
    <div className="flex gap-1 border-b" style={{ borderColor: "var(--border)" }}>
      {tabs.map((tab) => {
        const isActive = tab.id === active;
        return (
          <button
            key={tab.id}
            onClick={() => onChange(tab.id)}
            className={clsx("relative px-4 py-2.5 text-sm font-medium transition-colors")}
            style={{ color: isActive ? "var(--text-primary)" : "var(--text-muted)" }}
          >
            <span className="flex items-center gap-2">
              {tab.label}
              {tab.badge !== undefined && tab.badge > 0 && (
                <span
                  className="rounded-full px-1.5 py-0.5 text-[10px] font-semibold"
                  style={{
                    background: "color-mix(in srgb, var(--status-critical) 16%, transparent)",
                    color: "var(--status-critical)",
                  }}
                >
                  {tab.badge}
                </span>
              )}
            </span>
            {isActive && (
              <span
                className="absolute inset-x-0 -bottom-px h-0.5 rounded-full"
                style={{ background: "var(--series-1)" }}
              />
            )}
          </button>
        );
      })}
    </div>
  );
}
