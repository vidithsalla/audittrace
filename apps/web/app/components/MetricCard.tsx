import { formatMetric } from "@/lib/format";

export function MetricCard({
  label,
  value,
  kind = "number",
  hint,
}: {
  label: string;
  value: number | null;
  kind?: "percent" | "number" | "ms";
  hint?: string;
}) {
  return (
    <div className="card metric">
      <span className="muted">{label}</span>
      <span className="metric-value">{formatMetric(value, kind)}</span>
      {hint ? <span className="muted">{hint}</span> : null}
    </div>
  );
}
