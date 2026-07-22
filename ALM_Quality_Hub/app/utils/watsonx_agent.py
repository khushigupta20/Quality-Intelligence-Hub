"""
IBM watsonx.ai agent — text generation and embedding calls
for the Defect RCA section of the Quality Intelligence Hub.

Authentication (in priority order):
  1. WATSONX_TOKEN      — watsonx Orchestrate Bearer token
  2. WATSONX_API_KEY    — IBM Cloud IAM API key (direct watsonx.ai)

Required alongside either key:
  WATSONX_PROJECT_ID   — watsonx.ai project ID

Optional overrides:
  WATSONX_MODEL_ID     — text-generation model  (default: ibm/granite-3-8b-instruct)
  WATSONX_EMBED_MODEL  — embedding model         (default: ibm/slate-125m-english-rtrvr)
  WATSONX_URL          — service URL             (default: https://us-south.ml.cloud.ibm.com)

All public functions return graceful error dicts on failure so callers
can fall back to existing rule-based output without crashing.
"""

import os
import logging

logger = logging.getLogger(__name__)

_DEFAULT_URL         = "https://us-south.ml.cloud.ibm.com"
_DEFAULT_MODEL_ID    = "ibm/granite-3-8b-instruct"
_DEFAULT_EMBED_MODEL = "ibm/slate-125m-english-rtrvr"


# ── Configuration check ───────────────────────────────────────────────────────

def is_configured(watsonx_api_key: str, watsonx_project_id: str) -> bool:
    """Return True only when both a non-blank API key and project ID are provided."""
    return bool(
        watsonx_api_key   and watsonx_api_key.strip() and
        watsonx_project_id and watsonx_project_id.strip()
    )


# ── Low-level model builder ───────────────────────────────────────────────────

def _get_credentials(watsonx_api_key: str):
    """Build a watsonx Credentials object from an IAM API key."""
    from ibm_watsonx_ai import Credentials
    url = os.environ.get("WATSONX_URL", _DEFAULT_URL)
    return Credentials(url=url, api_key=watsonx_api_key)


def _make_model(watsonx_api_key: str, watsonx_project_id: str,
                watsonx_model_id: str = ""):
    """Instantiate a watsonx.ai ModelInference object for text generation."""
    from ibm_watsonx_ai.foundation_models import ModelInference
    model_id = (watsonx_model_id or _DEFAULT_MODEL_ID).strip()
    credentials = _get_credentials(watsonx_api_key)
    return ModelInference(
        model_id=model_id,
        credentials=credentials,
        project_id=watsonx_project_id,
    )


# ── Text generation ───────────────────────────────────────────────────────────

def generate_text(prompt: str, watsonx_api_key: str, watsonx_project_id: str,
                  watsonx_model_id: str = "") -> dict:
    """
    Generate text from the configured watsonx model.

    Returns:
        {"text": <generated string>}   on success
        {"error": <message>}           on failure
    """
    try:
        model = _make_model(watsonx_api_key, watsonx_project_id, watsonx_model_id)
        messages = [{"role": "user", "content": prompt}]
        response = model.chat(messages=messages)
        text = response["choices"][0]["message"]["content"]
        return {"text": text.strip()}
    except Exception as exc:
        logger.warning("generate_text failed: %s", exc)
        return {"error": str(exc)}


# ── Embeddings ────────────────────────────────────────────────────────────────

def get_embeddings(texts: list, watsonx_api_key: str,
                   watsonx_project_id: str) -> dict:
    """
    Get sentence embeddings for a list of strings using watsonx embed API.

    Returns:
        {"embeddings": [[float, ...], ...]}   on success
        {"error": <message>}                  on failure
    """
    try:
        from ibm_watsonx_ai.foundation_models import Embeddings
        embed_model = os.environ.get("WATSONX_EMBED_MODEL", _DEFAULT_EMBED_MODEL)
        credentials = _get_credentials(watsonx_api_key)
        embedder = Embeddings(
            model_id=embed_model,
            credentials=credentials,
            project_id=watsonx_project_id,
        )
        result = embedder.embed_documents(texts=texts)
        # result is a list of embedding vectors
        if isinstance(result, list):
            return {"embeddings": result}
        return {"error": f"Unexpected embedding response shape: {type(result)}"}
    except Exception as exc:
        logger.warning("get_embeddings failed: %s", exc)
        return {"error": str(exc)}


# ── Defect RCA — high-level helpers ──────────────────────────────────────────

def generate_five_whys(category: str, summaries: list,
                       watsonx_api_key: str, watsonx_project_id: str,
                       watsonx_model_id: str = "") -> dict:
    """
    Generate a 5-Whys analysis for a defect category using the actual
    defect summaries as context.

    Returns a dict with keys why1..why5, answer1..answer5, root_cause
    on success, or {"error": ...} on failure.
    """
    summaries_text = "\n".join(f"- {s}" for s in summaries[:10]) if summaries else "(no summaries provided)"

    prompt = f"""You are a software QA expert performing a Root Cause Analysis.

Category: {category}

Defect summaries from this category:
{summaries_text}

Perform a 5-Whys analysis. Respond ONLY with valid JSON in exactly this format:
{{
  "why1": "Why question 1?",
  "answer1": "Answer to why 1",
  "why2": "Why question 2?",
  "answer2": "Answer to why 2",
  "why3": "Why question 3?",
  "answer3": "Answer to why 3",
  "why4": "Why question 4?",
  "answer4": "Answer to why 4",
  "why5": "Why question 5?",
  "answer5": "Answer to why 5",
  "root_cause": "The single root cause statement"
}}"""

    result = generate_text(prompt, watsonx_api_key, watsonx_project_id, watsonx_model_id)
    if "error" in result:
        return result

    import json, re
    text = result["text"]
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.startswith("```")
        ).strip()
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return {"error": "LLM did not return valid JSON for 5-Whys"}
    try:
        parsed = json.loads(match.group())
        required = [f"why{i}" for i in range(1, 6)] + \
                   [f"answer{i}" for i in range(1, 6)] + ["root_cause"]
        if all(k in parsed for k in required):
            return parsed
        return {"error": "LLM JSON missing required 5-Whys keys"}
    except json.JSONDecodeError as exc:
        return {"error": f"JSON parse error: {exc}"}


