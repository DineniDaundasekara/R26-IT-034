const express = require("express");
const multer = require("multer");
const fs = require("fs");
const path = require("path");

const AnalysisResult = require("../schemas/AnalysisResult");
const crypto = require("crypto");

const router = express.Router();

const NO_DB = String(process.env.NO_DB || "").trim() === "1";
const memoryHistory = [];

function nowIso() {
  return new Date().toISOString();
}

function toMemoryDoc(doc) {
  return {
    _id: crypto.randomUUID(),
    ...doc,
    createdAt: nowIso(),
    updatedAt: nowIso()
  };
}

async function saveResult(doc) {
  if (NO_DB) {
    const saved = toMemoryDoc(doc);
    memoryHistory.unshift(saved);
    memoryHistory.splice(25);
    return saved;
  }

  return AnalysisResult.create(doc);
}

async function loadHistory() {
  if (NO_DB) return memoryHistory.slice(0, 25);
  return AnalysisResult.find().sort({ createdAt: -1 }).limit(25);
}

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }
});

function getGroqKey() {
  const key = process.env.GROQ_API_KEY;
  if (!key) {
    const err = new Error("GROQ_API_KEY missing in backend/.env");
    err.statusCode = 500;
    throw err;
  }
  return key;
}

function getFetchAndFormData() {
  // Node 18+ has these globally. Fallback to undici if needed.
  const fetchFn = global.fetch;
  const FormDataCtor = global.FormData;
  const BlobCtor = global.Blob;

  if (fetchFn && FormDataCtor && BlobCtor) {
    return { fetchFn, FormDataCtor, BlobCtor };
  }

  // eslint-disable-next-line global-require
  const undici = require("undici");
  return {
    fetchFn: undici.fetch,
    FormDataCtor: undici.FormData,
    BlobCtor: undici.Blob
  };
}

async function groqTranscribeAudio({ buffer, filename, mimeType }) {
  const { fetchFn, FormDataCtor, BlobCtor } = getFetchAndFormData();
  const apiKey = getGroqKey();

  const form = new FormDataCtor();
  const blob = new BlobCtor([buffer], { type: mimeType || "application/octet-stream" });

  form.append("file", blob, filename || "audio.wav");
  form.append("model", "whisper-large-v3-turbo");
  form.append("response_format", "json");

  const resp = await fetchFn("https://api.groq.com/openai/v1/audio/transcriptions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`
    },
    body: form
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    const err = new Error(`Groq transcription failed (${resp.status}): ${text || resp.statusText}`);
    err.statusCode = 502;
    throw err;
  }

  const json = await resp.json();
  return (json && json.text ? String(json.text) : "").trim();
}

