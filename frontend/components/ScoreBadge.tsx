export function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="text-sm text-zinc-400 dark:text-zinc-500">Not personalized yet</span>;
  }
  const color =
    score >= 70
      ? "bg-emerald-600"
      : score >= 45
        ? "bg-amber-500"
        : "bg-rose-500";
  return (
    <span className={`inline-flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold text-white ${color}`}>
      {score}
    </span>
  );
}
