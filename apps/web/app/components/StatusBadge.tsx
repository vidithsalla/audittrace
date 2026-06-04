import { titleize } from "@/lib/format";

export function StatusBadge({ value }: { value: string }) {
  return <span className={`badge ${value}`}>{titleize(value)}</span>;
}
