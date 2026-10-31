"""JSON configuration for the antenna control service."""

import json
import os

from config_layout import compose
from dataclasses import dataclass
from pathlib import Path


CONFIG_DIR = Path("/app/cfg")


@dataclass(frozen=True)
class Config:
    """Validated technical configuration and control data."""

    mqtt_host: str
    mqtt_port: int
    mqtt_keepalive: int
    stacks: dict
    sixpack: dict
    stn1: dict
    stn2: dict
    state_path: Path = Path("/app/data/control/state.json")


def _load_json(path):
    try:
        with path.open(encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se puede cargar {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: la raíz debe ser un objeto JSON")
    return data


def _required_string(data, key, source):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{source}: {key} debe ser una cadena no vacía")
    return value


def _required_integer(data, key, source, minimum, maximum):
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or not minimum <= value <= maximum:
        raise ValueError(f"{source}: {key} debe estar entre {minimum} y {maximum}")
    return value


def load_config(config_dir=CONFIG_DIR):
    """Load the service configuration and its control data files."""
    config_dir = Path(config_dir)
    control_path = config_dir / "control.json"
    control = _load_json(control_path)

    installation_path = config_dir / 'control/installation.json'
    initial_path = config_dir / 'control/initial-state.json'
    if installation_path.exists() or initial_path.exists():
        stations, stacks, sixpack = compose(_load_json(installation_path), _load_json(initial_path))
    else:
        # Existing deployments remain valid until their own files are migrated.
        stations = {name: _load_json(config_dir / (name + '.json')) for name in ('stn1', 'stn2')}
        stacks, sixpack = _load_json(config_dir / 'stacks.json'), _load_json(config_dir / 'sixpack.json')
    return Config(
        mqtt_host=_required_string(control, "mqtt_host", control_path),
        mqtt_port=_required_integer(control, "mqtt_port", control_path, 1, 65535),
        mqtt_keepalive=_required_integer(control, "mqtt_keepalive", control_path, 1, 65535),
        stacks=stacks,
        sixpack=sixpack,
        stn1=stations["stn1"],
        stn2=stations["stn2"],
        state_path=Path(os.environ.get("CONTROL_STATE_PATH", "/app/data/control/state.json")),
    )
