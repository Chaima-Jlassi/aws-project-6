const express = require("express");

const PORT = process.env.PORT || 3000;

const app = express();
app.use(express.json());

// Keeps the last 100 notifications in memory. In a real system this service
// would publish to SNS/SES; logging to stdout lands in CloudWatch Logs on ECS.
const notifications = [];

app.get("/health", (_req, res) => {
  res.json({ status: "ok", service: "notifications" });
});

app.post("/notify", (req, res) => {
  const { user, message } = req.body || {};
  if (!user || !message) {
    return res.status(400).json({ error: "user and message are required" });
  }
  const entry = { user, message, sentAt: new Date().toISOString() };
  notifications.push(entry);
  if (notifications.length > 100) notifications.shift();
  console.log(JSON.stringify({ event: "notification", ...entry }));
  res.status(202).json(entry);
});

app.get("/notifications", (_req, res) => {
  res.json(notifications);
});

app.listen(PORT, () => console.log(`notifications service listening on ${PORT}`));