async function groqGenerateFeedback({ transcript, jobRole = "", jobDescription = "", question = "" }) {
  const { fetchFn } = getFetchAndFormData();
  const apiKey = getGroqKey();

  const prompt = `
You are an interview communication coach.

Candidate Job Role Target:
${jobRole || "Not provided"}

Job Description:
${jobDescription || "Not provided"}

Interview Question:
${question || "Tell me about yourself and your skills, experience, and career goals."}

Candidate Transcript:
${transcript}

Return ONLY valid JSON using this exact structure:
{
  "communication_skill_level": "Poor Communication | Average Communication | Good Communication | Excellent Communication",
  "predicted_level": 1,
  "feedback": "one useful feedback paragraph",
  "strengths": ["strength 1", "strength 2"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"],
  "better_answer_example": "a better interview answer example"
}

Rules:
- Do not mention any hidden scoring system.
- Be specific to the transcript.
- Suggestions must improve spoken English, structure, professional wording, confidence, and job-role alignment.
- The better answer example must be based on the same role/project mentioned in the transcript.
`;

  const body = {
    model: "llama-3.3-70b-versatile",
    messages: [
      { role: "system", content: "Return valid JSON only. No markdown. No extra keys." },
      { role: "user", content: prompt }
    ],
    temperature: 0.2,
    response_format: { type: "json_object" }
  };

  const resp = await fetchFn("https://api.groq.com/openai/v1/chat/completions", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  if (!resp.ok) {
    const text = await resp.text().catch(() => "");
    const err = new Error(`Groq feedback failed (${resp.status}): ${text || resp.statusText}`);
    err.statusCode = 502;
    throw err;
  }

  const json = await resp.json();
  const content = json?.choices?.[0]?.message?.content;
  if (!content) {
    const err = new Error("Groq feedback returned empty content");
    err.statusCode = 502;
    throw err;
  }

  let parsed;
  try {
    parsed = JSON.parse(content);
  } catch {
    const err = new Error("Groq feedback returned non-JSON content");
    err.statusCode = 502;
    throw err;
  }

  return {
    communicationSkillLevel: String(parsed.communication_skill_level || ""),
    predictedLevel: Number(parsed.predicted_level || 0),
    feedback: String(parsed.feedback || ""),
    strengths: Array.isArray(parsed.strengths) ? parsed.strengths.map(String) : [],
    weaknesses: Array.isArray(parsed.weaknesses) ? parsed.weaknesses.map(String) : [],
    suggestions: Array.isArray(parsed.suggestions) ? parsed.suggestions.map(String) : [],
    betterAnswerExample: String(parsed.better_answer_example || "")
  };
}

router.get("/test", (req, res) => {
  res.json({ success: true, message: "Analyze route working" });
});

router.get("/training-summary", async (req, res) => {
  try {
    const modelsDir = path.join(__dirname, "..", "models");
    const best = JSON.parse(fs.readFileSync(path.join(modelsDir, "best_model_result.json"), "utf-8"));
    const all = JSON.parse(fs.readFileSync(path.join(modelsDir, "model_results.json"), "utf-8"));

    res.json({
      success: true,
      data: {
        bestModel: best,
        modelResults: all
      }
    });
  } catch (e) {
    res.status(500).json({
      success: false,
      message: "Failed to load training summary",
      error: e?.message || String(e)
    });
  }
});

router.get("/history", async (req, res) => {
  try {
    const items = await loadHistory();
    res.json({ success: true, data: items });
  } catch (e) {
    res.status(500).json({ success: false, message: "Failed to load history", error: e?.message || String(e) });
  }
});

router.post("/text", async (req, res) => {
  try {
    const { transcript, jobRole = "", jobDescription = "", question = "" } = req.body || {};

    const cleanTranscript = String(transcript || "").trim();
    if (!cleanTranscript) {
      return res.status(400).json({ success: false, message: "transcript is required" });
    }

    const fb = await groqGenerateFeedback({ transcript: cleanTranscript, jobRole, jobDescription, question });

    const saved = await saveResult({
      inputType: "text",
      jobRole: String(jobRole || ""),
      jobDescription: String(jobDescription || ""),
      question: String(question || ""),
      transcript: cleanTranscript,
      communicationSkillLevel: fb.communicationSkillLevel,
      predictedLevel: fb.predictedLevel,
      feedback: fb.feedback,
      strengths: fb.strengths,
      weaknesses: fb.weaknesses,
      suggestions: fb.suggestions,
      betterAnswerExample: fb.betterAnswerExample
    });

    return res.json({ success: true, data: saved });
  } catch (e) {
    const code = e?.statusCode || 500;
    return res.status(code).json({ success: false, message: "Text analysis failed", error: e?.message || String(e) });
  }
});

router.post("/audio", upload.single("audio"), async (req, res) => {
  try {
    const file = req.file;
    const jobRole = req.body?.jobRole || "";
    const jobDescription = req.body?.jobDescription || "";
    const question = req.body?.question || "";

    if (!file) {
      return res.status(400).json({ success: false, message: "audio file is required (field name: audio)" });
    }

    const transcript = await groqTranscribeAudio({
      buffer: file.buffer,
      filename: file.originalname,
      mimeType: file.mimetype
    });

    if (!transcript) {
      return res.status(422).json({ success: false, message: "No speech detected in audio" });
    }

    const fb = await groqGenerateFeedback({ transcript, jobRole, jobDescription, question });

    const saved = await saveResult({
      inputType: "audio",
      jobRole: String(jobRole || ""),
      jobDescription: String(jobDescription || ""),
      question: String(question || ""),
      transcript,
      communicationSkillLevel: fb.communicationSkillLevel,
      predictedLevel: fb.predictedLevel,
      feedback: fb.feedback,
      strengths: fb.strengths,
      weaknesses: fb.weaknesses,
      suggestions: fb.suggestions,
      betterAnswerExample: fb.betterAnswerExample,
      meta: {
        originalname: file.originalname,
        mimetype: file.mimetype,
        size: file.size
      }
    });

    return res.json({ success: true, data: saved });
  } catch (e) {
    const code = e?.statusCode || 500;
    return res.status(code).json({ success: false, message: "Audio analysis failed", error: e?.message || String(e) });
  }
});

module.exports = router;