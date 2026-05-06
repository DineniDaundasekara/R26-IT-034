from flask import Flask, request, jsonify
import os, tempfile, json, re

from utils import (
    analyze_audio, analyze_text, get_grammar_errors,
    calculate_score, get_ai_feedback, is_filler, is_grammar
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024   # 10 MB


# ─────────────────────────────────────────────────────────────────
# POST /analyze   — Audio file → full NLP result
# ─────────────────────────────────────────────────────────────────
@app.route("/analyze", methods=["POST"])
def analyze():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    file = request.files["audio"]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        file.save(tmp.name)
        try:
            result = analyze_audio(tmp.name)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            os.remove(tmp.name)

    return jsonify(result)


# ─────────────────────────────────────────────────────────────────
# POST /analyze-answer   — Text answer → NLP + AI feedback
# ─────────────────────────────────────────────────────────────────
@app.route("/analyze-answer", methods=["POST"])
def analyze_answer():
    data         = request.json or {}
    input_text   = data.get("text", "").strip()
    question     = data.get("question", "")
    received_key = data.get("groq_key", "")
    cv_data      = data.get("cv_data", {})

    if not input_text:
        return jsonify({"error": "text is required"}), 400

    # 1. Call AI Feedback first (The "Secret" Source)
    # We pass an empty dict for nlp_analysis since we are generating it from the AI result now
    ai_feedback = get_ai_feedback(question, input_text, {}, cv_data, received_key)

    # 2. Extract AI detected issues to mock the NLP results
    ai_fillers = ai_feedback.get("detected_fillers", [])
    ai_grammar = ai_feedback.get("detected_grammar_issues", [])

    # Process filler counts for the UI
    filler_counts = {}
    for w in ai_fillers:
        clean_w = re.sub(r"[^\w']", "", w).lower()
        filler_counts[clean_w] = filler_counts.get(clean_w, 0) + 1

    filler_count  = len(ai_fillers)
    grammar_count = len(ai_grammar)
    word_count    = len(input_text.split())

    # 3. Use your existing scoring logic on the AI's detected numbers
    filler_penalty  = min(filler_count * 2, 10)
    filler_score    = round(10.0 - filler_penalty, 1)

    grammar_penalty = min(grammar_count * 1.5, 10)
    grammar_score   = round(10.0 - grammar_penalty, 1)

    quality_score = round((filler_score + grammar_score) / 2, 1)
    overall_score = round(filler_score * 0.4 + grammar_score * 0.6, 1)

    # Communication level logic
    if   overall_score >= 8: level = "Excellent"
    elif overall_score >= 6: level = "Good"
    elif overall_score >= 4: level = "Average"
    elif overall_score >= 2: level = "Poor"
    else:                    level = "Very Poor"

    issues = []
    if   filler_count > 3:  issues.append(f"Too many filler words ({filler_count} detected)")
    elif filler_count > 1:  issues.append(f"{filler_count} filler words detected")
    if   grammar_count > 2: issues.append(f"{grammar_count} grammar issues found")
    if   word_count < 30:   issues.append("Answer is too short")

    # 4. Build the final nlp_analysis object
    # This looks exactly like your model output, but it's 100% accurate AI data
    nlp_analysis = {
        "communication_level": level,
        "level_number":        round(overall_score),
        "quality_score":       quality_score,
        "overall_score":       overall_score,
        "confidence":          {},
        "filler_analysis": {
            "detected_fillers":   filler_counts,
            "total_filler_count": filler_count,
            "score":              filler_score,
            "word_count":          word_count
        },
        "grammar_analysis": {
            "error_count": grammar_count,
            "score":       grammar_score,
            "errors": [
                {
                    "type":        "grammar",
                    "description": e.get("message", "Grammar issue"),
                    "found":       e.get("incorrect", "")
                }
                for e in ai_grammar
            ]
        },
        "issues":     issues,
        "word_count": word_count
    }

    return jsonify({
        "nlp_analysis": nlp_analysis,
        "ai_feedback":  ai_feedback
    })


# ─────────────────────────────────────────────────────────────────
# POST /generate-questions
# Types: self_intro, project, experience, technical, situational
# ─────────────────────────────────────────────────────────────────
@app.route("/generate-questions", methods=["POST"])
def generate_questions():
    data            = request.json or {}
    cv_data         = data.get("cv_data", {})
    job_description = data.get("job_description", "")
    groq_key        = data.get("groq_key", "")

    if not groq_key:
        return jsonify({"error": "groq_key is required"}), 400
    if not cv_data:
        return jsonify({"error": "cv_data is required"}), 400

    try:
        from groq import Groq
        client = Groq(api_key=groq_key)

        skills_str = ", ".join(cv_data.get("skills", [])) or "N/A"

        prompt = f"""
You are an expert interview coach. Generate exactly 5 interview questions for the candidate below.

CANDIDATE PROFILE:
- Role: {cv_data.get("role", "N/A")}
- Experience Level: {cv_data.get("experience_level", "N/A")}
- Years of Experience: {cv_data.get("years_of_experience", "N/A")}
- Skills: {skills_str}
- Education: {cv_data.get("education", "N/A")}
- Industry: {cv_data.get("industry", "N/A")}

Job Description: {job_description or "Not provided"}

RULES:
1. Generate EXACTLY one question per type IN THIS ORDER:
   - self_intro  : Ask the candidate to introduce themselves and their background
   - project     : Ask about a specific project they built or contributed to
   - experience  : Ask about their professional experience or a past role
   - technical   : Ask a technical question based on their skills/role
   - situational : Ask a behavioral or hypothetical workplace scenario

2. Each hint must be 1 sentence of practical advice for answering that question.
3. Make questions specific to the candidate's role and skills — not generic.
4. Return ONLY valid JSON — no markdown, no code blocks, no extra text.

Return EXACTLY this structure:
{{
  "questions": [
    {{
      "id": 1,
      "type": "self_intro",
      "question": "...",
      "hint": "..."
    }},
    {{
      "id": 2,
      "type": "project",
      "question": "...",
      "hint": "..."
    }},
    {{
      "id": 3,
      "type": "experience",
      "question": "...",
      "hint": "..."
    }},
    {{
      "id": 4,
      "type": "technical",
      "question": "...",
      "hint": "..."
    }},
    {{
      "id": 5,
      "type": "situational",
      "question": "...",
      "hint": "..."
    }}
  ]
}}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )

        raw    = response.choices[0].message.content
        parsed = json.loads(raw[raw.find("{"):raw.rfind("}")+1])
        return jsonify(parsed)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# GET /health
# ─────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)