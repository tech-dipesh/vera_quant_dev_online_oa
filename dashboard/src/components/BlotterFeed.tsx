import type { FillEvent } from "@/lib/schemas";

export function BlotterFeed({ fills }: { fills: FillEvent[] }) {
  if (fills.length === 0) {
    return <div className="py-6 text-center text-sm text-ink-dim">no fills yet</div>;
  }

  return (
    <div className="max-h-64 overflow-y-auto font-mono text-sm">
      <table className="w-full">
        <thead className="sticky top-0 bg-surface-1 text-xs text-ink-dim">
          <tr>
            <th className="py-1 text-left font-normal">time</th>
            <th className="py-1 text-left font-normal">engine</th>
            <th className="py-1 text-left font-normal">side</th>
            <th className="py-1 text-right font-normal">price</th>
            <th className="py-1 text-right font-normal">qty</th>
          </tr>
        </thead>
        <tbody>
          {fills.map((fill, index) => (
            <tr key={`${fill.engine}-${index}`} className="border-t border-line">
              <td className="py-1 text-ink-dim">
                {new Date().toLocaleTimeString(undefined, { hour12: false })}
              </td>
              <td className="py-1">{fill.engine.replace(/_/g, " ")}</td>
              <td className={`py-1 ${fill.side === "long" ? "text-long" : "text-short"}`}>
                {fill.side.toUpperCase()}
              </td>
              <td className="py-1 text-right">{fill.price.toFixed(2)}</td>
              <td className="py-1 text-right">{fill.quantity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
