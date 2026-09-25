"""Environment configuration for the FlexRadio to MQTT bridge."""

from os import environ

from environs import Env


ENVIR = Env()
ENVIR.read_env()


class Config:
    """Required runtime settings supplied by Docker Compose."""

    UDPPORT = ENVIR("UDPPORT")
    FLEXIP = ENVIR("FLEXIP")
    FLEXPORT = ENVIR("FLEXPORT")
    STN = ENVIR("STN")
    MQTT_HOST = ENVIR("MQTT_HOST")
    MQTT_PORT = ENVIR("MQTT_PORT")
