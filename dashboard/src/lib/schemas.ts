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

export const macroRegimeSchema = z.object({
  regime: z.enum(["calm", "elevated", "crisis"]),
  trading_halted: z.boolean(),
  spacing_multiplier: z.number(),
  size_multiplier: z.number(),
});

export const blotterRowSchema = z.object({
  timestamp: z.string(),
  side: z.enum(["long", "short"]),
  price: z.number(),
  quantity: z.number(),
});

export const blotterSchema = z.record(z.string(), z.array(blotterRowSchema));

export const tickEventSchema = z.object({
  type: z.literal("tick"),
  symbol: z.string(),
  price: z.number(),
});

export const fillEventSchema = z.object({
  type: z.literal("fill"),
  engine: z.string(),
  symbol: z.string(),
  side: z.enum(["long", "short"]),
  price: z.number(),
  quantity: z.number(),
});

export const liveEventSchema = z.discriminatedUnion("type", [tickEventSchema, fillEventSchema]);

export type Position = z.infer<typeof positionSchema>;
export type Positions = z.infer<typeof positionsSchema>;
export type DemoStatus = z.infer<typeof demoStatusSchema>;
export type MacroRegime = z.infer<typeof macroRegimeSchema>;
export type BlotterRow = z.infer<typeof blotterRowSchema>;
export type Blotter = z.infer<typeof blotterSchema>;
export type TickEvent = z.infer<typeof tickEventSchema>;
export type FillEvent = z.infer<typeof fillEventSchema>;
export type LiveEvent = z.infer<typeof liveEventSchema>;
