"""
title: Snapdragon NPU Demo Tools
author: Qualcomm DevRel
description: Local demo tools for showing Open WebUI agent behavior on a Snapdragon NPU through Foundry Local.
version: 0.1.0
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import json
import urllib.error
import urllib.request


class Tools:
    def get_current_time(self, timezone: str = "Asia/Calcutta") -> str:
        """
        Get the current local time for the requested timezone.
        :param timezone: IANA timezone name, for example Asia/Calcutta or America/Los_Angeles.
        :return: A JSON string with the timezone, ISO timestamp, date, and time.
        """
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            timezone = "Asia/Calcutta"
            tz = ZoneInfo(timezone)

        now = datetime.now(tz)
        return json.dumps(
            {
                "timezone": timezone,
                "iso": now.isoformat(timespec="seconds"),
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
            }
        )

    def get_npu_status(self) -> str:
        """
        Check the local Foundry endpoint and report the active Snapdragon NPU model status.
        :return: A JSON string with endpoint, model, device, acceleration provider, and readiness.
        """
        endpoint = "http://127.0.0.1:5272/v1"
        status = {
            "endpoint": endpoint,
            "ready": False,
            "device": "NPU",
            "acceleration": "QNNExecutionProvider",
            "model": "unknown",
            "note": "Foundry Local should be running on the Snapdragon NPU.",
        }

        try:
            with urllib.request.urlopen(f"{endpoint}/models", timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            models = payload.get("data", [])
            if models:
                status["model"] = models[0].get("id", "unknown")
                status["ready"] = True
                status["note"] = "Foundry Local is serving this model through the local NPU bridge."
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            status["note"] = f"Foundry Local was not reachable: {exc}"

        return json.dumps(status)

    def draft_stage_note(self, topic: str = "local AI agent demo") -> str:
        """
        Draft a short stage note for a Qualcomm DevRel demo.
        :param topic: The demo topic or audience framing.
        :return: A concise stage note that can be read aloud.
        """
        return (
            f"For this {topic}, Open WebUI is the chat surface, Foundry Local is the OpenAI-compatible runtime, "
            "and the model is running locally on the Snapdragon NPU with tool calls handled on-device."
        )
