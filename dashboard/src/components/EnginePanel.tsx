import type { Position } from "@/lib/schemas";

function formatSigned(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}`;
}

export function EnginePanel({ name, position }: { name: string; position: Position | null }) {
  const side = position?.side ?? null;
  const sideColor = side === "long" ? "text-long" : side === "short" ? "text-short" : "text-ink-dim";
  const pnlColor = (position?.realized_pnl ?? 0) >= 0 ? "text-long" : "text-short";

  return (
    <div className="rounded border border-line bg-surface-1 p-4">
      <div className="text-xs uppercase tracking-wide text-ink-dim">{name.replace(/_/g, " ")}</div>

      <div className="mt-3 flex items-baseline justify-between">
        <span className={`font-mono text-lg ${sideColor}`}>{side ? side.toUpperCase() : "FLAT"}</span>
        <span className="font-mono text-sm text-ink-dim">qty {position?.quantity ?? 0}</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 font-mono text-sm">
        <div>
          <div className="text-xs text-ink-dim">avg price</div>
          <div>{position ? position.average_price.toFixed(2) : "-"}</div>
        </div>
        <div>
          <div className="text-xs text-ink-dim">realized P&amp;L</div>
          <div className={pnlColor}>{position ? formatSigned(position.realized_pnl) : "-"}</div>
        </div>
      </div>
    </div>
  );
}
