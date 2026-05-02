const express = require("express");
const cors = require("cors");
require("dotenv").config();

const predictRoute = require("./routes/predict");

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api/predict", predictRoute);

// TEMPORARILY DISABLED MONGODB
// const mongoose = require("mongoose");
// mongoose.connect(process.env.MONGO_URI)
//   .then(() => console.log("MongoDB connected"))
//   .catch(err => console.error(err));

app.listen(5000, () => {
  console.log("Server running on port 5000");
});