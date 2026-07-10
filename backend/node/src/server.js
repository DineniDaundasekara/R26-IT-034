require('dotenv').config();
const express = require('express');
const cors = require('cors');
const connectDB = require('./config/db');

const candidateRoutes = require('./routes/candidateRoutes');
const roleRoutes = require('./routes/roleRoutes');
const ablationRoutes = require('./routes/ablationRoutes');

const app = express();
const PORT = process.env.PORT || 5001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Connect to MongoDB
connectDB();

// API Routes
app.use('/api/candidates', candidateRoutes);
app.use('/api/roles', roleRoutes);
app.use('/api/ablation', ablationRoutes);

// Health Check
app.get('/api/health', (req, res) => {
  res.status(200).json({
    status: 'healthy',
    service: 'Technical Candidate Assessment Express Backend',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`[Express Node Backend] Server running on http://127.0.0.1:${PORT}`);
});
