import { StatusDot } from "@/components/StatusDot";
import type { ConnectionStatus } from "@/hooks/useLiveFeed";

type Props = {
  symbol: string;
  running: boolean;
  connection: ConnectionStatus;
  lastPrice: number | null;
  busy: boolean;
  onStart: () => void;
  onStop: () => void;
  onFlatten: () => void;
};

const connectionTone = {
  open: "live",
  connecting: "warn",
  closed: "danger",
} as const;

export function ControlBar({
  symbol,
  running,
  connection,
  lastPrice,
  busy,
  onStart,
  onStop,
  onFlatten,
}: Props) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-line pb-4">
      <div className="flex items-baseline gap-4">
        <h1 className="font-mono text-lg font-medium">{symbol}</h1>
        <span className="font-mono text-2xl">{lastPrice !== null ? lastPrice.toFixed(2) : "--.--"}</span>
        <div className="flex items-center gap-1.5 text-xs text-ink-dim">
          <StatusDot tone={connectionTone[connection]} />
          feed {connection}
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onStart}
          disabled={running || busy}
          className="rounded border border-line px-3 py-1.5 text-sm text-long disabled:opacity-40"
        >
          Start
        </button>
        <button
          onClick={onFlatten}
          disabled={!running || busy}
          className="rounded border border-line px-3 py-1.5 text-sm text-amber disabled:opacity-40"
        >
          Flatten
        </button>
        <button
          onClick={onStop}
          disabled={!running || busy}
          className="rounded border border-line px-3 py-1.5 text-sm text-short disabled:opacity-40"
        >
          Stop
        </button>
      </div>
    </div>
  );
}
