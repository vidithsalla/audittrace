export function formatMetric(value: number | null, kind: "percent" | "number" | "ms" = "number") {
  if (value === null || Number.isNaN(value)) {
    return "n/a";
  }
  if (kind === "percent") {
    return `${(value * 100).toFixed(1)}%`;
  }
  if (kind === "ms") {
    return `${value.toFixed(1)} ms`;
  }
  return Number.isInteger(value) ? `${value}` : value.toFixed(4);
}

export function titleize(value: string) {
  return value.replaceAll("_", " ");
}
