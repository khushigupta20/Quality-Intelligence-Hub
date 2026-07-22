"""
LLM-powered 5-Whys generator — IBM watsonx only.

Two authentication methods are supported, both backed by watsonx.ai:

1. watsonx Orchestrate token  (preferred for IBM employees / internal use)
   ─────────────────────────────────────────────────────────────────────
   WATSONX_TOKEN        Bearer token obtained from watsonx Orchestrate
                        (copy from the Orchestrate UI → Profile → API access)
   WATSONX_PROJECT_ID   watsonx.ai project ID
   WATSONX_URL          (optional) service URL, defaults to Dallas region

2. IBM Cloud IAM API key  (for direct watsonx.ai access)
   ─────────────────────────────────────────────────────────────────────
   WATSONX_API_KEY      IBM Cloud IAM API key
   WATSONX_PROJECT_ID   watsonx.ai project ID
   WATSONX_URL          (optional) service URL, defaults to Dallas region

Both methods also respect:
   WATSONX_MODEL_ID     (optional) model to use, defaults to
                        ibm/granite-3-8b-instruct

If neither credential set is present, or the call fails for any reason,
the function returns None and the caller falls back to static templates.
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

_DEFAULT_URL      = "https://us-south.ml.cloud.ibm.com"
_DEFAULT_MODEL_ID = "ibm/granite-3-8b-instruct"

# ── expected output schema ────────────────────────────────────────────────────
_SCHEMA_KEYS = [
    "why1", "answer1",
    "why2", "answer2",
    "why3", "answer3",
    "why4", "answer4",
    "why5", "answer5",
    "root_cause",
]

_SYSTEM_PROMPT = (
    "You are a senior software quality engineer specialising in Root Cause Analysis (RCA). "
    "Your task is to produce a rigorous, context-specific 5-Whys analysis for a cluster of "
    "software defects. Use the actual defect summaries provided to make each answer concrete "
    "and specific — never generic. "
    "Respond ONLY with a single valid JSON object and no other text."
)

_USER_TEMPLATE = """\
Defect cluster category  : {category}
Number of defects        : {count}
Defect summaries (sample):
{summaries}

Produce a 5-Whys analysis in this exact JSON format:
{{
  "why1": "<first why question>",
  "answer1": "<answer to why1>",
  "why2": "<second why question>",
  "answer2": "<answer to why2>",
  "why3": "<third why question>",
  "answer3": "<answer to why3>",
  "why4": "<fourth why question>",
  "answer4": "<answer to why4>",
  "why5": "<fifth why question>",
  "answer5": "<answer to why5>",
  "root_cause": "<single-sentence root cause statement>"
}}
"""


# ── helpers ───────────────────────────────────────────────────────────────────
def _build_prompt(category: str, defect_summaries: list[str]) -> str:
    sample = "\n".join(f"  - {s[:120]}" for s in defect_summaries[:8])
    return _USER_TEMPLATE.format(
        category=category,
        count=len(defect_summaries),
        summaries=sample,
    )


def _parse_response(text: str) -> dict | None:
    """Extract and validate JSON from LLM response text."""
    text = text.strip()
    # Strip markdown code fences if present
    if text.startswith("```"):
        text = "\n".join(
            line for line in text.splitlines() if not line.startswith("```")
        ).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("LLM 5-Whys: could not parse JSON response")
        return None

    for key in _SCHEMA_KEYS:
        if key not in data or not isinstance(data[key], str) or not data[key].strip():
            logger.warning("LLM 5-Whys: missing or empty key '%s' in response", key)
            return None

    return data


def _make_model(credentials, project_id: str):
    """Instantiate a watsonx.ai ModelInference object."""
    from ibm_watsonx_ai.foundation_models import ModelInference
    return ModelInference(
        model_id=os.environ.get("WATSONX_MODEL_ID", _DEFAULT_MODEL_ID),
        credentials=credentials,
        project_id=project_id,
    )


def _invoke(model, prompt: str) -> dict | None:
    """Call the model and parse the response."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": prompt},
    ]
    response = model.chat(messages=messages)
    text = response["choices"][0]["message"]["content"]
    return _parse_response(text)


# ── auth method 1: watsonx Orchestrate Bearer token ───────────────────────────
def _call_watsonx_orchestrate(prompt: str) -> dict | None:
    """
    Authenticate using a Bearer token obtained from watsonx Orchestrate.

    In the Orchestrate UI go to:
      Profile (top-right) → API access → Copy token

    Set it as:
      WATSONX_TOKEN=<paste token here>
    """
    try:
        from ibm_watsonx_ai import Credentials
    except ImportError:
        logger.debug("ibm-watsonx-ai not installed; skipping Orchestrate token path")
        return None

    token      = os.environ.get("WATSONX_TOKEN")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url        = os.environ.get("WATSONX_URL", _DEFAULT_URL)

    if not token or not project_id:
        return None

    try:
        credentials = Credentials(url=url, token=token)
        model = _make_model(credentials, project_id)
        return _invoke(model, prompt)
    except Exception as exc:
        logger.warning("LLM 5-Whys (Orchestrate token): call failed — %s", exc)
        return None


# ── auth method 2: IBM Cloud IAM API key ─────────────────────────────────────
def _call_watsonx_apikey(prompt: str) -> dict | None:
    """
    Authenticate using an IBM Cloud IAM API key for direct watsonx.ai access.

    Set:
      WATSONX_API_KEY=<iam-api-key>
    """
    try:
        from ibm_watsonx_ai import Credentials
    except ImportError:
        logger.debug("ibm-watsonx-ai not installed; skipping IAM API key path")
        return None

    api_key    = os.environ.get("WATSONX_API_KEY")
    project_id = os.environ.get("WATSONX_PROJECT_ID")
    url        = os.environ.get("WATSONX_URL", _DEFAULT_URL)

    if not api_key or not project_id:
        return None

    try:
        credentials = Credentials(url=url, api_key=api_key)
        model = _make_model(credentials, project_id)
        return _invoke(model, prompt)
    except Exception as exc:
        logger.warning("LLM 5-Whys (IAM API key): call failed — %s", exc)
        return None


# ── public entry point ────────────────────────────────────────────────────────
def generate_five_whys_llm(
    category: str,
    defect_summaries: list[str],
) -> dict | None:
    """
    Generate a context-specific 5-Whys dict using watsonx.ai.

    Authentication priority:
      1. WATSONX_TOKEN      — watsonx Orchestrate Bearer token (preferred)
      2. WATSONX_API_KEY    — IBM Cloud IAM API key (direct watsonx.ai)

    Returns a dict with keys why1..why5, answer1..answer5, root_cause,
    or None if no credentials are set or the call fails.
    The caller falls back to static templates when this returns None.
    """
    if not defect_summaries:
        return None

    prompt = _build_prompt(category, defect_summaries)

    # Prefer Orchestrate token — available to all IBM employees with Orchestrate access
    if os.environ.get("WATSONX_TOKEN"):
        result = _call_watsonx_orchestrate(prompt)
        if result is not None:
            return result

    # Fall back to direct IAM API key
    if os.environ.get("WATSONX_API_KEY"):
        result = _call_watsonx_apikey(prompt)
        if result is not None:
            return result

    return None
