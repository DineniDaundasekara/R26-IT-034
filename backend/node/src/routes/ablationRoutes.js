const express = require('express');
const router = express.Router();
const AIServiceClient = require('../services/aiServiceClient');

// Get ablation study results
router.get('/', async (req, res) => {
  try {
    const metrics = await AIServiceClient.getAblationMetrics();
    return res.status(200).json(metrics);
  } catch (err) {
    return res.status(500).json({ error: 'Failed to fetch ablation metrics', message: err.message });
  }
});

module.exports = router;
