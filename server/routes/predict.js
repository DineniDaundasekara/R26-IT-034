const express = require("express");
const router = express.Router();
const fs = require("fs");
const path = require("path");
const Prediction = require("../models/Prediction");

const modelPath = path.join(__dirname, "../model/final_model.json");
const modelData = JSON.parse(fs.readFileSync(modelPath, "utf-8"));

function getLevel(score) {
  if (score < 2.5) return "Low";
  if (score < 3.5) return "Medium";
  return "High";
}

router.post("/", async (req, res) => {
  try {
    const inputData = req.body;

    const { intercept, coefficients, feature_names } = modelData;

    let score = intercept;

    feature_names.forEach((feature, index) => {
      const value = Number(inputData[feature] || 0);
      score += value * coefficients[index];
    });

    const level = getLevel(score);

    const saved = await Prediction.create({
      inputs: inputData,
      predictedScore: score,
      level
    });

    res.json({
      predictedScore: Number(score.toFixed(2)),
      level,
      savedId: saved._id
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Prediction failed" });
  }
});

module.exports = router;