def generate_measures(category: str, summaries: list, modules: list,
                      watsonx_api_key: str, watsonx_project_id: str,
                      watsonx_model_id: str = "") -> dict:
    """
    Generate preventive measures for a defect category using the actual
    defect summaries and affected modules as context.

    Returns:
        {"immediate": [...], "long_term": [...]}   on success
        {"error": <message>}                       on failure
    """
    summaries_text = "\n".join(f"- {s}" for s in summaries[:10]) if summaries else "(none)"
    modules_text   = ", ".join(modules) if modules else "unspecified"

    prompt = f"""You are a software QA expert. Based on the defect category and actual defect descriptions below, suggest targeted preventive measures.

Category: {category}
Affected modules: {modules_text}

Defect summaries:
{summaries_text}

Respond ONLY with valid JSON in exactly this format:
{{
  "immediate": [
    "Immediate action 1",
    "Immediate action 2",
    "Immediate action 3"
  ],
  "long_term": [
    "Long-term prevention 1",
    "Long-term prevention 2",
    "Long-term prevention 3"
  ]
}}"""

    result = generate_text(prompt, watsonx_api_key, watsonx_project_id, watsonx_model_id)
    if "error" in result:
        return result

    import json, re
    text  = result["text"]
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.startswith("```")
        ).strip()
    match = re.search(r'\{[\s\S]*\}', text)
    if not match:
        return {"error": "LLM did not return valid JSON for measures"}
    try:
        parsed = json.loads(match.group())
        if "immediate" in parsed and "long_term" in parsed:
            return parsed
        return {"error": "LLM JSON missing immediate/long_term keys"}
    except json.JSONDecodeError as exc:
        return {"error": f"JSON parse error: {exc}"}


def suggest_root_cause(defect_summary: str, severity: str, module: str,
                       watsonx_api_key: str, watsonx_project_id: str,
                       watsonx_model_id: str = "") -> dict:
    """
    Suggest a probable root cause for a single defect.

    Returns:
        {"suggestion": <1-2 sentence string>}   on success
        {"error": <message>}                    on failure
    """
    prompt = f"""You are a software QA expert. Given this defect, suggest the most probable root cause in 1-2 sentences. Be specific and technical.

Defect Summary: {defect_summary}
Severity: {severity}
Module: {module}

Root cause suggestion:"""

    result = generate_text(prompt, watsonx_api_key, watsonx_project_id, watsonx_model_id)
    if "error" in result:
        return result
    text = result["text"].strip()
    sentences = text.split(". ")
    short = ". ".join(sentences[:2]).strip()
    if short and not short.endswith("."):
        short += "."
    return {"suggestion": short or text}


def generate_executive_summary(total: int, open_: int, closed: int,
                                crit: int, top_modules: list,
                                pattern_names: list,
                                watsonx_api_key: str,
                                watsonx_project_id: str,
                                watsonx_model_id: str = "") -> dict:
    """
    Generate a 3-4 sentence executive summary paragraph for the PDF report.

    Returns:
        {"summary": <string>}   on success
        {"error": <message>}    on failure
    """
    modules_text  = ", ".join(top_modules[:3])  if top_modules  else "various modules"
    patterns_text = ", ".join(pattern_names[:4]) if pattern_names else "several areas"

    prompt = f"""You are a software quality manager writing an executive summary for a defect RCA report.

Dataset statistics:
- Total defects: {total}
- Open: {open_}
- Closed: {closed}
- Critical/High severity: {crit}
- Most affected modules: {modules_text}
- Detected patterns: {patterns_text}

Write a professional 3-4 sentence executive summary paragraph that describes the quality situation, highlights the most important findings, and mentions the key areas requiring attention. Be concise and factual.

Executive Summary:"""

    result = generate_text(prompt, watsonx_api_key, watsonx_project_id, watsonx_model_id)
    if "error" in result:
        return result
    return {"summary": result["text"].strip()}


def cluster_defects(summaries: list, watsonx_api_key: str,
                    watsonx_project_id: str,
                    threshold: float = 0.72) -> dict:
    """
    Group a list of defect summary strings by semantic similarity using
    watsonx sentence embeddings (cosine similarity).

    Returns:
        {"groups": {group_id: [idx, ...], ...}}   on success
        {"error": <message>}                       on failure
    """
    if not summaries:
        return {"error": "No summaries provided"}

    result = get_embeddings(summaries, watsonx_api_key, watsonx_project_id)
    if "error" in result:
        return result

    embeddings = result["embeddings"]

    if not embeddings or not isinstance(embeddings[0], (list, tuple)):
        return {"error": "Unexpected embedding shape from watsonx API"}

    import math

    def cosine(a, b):
        dot    = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    n      = len(embeddings)
    labels = [-1] * n
    next_group = 0

    for i in range(n):
        if labels[i] != -1:
            continue
        labels[i] = next_group
        for j in range(i + 1, n):
            if labels[j] == -1:
                sim = cosine(embeddings[i], embeddings[j])
                if sim >= threshold:
                    labels[j] = next_group
        next_group += 1

    groups: dict = {}
    for idx, gid in enumerate(labels):
        groups.setdefault(gid, []).append(idx)

    return {"groups": groups}
