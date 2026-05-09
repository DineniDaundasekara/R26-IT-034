const mongoose = require("mongoose");

const AnalysisResultSchema = new mongoose.Schema(
  {
    inputType: {
      type: String,
      enum: ["text", "audio"],
      required: true
    },
    jobRole: { type: String, default: "" },
    jobDescription: { type: String, default: "" },
    question: { type: String, default: "" },
    transcript: { type: String, required: true },
    communicationSkillLevel: { type: String, default: "" },
    predictedLevel: { type: Number, default: 0 },
    feedback: { type: String, default: "" },
    strengths: { type: [String], default: [] },
    weaknesses: { type: [String], default: [] },
    suggestions: { type: [String], default: [] },
    betterAnswerExample: { type: String, default: "" },
    meta: { type: Object, default: {} }
  },
  { timestamps: true }
);

module.exports = mongoose.model("AnalysisResult", AnalysisResultSchema);
