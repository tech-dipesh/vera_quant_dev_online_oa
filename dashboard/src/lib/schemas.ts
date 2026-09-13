import { z } from "zod";

export const positionSchema = z.object({
  symbol: z.string(),
  side: z.enum(["long", "short"]).nullable(),
  quantity: z.number(),
  average_price: z.number(),
  realized_pnl: z.number(),
});

export const positionsSchema = z.record(z.string(), positionSchema);

export const demoStatusSchema = z.object({
  running: z.boolean(),
  symbol: z.string(),
  engines: z.array(z.string()),
});

export const flattenResultSchema = z.object({
  closed: z.number(),
});
