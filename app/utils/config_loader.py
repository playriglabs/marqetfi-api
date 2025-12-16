"""Configuration file loader utilities."""

import json
from pathlib import Path
from typing import Any

from loguru import logger


def load_json_config(filename: str) -> dict[str, Any]:
    """Load JSON configuration file.

    Args:
        filename: Name of the JSON file in app/config/

    Returns:
        Parsed JSON data

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    config_path = Path(__file__).parent.parent / "config" / filename

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {filename}")

    try:
        with open(config_path, encoding="utf-8") as f:
            data: dict[str, Any] = json.load(f)
        logger.info(f"Loaded config from {filename}")
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {filename}: {e}")
        raise


def get_chains_config() -> dict[str, Any]:
    """Get chains configuration."""
    return load_json_config("chains.json")


def get_contracts_config() -> dict[str, Any]:
    """Get contracts configuration."""
    return load_json_config("contracts.json")


def get_buffers_config() -> dict[str, Any]:
    """Get buffers configuration."""
    return load_json_config("buffers.json")

