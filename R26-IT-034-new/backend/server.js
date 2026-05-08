const express = require("express");
const cors = require("cors");
require("dotenv").config();

const predictionRoute = require("./routes/predictionRoute");

const app = express();

app.use(cors());
app.use(express.json());

app.use("/api", predictionRoute);

app.get("/", (req, res) => {
  res.send("MERN backend running");
});

const PORT = process.env.PORT || 5000;

app.listen(PORT, () => {
  console.log(`Backend server running on port ${PORT}`);
});