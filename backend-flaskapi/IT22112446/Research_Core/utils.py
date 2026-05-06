import torch
import whisper
import language_tool_python
from transformers import DistilBertForTokenClassification, DistilBertTokenizerFast
from groq import Groq
import json
import re

# ─────────────────────────────────────────────
# Load models ONCE at startup
# ─────────────────────────────────────────────
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

whisper_model = whisper.load_model("base")

tokenizer = DistilBertTokenizerFast.from_pretrained("model/")
ner_model = DistilBertForTokenClassification.from_pretrained("model/").to(device)
ner_model.eval()

grammar_tool = language_tool_python.LanguageTool('en-US')

TAG2ID = ner_model.config.label2id
ID2TAG = ner_model.config.id2label


# ─────────────────────────────────────────────
# 🔹 Text pre-processing
# "uh,"  → "uh"
# "like." → "like"
# Training data had clean tokens — real speech has punctuation attached
# ─────────────────────────────────────────────
def clean_token(word: str) -> str:
    """Strip punctuation, lowercase — matches training data format."""
    return re.sub(r"[^\w']", "", word).lower()


def preprocess_tokens(text: str):
    """
    Returns:
        raw_tokens   — original words (for display in frontend)
        clean_tokens — punctuation-stripped lowercase (fed to NER model)
    """
    raw_tokens   = text.split()
    clean_tokens = [clean_token(t) or t for t in raw_tokens]
    return raw_tokens, clean_tokens


# ─────────────────────────────────────────────
# 🔹 NER Prediction
# Fixes applied:
#   1. Feed clean tokens (no punctuation) to model
#   2. word_ids(batch_index=0) explicit
#   3. seen set — one tag per word (first subtoken only)
# ─────────────────────────────────────────────
def analyze_text(text: str) -> list:
    raw_tokens, clean_tokens = preprocess_tokens(text)
    if not clean_tokens:
        return []

    inputs = tokenizer(
        clean_tokens,
        is_split_into_words=True,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    ).to(device)

    with torch.no_grad():
        outputs = ner_model(**inputs)
        preds   = torch.argmax(outputs.logits, dim=2)

    word_ids = inputs.word_ids(batch_index=0)

    seen    = set()
    results = []
    for i, word_id in enumerate(word_ids):
        if word_id is None or word_id in seen:
            continue
        seen.add(word_id)

        label = ID2TAG[preds[0][i].item()]
        word  = raw_tokens[word_id]   # show original (with punctuation) in UI
        results.append({"word": word, "tag": label})

    return results


# ─────────────────────────────────────────────
# 🔹 Label helpers
# ─────────────────────────────────────────────
def is_filler(tag: str) -> bool:
    return tag in ("B-FILL", "I-FILL")

def is_grammar(tag: str) -> bool:
    return tag.startswith("B-GRAM") or tag.startswith("I-GRAM")


# ─────────────────────────────────────────────
# 🔹 Grammar Errors  (LanguageTool)
# ─────────────────────────────────────────────
def get_grammar_errors(text: str) -> list:
    matches = grammar_tool.check(text)
    errors  = []
    for match in matches:
        err_len = getattr(match, 'errorLength', getattr(match, 'length', 0))
        errors.append({
            "message":     match.message,
            "incorrect":   text[match.offset: match.offset + err_len],
            "suggestions": match.replacements[:3],
            "start":       match.offset,
            "end":         match.offset + err_len
        })
    return errors


# ─────────────────────────────────────────────
# 🔹 Score Calculation  (used by audio pipeline)
# ─────────────────────────────────────────────
def calculate_score(predictions: list, grammar_errors: list) -> int:
    filler  = sum(1 for p in predictions if is_filler(p["tag"]))
    grammar = len(grammar_errors)
    score   = 100 - (filler * 2 + grammar * 5)
    return max(score, 0)


# ─────────────────────────────────────────────
# 🔹 AI Feedback  (Groq / LLaMA)
# ─────────────────────────────────────────────
def get_ai_feedback(question: str, answer: str, nlp_results: dict,
                    cv_data: dict, groq_key: str) -> dict:

    _fallback = {
        "overall_feedback": "Analysis could not be completed at this time.",
        "strengths": ["Answer was provided"],
        "improvements": ["Please try again for detailed feedback"],
        "better_version": answer or "",
        "tip": "Practice speaking clearly and concisely.",
        "detected_fillers": [],
        "detected_grammar_issues": []
    }

    if not groq_key:
        return _fallback

    try:
        client = Groq(api_key=groq_key)

        prompt = f"""
You are an expert interview coach and NLP analyzer. Analyze this interview answer.
Return ONLY a valid JSON object.

Question: "{question}"
Candidate Answer: "{answer}"

Return EXACTLY this JSON structure:
{{
  "detected_fillers": ["list", "of", "every", "filler", "word", "found"],
  "detected_grammar_issues": [
    {{"incorrect": "wrong text", "message": "explanation of error"}}
  ],
  "overall_feedback": "2-3 sentence honest overall assessment",
  "strengths": ["strength 1", "strength 2"],
  "improvements": ["improvement 1", "improvement 2", "improvement 3"],
  "better_version": "A rewritten, improved version of the answer",
  "tip": "One specific actionable tip"
}}
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        raw = response.choices[0].message.content
        cleaned = raw[raw.find("{"):raw.rfind("}")+1]
        return json.loads(cleaned)

    except Exception:
        return _fallback


# ─────────────────────────────────────────────
# 🔹 Full Audio Pipeline
# ─────────────────────────────────────────────
def analyze_audio(file_path: str) -> dict:
    result = whisper_model.transcribe(file_path)
    text   = result["text"]

    predictions    = analyze_text(text)
    grammar_errors = get_grammar_errors(text)
    score          = calculate_score(predictions, grammar_errors)

    return {
        "text":           text,
        "tokens":         predictions,
        "grammar_errors": grammar_errors,
        "score":          score
    }

