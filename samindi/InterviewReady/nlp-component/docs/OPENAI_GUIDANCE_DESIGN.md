# Grounded Generative Guidance Design

## Research concept

The OpenAI model is a **Guidance Realizer/Coach**, not the communication classifier.

```text
Saved ML classifier → communication level
Deterministic evidence engine → observable evidence
OpenAI Responses API → personalised wording + practice guidance
```

This separation makes the contribution explainable:

- If OpenAI is disabled, the communication category still works.
- If the generative request fails, deterministic fallback guidance still works.
- The LLM does not have authority to change the ML category.

## Inputs sent to the guidance model

- transcript
- authoritative ML communication level
- target role (optional)
- experience level (optional)
- candidate practice goal (optional)
- deterministic evidence booleans/lists
- deterministic baseline strengths/weaknesses/guidance

Research evaluation metrics and raw candidate-facing numeric feature values are not required for guidance generation.

## Generation guardrails

The system prompt requires:

- no invented projects
- no invented employers
- no invented responsibilities
- no invented technologies
- no invented achievements
- no invented numerical results
- no new communication score
- no confidence percentage
- preserve candidate facts
- use placeholders when a real result is missing
- return structured JSON validated by Pydantic

## Why professional rewrites are useful

The candidate should not receive only abstract advice such as "be more professional". The interface shows reusable structures such as:

```text
My main responsibility was to...
To address this, I...
As a result...
What I learned from this experience was...
```

The candidate learns a speaking pattern and inserts their own factual content.

## Adaptive loop

```text
Attempt 1
  ↓
Category + evidence + coaching plan
  ↓
7-day practice + activities
  ↓
Attempt 2
  ↓
New category + new evidence + new priorities
```

Attempt history records categories and focus areas. It deliberately does not convert these into a fabricated "improvement percentage".


## Two-pass accuracy mode

When `OPENAI_GUIDANCE_VERIFY=true`, the guidance path is:

```text
Evidence-grounded generation
        ↓
Second-pass factual grounding verifier
        ↓
Pydantic schema validation
        ↓
Candidate UI
```

If generation or verification fails, the API falls back to deterministic coaching instead of returning malformed or ungrounded content. This is particularly useful for a research demonstration because the system can explain both its grounding constraint and its failure path.
