import type { MacroRegime } from "@/lib/schemas";
import { StatusDot } from "@/components/StatusDot";

const toneByRegime = {
  calm: "live",
  elevated: "warn",
  crisis: "danger",
} as const;

export function MacroRegimeBadge({ regime }: { regime: MacroRegime | null }) {
  if (!regime) {
    return (
      <div className="flex items-center gap-2 rounded border border-line px-3 py-1.5 text-sm text-ink-dim">
        <StatusDot tone="idle" />
        macro regime unknown
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 rounded border border-line px-3 py-1.5 text-sm">
      <StatusDot tone={toneByRegime[regime.regime]} />
      <span className="font-mono uppercase tracking-wide">{regime.regime}</span>
      {regime.trading_halted && <span className="text-short">trading halted</span>}
    </div>
  );
}
