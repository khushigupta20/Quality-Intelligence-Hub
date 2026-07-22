"""
Settings manager — reads and writes ICA Agent credentials to config.json.
config.json is stored at the project root (next to app.py).
"""

import os
import json
import logging

logger = logging.getLogger(__name__)

# Resolve config.json path relative to this file's location:
# this file is at app/utils/settings.py → ../../config.json = project root
CONFIG_PATH = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'config.json')
)

_DEFAULTS = {
    "ica_endpoint":       "",
    "ica_api_key":        "",
    "watsonx_api_key":    "",
    "watsonx_project_id": "",
    "watsonx_model_id":   "",
}


def get_settings() -> dict:
    """Read config.json and return settings dict. Returns defaults if file is missing or invalid."""
    if not os.path.exists(CONFIG_PATH):
        return dict(_DEFAULTS)
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {
            "ica_endpoint":       str(data.get("ica_endpoint",       "")),
            "ica_api_key":        str(data.get("ica_api_key",        "")),
            "watsonx_api_key":    str(data.get("watsonx_api_key",    "")),
            "watsonx_project_id": str(data.get("watsonx_project_id", "")),
            "watsonx_model_id":   str(data.get("watsonx_model_id",   "")),
        }
    except Exception as exc:
        logger.warning("Could not read config.json: %s", exc)
        return dict(_DEFAULTS)


def save_settings(data: dict) -> None:
    """Write settings to config.json — preserves the 'users' key."""
    # Load existing config so we never overwrite the users block
    existing = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        except Exception:
            pass

    existing.update({
        "ica_endpoint":       str(data.get("ica_endpoint",       "")),
        "ica_api_key":        str(data.get("ica_api_key",        "")),
        "watsonx_api_key":    str(data.get("watsonx_api_key",    "")),
        "watsonx_project_id": str(data.get("watsonx_project_id", "")),
        "watsonx_model_id":   str(data.get("watsonx_model_id",   "")),
    })
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(existing, f, indent=2)
    logger.info("Settings saved to %s", CONFIG_PATH)


def get_users() -> dict:
    """Read the 'users' dict from config.json."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get("users", {})
    except Exception as exc:
        logger.warning("Could not read users from config.json: %s", exc)
        return {}
