const express = require("express");
const axios = require("axios");

const router = express.Router();

router.post("/predict", async (req, res) => {
  try {
    const response = await axios.post(
      "http://127.0.0.1:8000/predict",
      req.body
    );

    res.status(200).json(response.data);
  } catch (error) {
    console.error("Prediction error:", error.message);

    res.status(500).json({
      message: "Prediction failed",
      error: error.message,
    });
  }
});

module.exports = router;