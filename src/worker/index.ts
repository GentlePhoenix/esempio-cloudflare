import { Hono } from "hono";

const app = new Hono<{ Bindings: Env }>();

// Health check
app.get("/api/health", (c) => {
  return c.json({ status: "ok" });
});

// Test D1 connection
app.get("/api/questions/count", async (c) => {
  try {
    
    return c.json({ count: 42});
  } catch (error) {
    return c.json({ error: "Database not initialized" }, 500);
  }
});

export default app;
