"use client";

import { useCallback, useEffect, useRef, useState } from "react";
const POLL_INTERVAL_MS = 2000;
const MAX_FILLS = 50;
const MAX_EQUITY_POINTS = 200;

export default function Dashboard() {
  const [status, setStatus] = useState<DemoStatus | null>(null);
   return (
    <main className="mx-auto max-w-5xl px-6 py-8">
      Hello
    </main>
  );
}
