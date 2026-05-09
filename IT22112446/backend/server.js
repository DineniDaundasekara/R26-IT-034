const express = require("express");
const mongoose = require("mongoose");
const cors = require("cors");
require("dotenv").config();

const analyzeRoutes = require("./routes/analyzeRoutes");

const app = express();

app.use(cors());
app.use(express.json({ limit: "50mb" }));
app.use(express.urlencoded({ extended: true }));

// Test route
app.get("/", (req, res) => {
  res.json({
    success: true,
    message: "Interview Readiness Backend Running Successfully"
  });
});

// API routes
app.use("/api/analyze", analyzeRoutes);

const PORT = process.env.PORT || 5000;
const MONGO_URI = process.env.MONGO_URI;
const NO_DB = String(process.env.NO_DB || "").trim() === "1";

if (NO_DB) {
  console.log("NO_DB=1 enabled. Starting backend without MongoDB.");
  app.listen(PORT, () => {
    console.log(`Backend running on http://localhost:${PORT}`);
  });
  return;
}

if (!MONGO_URI) {
  console.error("MONGO_URI is missing in .env file (or set NO_DB=1)");
  process.exit(1);
}

mongoose
  .connect(MONGO_URI)
  .then(() => {
    console.log("MongoDB connected successfully");

    app.listen(PORT, () => {
      console.log(`Backend running on http://localhost:${PORT}`);
    });
  })
  .catch((error) => {
    console.error("MongoDB connection failed:");
    console.error(error.message);
    console.error("");
    console.error("Quick fixes to make MongoDB connect:");
    console.error("- Ensure Atlas Network Access allows your IP (or temporary 0.0.0.0/0 for demo).");
    console.error("- Ensure your Atlas cluster is running and reachable from this network.");
    console.error("- Ensure URI includes a database name, e.g. ...mongodb.net/interview?retryWrites=true&w=majority");
    console.error("- If your college Wi-Fi blocks SRV/DNS, try mobile hotspot or use local MongoDB:");
    console.error("  MONGO_URI=mongodb://127.0.0.1:27017/interview");
    process.exit(1);
  });