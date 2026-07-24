export function Spinner({ size = 16 }: { size?: number }) {
  return (
    <svg
      className="animate-spin"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      style={{ color: "var(--text-muted)" }}
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
      <path d="M22 12a10 10 0 0 0-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}

export function FullPageSpinner({ label }: { label?: string }) {
  return (
    <div className="flex h-64 flex-col items-center justify-center gap-3">
      <Spinner size={28} />
      {label && (
        <p className="text-sm" style={{ color: "var(--text-muted)" }}>
          {label}
        </p>
      )}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div
      className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed py-12 text-center"
      style={{ borderColor: "var(--border)" }}
    >
      <p className="text-sm font-medium" style={{ color: "var(--status-critical)" }}>
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg px-3 py-1.5 text-xs font-medium"
          style={{ background: "var(--series-1)", color: "white" }}
        >
          Retry
        </button>
      )}
    </div>
  );
}
