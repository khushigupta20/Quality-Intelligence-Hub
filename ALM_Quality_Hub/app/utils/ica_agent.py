"""
ICA Agent HTTP caller — sends prompts to an IBM ICA agent endpoint and
returns the parsed reply. Mirrors the retry/timeout logic from the
Node.js server.js backend in ICA_BOB/req-analyzer-app/backend/.
"""

import requests
import time
import logging

logger = logging.getLogger(__name__)

ICA_TIMEOUT = 120  # seconds per attempt
RETRYABLE_STATUSES = {502, 503, 504}

TASK_PROMPTS = {
    "translate": (
        "You are a requirements translator. The user will provide software requirements in any language. \n"
        "Translate them accurately into clear, professional English. Preserve all technical details."
    ),
    "analyze": (
        "You are a software requirements analyst. Analyze the provided requirements and give a structured report covering:\n"
        "1. Clarity and completeness\n"
        "2. Ambiguities or vague statements\n"
        "3. Missing information\n"
        "4. Suggestions for improvement"
    ),
    "review_tests": (
        "You are a test case reviewer. Review the provided test cases against the requirements and report:\n"
        "1. Missing test scenarios\n"
        "2. Redundant or duplicate tests\n"
        "3. Edge cases not covered\n"
        "4. Inconsistencies between requirements and test cases"
    ),
    "edge_cases": (
        "You are a software QA expert. Identify all possible edge cases, boundary conditions, and negative scenarios \n"
        "for the provided requirements or functionality. Be thorough and systematic."
    ),
    "validate": (
        "You are a requirements validation expert. Check the consistency between the provided requirements and test cases.\n"
        "Report: \n"
        "1. Requirements with no test coverage\n"
        "2. Test cases that don't map to any requirement\n"
        "3. Conflicts or contradictions"
    ),
    "auth": (
        "You are an access control agent for the Quality Intelligence Hub application. "
        "A user has passed local password verification and is requesting access. "
        "Your job is to confirm or deny their access. "
        "Reply with exactly one word: ALLOW to grant access, or DENY to block it. "
        "Unless there is a specific reason to deny, reply ALLOW."
    ),
}


def call_ica_agent(task_type: str, user_input: str, endpoint: str, api_key: str) -> dict:
    """Call the ICA agent with the given task type and user input.

    Returns a dict with either ``{"reply": <text>}`` on success or
    ``{"error": <message>}`` on failure.
    """
    if task_type not in TASK_PROMPTS:
        return {"error": f"Unknown task type: {task_type}"}

    full_prompt = TASK_PROMPTS[task_type] + "\n\n---\n\nUser Input:\n" + user_input
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    body = {"message": full_prompt}

    last_status = None
    last_error = None

    for attempt in range(1, 3):  # attempts 1 and 2
        try:
            response = requests.post(endpoint, json=body, headers=headers, timeout=ICA_TIMEOUT)
            last_status = response.status_code

            if response.ok:
                try:
                    data = response.json()
                except Exception:
                    data = {}

                # Reply extraction fallback chain
                agent_reply = None
                messages = data.get("messages", [])
                for msg in reversed(messages):
                    if isinstance(msg, dict) and msg.get("role") == "assistant":
                        agent_reply = msg.get("content") or msg.get("text") or str(msg)
                        break
                if agent_reply is None:
                    agent_reply = (
                        (data.get("output") or {}).get("text")
                        or data.get("message")
                        or data.get("response")
                        or data.get("result")
                        or data.get("content")
                        or str(data)
                    )

                return {"reply": agent_reply}

            # Non-OK response
            logger.warning("ICA attempt %d → %d", attempt, last_status)

            if last_status not in RETRYABLE_STATUSES:
                break  # non-retryable (e.g. 401, 400)

            if attempt < 2:
                logger.info("Retrying after 3s…")
                time.sleep(3)

        except requests.Timeout:
            last_status = 504
            logger.warning("ICA attempt %d timed out", attempt)
            if attempt < 2:
                time.sleep(3)

        except Exception as exc:
            raise exc

    # Build user-friendly error message
    if last_status == 504:
        last_error = (
            "The ICA agent took too long to respond (timeout). "
            "Please try again or simplify your input."
        )
    elif last_status == 503:
        last_error = "The ICA agent is temporarily unavailable. Please try again in a moment."
    else:
        last_error = (
            f"ICA agent returned an error (status {last_status}). "
            "Please check your endpoint and API key in Settings."
        )

    return {"error": last_error}
