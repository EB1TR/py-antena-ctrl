"""JSON configuration for the FlexRadio to MQTT bridge."""

import json
from dataclasses import dataclass
from pathlib import Path


CONFIG_PATH = Path("/app/config.json")


@dataclass(frozen=True)
class Config:
    """Validated runtime settings for one FlexRadio station."""

    station: str
    flex_host: str
    flex_port: int
    udp_port: int
    mqtt_host: str
    mqtt_port: int


def _required_string(data, key):
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} debe ser una cadena no vacía")
    return value


def _required_port(data, key):
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or not 1 <= value <= 65535:
        raise ValueError(f"{key} debe ser un puerto entre 1 y 65535")
    return value


def load_config(path=CONFIG_PATH):
    """Load and validate a station configuration file."""
    path = Path(path)
    try:
        with path.open(encoding="utf-8") as config_file:
            data = json.load(config_file)
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"No se puede cargar {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path}: la raíz debe ser un objeto JSON")

    station = _required_string(data, "station")
    if station not in ("stn1", "stn2"):
        raise ValueError("station debe ser stn1 o stn2")

    return Config(
        station=station,
        flex_host=_required_string(data, "flex_host"),
        flex_port=_required_port(data, "flex_port"),
        udp_port=_required_port(data, "udp_port"),
        mqtt_host=_required_string(data, "mqtt_host"),
        mqtt_port=_required_port(data, "mqtt_port"),
    )
