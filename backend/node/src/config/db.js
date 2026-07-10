const mongoose = require('mongoose');

const connectDB = async () => {
  mongoose.set('bufferCommands', false);
  const mongoURI = process.env.MONGODB_URI || 'mongodb://127.0.0.1:27017/veritas_ai';
  try {
    const conn = await mongoose.connect(mongoURI, {
      serverSelectionTimeoutMS: 2000
    });
    console.log(`[MongoDB] Connected successfully to: ${conn.connection.host}/${conn.connection.name}`);
  } catch (err) {
    console.warn(`[MongoDB] Warning: Direct MongoDB connection failed (${err.message}). Using fallback persistence.`);
  }
};


module.exports = connectDB;
