import type { ReactNode } from "react";
import clsx from "clsx";

export function Card({
  children,
  className,
  title,
  subtitle,
  action,
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div
      className={clsx(
        "rounded-xl border shadow-sm",
        className,
      )}
      style={{
        background: "var(--surface-1)",
        borderColor: "var(--border)",
      }}
    >
      {(title || action) && (
        <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-1">
          <div>
            {title && (
              <h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                {subtitle}
              </p>
            )}
          </div>
          {action}
        </div>
      )}
      <div className="px-5 pb-5 pt-3">{children}</div>
    </div>
  );
}
