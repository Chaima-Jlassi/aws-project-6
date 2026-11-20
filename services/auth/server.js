const express = require("express");
const jwt = require("jsonwebtoken");
const { createClient } = require("redis");

const PORT = process.env.PORT || 3000;
// In AWS this value is injected from Secrets Manager by the ECS task definition.
const JWT_SECRET = process.env.JWT_SECRET || "dev-only-secret-change-me";
const REDIS_URL = process.env.REDIS_URL; // e.g. redis://my-cache.xxxxxx.use1.cache.amazonaws.com:6379

// Demo users. Replace with a real user store (RDS/DynamoDB) later.
const USERS = {
  alice: "password123",
  bob: "password456",
};

const app = express();
app.use(express.json());

let redis = null;
async function initRedis() {
  if (!REDIS_URL) {
    console.log("REDIS_URL not set, sessions will not be stored");
    return;
  }
  redis = createClient({ url: REDIS_URL });
  redis.on("error", (err) => console.error("Redis error:", err.message));
  await redis.connect();
  console.log("Connected to Redis");
}

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "auth" });
});

app.post("/auth/login", async (req, res) => {
  const { username, password } = req.body || {};
  if (!username || USERS[username] !== password) {
    return res.status(401).json({ error: "Invalid credentials" });
  }
  const token = jwt.sign({ sub: username }, JWT_SECRET, { expiresIn: "1h" });
  if (redis) {
    await redis.set(`session:${username}`, token, { EX: 3600 });
  }
  res.json({ token });
});

app.post("/auth/verify", async (req, res) => {
  const { token } = req.body || {};
  if (!token) return res.status(400).json({ error: "token is required" });
  try {
    const payload = jwt.verify(token, JWT_SECRET);
    if (redis) {
      const stored = await redis.get(`session:${payload.sub}`);
      if (stored !== token) {
        return res.status(401).json({ valid: false, error: "Session not found" });
      }
    }
    res.json({ valid: true, user: payload.sub });
  } catch (err) {
    res.status(401).json({ valid: false, error: "Invalid or expired token" });
  }
});

initRedis()
  .catch((err) => console.error("Redis init failed:", err.message))
  .finally(() => {
    app.listen(PORT, () => console.log(`auth service listening on ${PORT}`));
  });
