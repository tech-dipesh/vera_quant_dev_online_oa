export function EquitySparkline({ values }: { values: number[] }) {
  if (values.length < 2) {
    return <div className="flex h-32 items-center justify-center text-sm text-ink-dim">waiting for data</div>;
  }

  const width = 600;
  const height = 128;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const points = values
    .map((value, index) => {
      const x = (index / (values.length - 1)) * width;
      const y = height - ((value - min) / range) * height;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const latest = values[values.length - 1];
  const lineColor = latest >= values[0] ? "var(--color-long)" : "var(--color-short)";

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-32 w-full" preserveAspectRatio="none">
      <polyline points={points} fill="none" stroke={lineColor} strokeWidth={1.5} />
    </svg>
  );
}
