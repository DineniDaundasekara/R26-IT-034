require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const multer = require('multer');
const axios = require('axios');
const fs = require('fs');
const FormData = require('form-data');
const Candidate = require('./models/Candidate');
const path = require('path');

const app = express();
app.use(cors());
app.use(express.json());

// Set up temporary upload directory if it doesn't exist
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

const upload = multer({ dest: 'uploads/' });

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/aihiring')
  .then(() => console.log('MongoDB Connected'))
  .catch(err => console.log('MongoDB Connection Error:', err));

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';

app.post('/api/candidates/evaluate', upload.single('resume'), async (req, res) => {
  try {
    const { name, email, github_username } = req.body;
    
    if (!req.file || !github_username) {
      if (req.file) fs.unlinkSync(req.file.path);
      return res.status(400).json({ error: 'Missing resume or github username' });
    }

    // Pass data to Python FastAPI microservice
    const form = new FormData();
    form.append('github_username', github_username);
    form.append('resume', fs.createReadStream(req.file.path), req.file.originalname);

    const aiResponse = await axios.post(`${FASTAPI_URL}/analyze_candidate`, form, {
      headers: {
        ...form.getHeaders()
      }
    });

    const aiData = aiResponse.data;

    // Save to Database
    const newCandidate = new Candidate({
      name,
      email,
      github_username,
      trust_score: aiData.trust_score,
      risk_category: aiData.risk_category,
      extracted_features: aiData.candidate,
      explanations: aiData.explanations
    });

    await newCandidate.save();

    // Clean up temp file
    fs.unlinkSync(req.file.path);

    res.status(201).json(newCandidate);
  } catch (error) {
    console.error('Error evaluating candidate:', error.message);
    if (req.file && fs.existsSync(req.file.path)) {
      fs.unlinkSync(req.file.path);
    }
    res.status(500).json({ error: 'Failed to process candidate.' });
  }
});

app.get('/api/candidates', async (req, res) => {
  try {
    const candidates = await Candidate.find().sort({ createdAt: -1 });
    res.json(candidates);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch candidates.' });
  }
});

const PORT = process.env.PORT || 5001;
app.listen(PORT, () => {
  console.log(`Node Server running on port ${PORT}`);
});
