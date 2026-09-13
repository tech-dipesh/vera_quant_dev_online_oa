"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ControlBar } from "@/components/ControlBar";
import { EnginePanel } from "@/components/EnginePanel";
import { EquitySparkline } from "@/components/EquitySparkline";
import { BlotterFeed } from "@/components/BlotterFeed";
import { MacroRegimeBadge } from "@/components/MacroRegimeBadge";
import { useLiveFeed } from "@/hooks/useLiveFeed";
import {
  fetchDemoStatus,
  fetchMacroRegime,
  fetchPositions,
  flattenDemo,
  startDemo,
  stopDemo,
} from "@/lib/api";
import type { DemoStatus, FillEvent, LiveEvent, MacroRegime, Positions } from "@/lib/schemas";

const POLL_INTERVAL_MS = 2000;
const MAX_FILLS = 50;
const MAX_EQUITY_POINTS = 200;

export default function Dashboard() {
  const [status, setStatus] = useState<DemoStatus | null>(null);
  const [positions, setPositions] = useState<Positions>({});
  const [regime, setRegime] = useState<MacroRegime | null>(null);
  const [lastPrice, setLastPrice] = useState<number | null>(null);
  const [fills, setFills] = useState<FillEvent[]>([]);
  const [equitySeries, setEquitySeries] = useState<number[]>([]);
  const [busy, setBusy] = useState(false);
  const positionsRef = useRef<Positions>({});

  const poll = useCallback(async () => {
    const [nextStatus, nextPositions, nextRegime] = await Promise.all([
      fetchDemoStatus(),
      fetchPositions(),
      fetchMacroRegime(),
    ]);
    setStatus(nextStatus);
    setPositions(nextPositions);
    positionsRef.current = nextPositions;
    setRegime(nextRegime);

    const totalPnl = Object.values(nextPositions).reduce(
      (sum, position) => sum + position.realized_pnl,
      0,
    );
    setEquitySeries((series) => [...series, totalPnl].slice(-MAX_EQUITY_POINTS));
  }, []);

  useEffect(() => {
    const initial = setTimeout(poll, 0);
    const interval = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      clearTimeout(initial);
      clearInterval(interval);
    };
  }, [poll]);

  const handleEvent = useCallback((event: LiveEvent) => {
    if (event.type === "tick") {
      setLastPrice(event.price);
    } else {
      setFills((current) => [event, ...current].slice(0, MAX_FILLS));
    }
  }, []);

  const connection = useLiveFeed(handleEvent);

  async function handleStart() {
    setBusy(true);
    try {
      await startDemo();
      await poll();
    } finally {
      setBusy(false);
    }
  }

  async function handleStop() {
    setBusy(true);
    try {
      await stopDemo();
      await poll();
    } finally {
      setBusy(false);
    }
  }

  async function handleFlatten() {
    setBusy(true);
    try {
      await flattenDemo();
      await poll();
    } finally {
      setBusy(false);
    }
  }

  const engineNames = status?.engines.length ? status.engines : ["grid", "stop_and_reverse"];

  return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      <ControlBar
        symbol={status?.symbol ?? "^NSEI"}
        running={status?.running ?? false}
        connection={connection}
        lastPrice={lastPrice}
        busy={busy}
        onStart={handleStart}
        onStop={handleStop}
        onFlatten={handleFlatten}
      />

      <div className="mt-6 flex items-center justify-between">
        <h2 className="text-sm text-ink-dim">engines</h2>
        <MacroRegimeBadge regime={regime} />
      </div>

      <div className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {engineNames.map((name) => (
          <EnginePanel key={name} name={name} position={positions[name] ?? null} />
        ))}
      </div>

      <div className="mt-8">
        <h2 className="text-sm text-ink-dim">combined realized P&amp;L</h2>
        <div className="mt-2 rounded border border-line bg-surface-1 p-4">
          <EquitySparkline values={equitySeries} />
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-sm text-ink-dim">trade blotter</h2>
        <div className="mt-2 rounded border border-line bg-surface-1 p-4">
          <BlotterFeed fills={fills} />
        </div>
      </div>
    </main>
  );
}
