const mongoose = require("mongoose");

const predictionSchema = new mongoose.Schema({
  inputs: Object,
  predictedScore: Number,
  level: String,
  createdAt: {
    type: Date,
    default: Date.now
  }
});

module.exports = mongoose.model("Prediction", predictionSchema);