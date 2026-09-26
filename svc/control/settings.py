"""JSON configuration for the antenna control service."""

import json
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

    return Config(
        mqtt_host=_required_string(control, "mqtt_host", control_path),
        mqtt_port=_required_integer(control, "mqtt_port", control_path, 1, 65535),
        mqtt_keepalive=_required_integer(control, "mqtt_keepalive", control_path, 1, 65535),
        stacks=_load_json(config_dir / "stacks.json"),
        sixpack=_load_json(config_dir / "sixpack.json"),
        stn1=_load_json(config_dir / "stn1.json"),
        stn2=_load_json(config_dir / "stn2.json"),
    )
