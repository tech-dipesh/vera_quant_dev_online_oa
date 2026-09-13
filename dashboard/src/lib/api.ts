import {
  blotterSchema,
  demoStatusSchema,
  flattenResultSchema,
  macroRegimeSchema,
  positionsSchema,
} from "@/lib/schemas";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, schema: { parse: (data: unknown) => T }, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    throw new Error(`${path} failed with status ${response.status}`);
  }
  const data = await response.json();
  return schema.parse(data);
}

export function startDemo() {
  return request("/demo/start", demoStatusSchema, { method: "POST" });
}

export function stopDemo() {
  return request("/demo/stop", demoStatusSchema, { method: "POST" });
}

export function flattenDemo() {
  return request("/demo/flatten", flattenResultSchema, { method: "POST" });
}

export function fetchDemoStatus() {
  return request("/demo/status", demoStatusSchema);
}

export function fetchPositions() {
  return request("/positions", positionsSchema);
}

export function fetchBlotter() {
  return request("/blotter", blotterSchema);
}

export function fetchMacroRegime() {
  return request("/macro-regime", macroRegimeSchema);
}

export function liveFeedUrl(): string {
  const base = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws/live";
  return base;
}
