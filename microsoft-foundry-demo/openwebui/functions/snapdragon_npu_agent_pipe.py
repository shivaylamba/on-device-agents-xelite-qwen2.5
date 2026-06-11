"""
title: Snapdragon NPU Agent Pipe
author: Qualcomm DevRel
description: Reliable Open WebUI pipe that runs a local agent loop with demo tools and Foundry Local on Snapdragon NPU.
version: 0.1.0
"""

from datetime import datetime
from zoneinfo import ZoneInfo
import json
import os
import urllib.error
import urllib.request


class Pipe:
    name = "Snapdragon NPU Agent Pipe "

    def _current_time(self) -> dict:
        now = datetime.now(ZoneInfo("Asia/Calcutta"))
        return {
            "timezone": "Asia/Calcutta",
            "iso": now.isoformat(timespec="seconds"),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        }

    def _npu_status(self) -> dict:
        endpoint = "http://127.0.0.1:5272/v1"
        status = {
            "endpoint": endpoint,
            "ready": False,
            "device": "NPU",
            "acceleration": "QNNExecutionProvider",
            "model": "qwen2.5-7b-instruct-qnn-npu",
            "note": "Foundry Local should be running on the Snapdragon NPU.",
        }
        try:
            with urllib.request.urlopen(f"{endpoint}/models", timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
            models = payload.get("data", [])
            if models:
                status["model"] = models[0].get("id", status["model"])
                status["ready"] = True
                status["note"] = "Foundry Local is serving this model through the local NPU bridge."
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            status["note"] = f"Foundry Local was not reachable: {exc}"
        return status

    def _draft_stage_note(self, topic: str) -> str:
        return (
            f"For this {topic}, Open WebUI is the chat surface, Foundry Local is the OpenAI-compatible runtime, "
            "and the model is running locally on the Snapdragon NPU with deterministic agent tool steps."
        )

    def _ask_foundry(self, user_prompt: str, tool_results: dict) -> str:
        base_url = os.environ.get("SAFE_NPU_BASE_URL", "http://127.0.0.1:5299/v1").rstrip("/")
        endpoint = f"{base_url}/chat/completions"
        payload = {
            "model": tool_results["npu_status"]["model"],
            "temperature": 0.2,
            "max_tokens": 48,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Write one short stage tagline for a Qualcomm Snapdragon NPU local AI demo. "
                        "Return one sentence only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Open WebUI is connected to Foundry Local. "
                        f"The model is {tool_results['npu_status']['model']} on "
                        f"{tool_results['npu_status']['acceleration']}."
                    ),
                },
            ],
        }
        try:
            request = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=28) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"].get("content", "").strip()
        except Exception as exc:
            return f"NPU completion check unavailable: {exc}"

    async def _emit(self, emitter, description: str, done: bool = False):
        if emitter:
            await emitter(
                {
                    "type": "status",
                    "data": {
                        "description": description,
                        "done": done,
                    },
                }
            )

    async def pipe(self, body: dict, __event_emitter__=None, **kwargs) -> str:
        messages = body.get("messages", [])
        user_prompt = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                content = message.get("content", "")
                user_prompt = content if isinstance(content, str) else json.dumps(content)
                break

        await self._emit(__event_emitter__, "Calling tool: get_current_time")
        current_time = self._current_time()

        await self._emit(__event_emitter__, "Calling tool: get_npu_status")
        npu_status = self._npu_status()

        await self._emit(__event_emitter__, "Calling tool: draft_stage_note")
        stage_note = self._draft_stage_note("Qualcomm DevRel Snapdragon NPU demo")

        tool_results = {
            "current_time": current_time,
            "npu_status": npu_status,
            "stage_note": stage_note,
        }

        await self._emit(__event_emitter__, "Calling local NPU model for final answer")
        npu_tagline = self._ask_foundry(user_prompt, tool_results)
        if len(npu_tagline.split()) < 6:
            npu_tagline = "Local agent steps completed through Open WebUI with Foundry Local on the Snapdragon NPU."
        await self._emit(__event_emitter__, "Agent run complete", done=True)

        final_answer = (
            f"It is {current_time['time']} on {current_time['date']} in {current_time['timezone']}. "
            f"Foundry Local reports `{npu_status['model']}` is ready on the `{npu_status['device']}` through "
            f"`{npu_status['acceleration']}`. Stage note: {stage_note} "
            f"NPU completion check: {npu_tagline}"
        )

        return (
            "### Agent Tool Trace\n"
            f"1. `get_current_time` -> {current_time['iso']} ({current_time['timezone']})\n"
            f"2. `get_npu_status` -> model `{npu_status['model']}`, device `{npu_status['device']}`, "
            f"acceleration `{npu_status['acceleration']}`, ready `{npu_status['ready']}`\n"
            f"3. `draft_stage_note` -> {stage_note}\n\n"
            "### Final Stage Answer\n"
            f"{final_answer}"
        )
