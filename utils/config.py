"""Application configuration settings.

This module centralises configuration constants and helper functions
for reading environment variables.  Having a single place for
configuration allows the rest of the application to remain free of
hard‑coded values and makes it easier to override settings across
environments (development, testing, production).
"""

from __future__ import annotations

import os


def _get_env(key: str, default: str) -> str:
    """Return the value of an environment variable or a default.

    Args:
        key (str): Environment variable name.
        default (str): Default value if the variable is not present.

    Returns:
        str: The environment value or default.
    """
    return os.environ.get(key, default)


# Application title displayed in the browser tab.
APP_TITLE: str = _get_env("APP_TITLE", "Plotly Dash MVVM")

# Debug mode: if True the Dash server will auto‑reload and display
# detailed error information.  Never set this to True in production.
DEBUG_MODE: bool = _get_env("DEBUG_MODE", "True").lower() in {"1", "true", "yes"}

# Server host and port configuration.
HOST: str = _get_env("HOST", "127.0.0.1")
PORT: int = int(_get_env("PORT", "8050"))