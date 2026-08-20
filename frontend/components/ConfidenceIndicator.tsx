import { Confidence } from "@/lib/api";

const STYLES: Record<Confidence, { label: string; className: string }> = {
  low: { label: "Low data", className: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300" },
  medium: { label: "Some data", className: "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300" },
  high: { label: "Well reviewed", className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300" },
};

export function ConfidenceIndicator({ confidence }: { confidence: Confidence }) {
  const style = STYLES[confidence];
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${style.className}`}>{style.label}</span>
  );
}
