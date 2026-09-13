const colorByTone = {
  live: "bg-long",
  idle: "bg-ink-dim",
  danger: "bg-short",
  warn: "bg-amber",
} as const;

export function StatusDot({ tone }: { tone: keyof typeof colorByTone }) {
  return <span className={`inline-block h-2 w-2 rounded-full ${colorByTone[tone]}`} />;
}
