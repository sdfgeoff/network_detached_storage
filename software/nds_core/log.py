from typing import Dict, Any
import json


def _log(level: str, event: str, data: Dict[str, Any]) -> None:
    msg = f"{level} -- {event} -- {json.dumps(data)}"
    print(msg)


def info(event: str, data: Dict[str, Any]) -> None:
    _log("INFO", event, data)


def warn(event: str, data: Dict[str, Any]) -> None:
    _log("WARN", event, data)


def error(event: str, data: Dict[str, Any]) -> None:
    _log("ERROR", event, data)


def debug(event: str, data: Dict[str, Any]) -> None:
    _log("DEBUG", event, data)
