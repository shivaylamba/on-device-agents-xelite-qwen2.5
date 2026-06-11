import argparse
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent
FOUNDRY_BASE = os.environ.get("FOUNDRY_BASE", "http://127.0.0.1:5299/v1")
MODEL = os.environ.get("FOUNDRY_MODEL_ID", "qwen2.5-0.5b-instruct-qnn-npu")
DRAFT_DIR = Path(os.environ.get("DEMO_DRAFT_DIR", ROOT / "drafts"))


TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Returns the current local time, timezone, and ISO timestamp.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_npu_status",
            "description": "Returns the local Foundry model, acceleration, endpoint, and demo readiness.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_draft",
            "description": "Saves a short text draft locally and returns the saved file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short title for the draft."},
                    "content": {"type": "string", "description": "Draft content to save."},
                },
                "required": ["title", "content"],
            },
        },
    },
]


def post_foundry(path, payload, timeout=35):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        FOUNDRY_BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read())


def get_foundry(path, timeout=10):
    with urllib.request.urlopen(FOUNDRY_BASE + path, timeout=timeout) as response:
        return json.loads(response.read())


def execute_tool(name, arguments):
    if name == "get_current_time":
        now = datetime.now().astimezone()
        return {
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": now.tzname(),
            "iso": now.isoformat(),
        }

    if name == "get_npu_status":
        models = get_foundry("/models").get("data", [])
        loaded = [model.get("id") for model in models]
        return {
            "endpoint": FOUNDRY_BASE,
            "model": loaded[0] if loaded else MODEL,
            "loaded_models": loaded,
            "device": "NPU",
            "execution_provider": "QNNExecutionProvider",
            "status": "ready" if loaded else "model endpoint reachable, no model listed",
        }

    if name == "save_draft":
        title = str(arguments.get("title", "agent-draft")).strip() or "agent-draft"
        content = str(arguments.get("content", "")).strip()
        safe_title = "".join(ch if ch.isalnum() else "-" for ch in title.lower()).strip("-")
        safe_title = safe_title or "agent-draft"
        DRAFT_DIR.mkdir(parents=True, exist_ok=True)
        path = DRAFT_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{safe_title}.md"
        path.write_text(f"# {title}\n\n{content}\n", encoding="utf-8")
        return {"saved": True, "path": str(path), "bytes": path.stat().st_size}

    return {"error": f"Unknown tool: {name}"}


def parse_arguments(raw):
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def run_agent(prompt):
    started = time.perf_counter()
    events = []
    system = (
        "You are a Qualcomm Snapdragon local AI demo agent. "
        "Use tools when helpful, especially for time, NPU status, or saving drafts. "
        "After receiving tool results, produce a concise final answer for a DevRel demo."
    )
    messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
    first_elapsed = 0
    tool_calls = []

    try:
        first_started = time.perf_counter()
        first = post_foundry(
            "/chat/completions",
            {
                "model": MODEL,
                "messages": messages,
                "tools": TOOLS,
                "tool_choice": "auto",
                "max_tokens": 96,
                "stream": False,
            },
            timeout=18,
        )
        first_elapsed = time.perf_counter() - first_started
        assistant = first["choices"][0]["message"]
        tool_calls = assistant.get("tool_calls") or []
        messages.append(assistant)
    except Exception as exc:
        events.append(
            {
                "name": "model_tool_planning",
                "source": "fallback",
                "arguments": {},
                "result": {"warning": f"Model tool planning timed out; running local demo tools. {exc}"},
                "elapsed_ms": 0,
            }
        )

    executed_names = set()
    for call in tool_calls:
        function = call.get("function", {})
        name = function.get("name", "")
        arguments = parse_arguments(function.get("arguments", "{}"))
        tool_started = time.perf_counter()
        result = execute_tool(name, arguments)
        elapsed = time.perf_counter() - tool_started
        events.append(
            {
                "name": name,
                "source": "model",
                "arguments": arguments,
                "result": result,
                "elapsed_ms": round(elapsed * 1000),
            }
        )
        executed_names.add(name)
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call.get("id", name),
                "name": name,
                "content": json.dumps(result),
            }
        )

    required_demo_tools = ["get_current_time", "get_npu_status"]
    if any(word in prompt.lower() for word in ("save", "draft")):
        required_demo_tools.append("save_draft")

    supplemental_results = []
    for name in required_demo_tools:
        if name in executed_names:
            continue
        arguments = {}
        if name == "save_draft":
            arguments = {
                "title": "Snapdragon local AI demo draft",
                "content": "Draft placeholder created by the local demo agent.",
            }
        tool_started = time.perf_counter()
        result = execute_tool(name, arguments)
        elapsed = time.perf_counter() - tool_started
        event = {
            "name": name,
            "source": "demo-runtime",
            "arguments": arguments,
            "result": result,
            "elapsed_ms": round(elapsed * 1000),
        }
        events.append(event)
        supplemental_results.append(event)

    final_started = time.perf_counter()
    final_messages = [
        {
            "role": "system",
            "content": (
                "You are a Qualcomm DevRel demo assistant. Write a confident final answer. "
                "Use the provided tool results as facts. Do not ask for more information. "
                "Do not apologize. Mention local NPU execution when relevant."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Original request: {prompt}\n\n"
                f"Tool results JSON:\n{json.dumps(events, indent=2)}\n\n"
                "Write the final answer now. If the user asked for a social post, write the post."
            ),
        },
    ]
    usage = {}
    try:
        final = post_foundry(
            "/chat/completions",
            {
                "model": MODEL,
                "messages": final_messages,
                "max_tokens": 96,
                "stream": False,
            },
            timeout=24,
        )
        final_elapsed = time.perf_counter() - final_started
        final_message = final["choices"][0]["message"].get("content", "")
        usage = final.get("usage", {})
    except Exception as exc:
        final_elapsed = time.perf_counter() - final_started
        status = next((event["result"] for event in events if event["name"] == "get_npu_status"), {})
        clock = next((event["result"] for event in events if event["name"] == "get_current_time"), {})
        final_message = (
            f"At {clock.get('local_time', 'local time')} {clock.get('timezone', '')}, "
            f"the local Snapdragon NPU agent is ready. "
            f"Model: {status.get('model', MODEL)}. "
            f"Acceleration: {status.get('execution_provider', 'QNNExecutionProvider')} on {status.get('device', 'NPU')}. "
            "Demo note: this agent is running locally through Foundry Local and can call tools without sending the workflow to the cloud."
        )
        events.append(
            {
                "name": "final_answer_fallback",
                "source": "demo-runtime",
                "arguments": {},
                "result": {"warning": f"Model final answer timed out; generated fallback answer. {exc}"},
                "elapsed_ms": round(final_elapsed * 1000),
            }
        )
    total_elapsed = time.perf_counter() - started
    completion_tokens = usage.get("completion_tokens") or 0

    return {
        "model": MODEL,
        "endpoint": FOUNDRY_BASE,
        "answer": final_message,
        "events": events,
        "metrics": {
            "first_call_ms": round(first_elapsed * 1000),
            "final_call_ms": round(final_elapsed * 1000),
            "total_ms": round(total_elapsed * 1000),
            "completion_tokens": completion_tokens,
            "tokens_per_second": round(completion_tokens / final_elapsed, 1) if completion_tokens else None,
        },
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, status, body, content_type="application/json"):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _json(self, status, payload):
        self._send(status, json.dumps(payload, indent=2), "application/json")

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (ROOT / "static" / "index.html").read_bytes(), "text/html; charset=utf-8")
            return
        if self.path == "/styles.css":
            self._send(200, (ROOT / "static" / "styles.css").read_bytes(), "text/css; charset=utf-8")
            return
        if self.path == "/app.js":
            self._send(200, (ROOT / "static" / "app.js").read_bytes(), "application/javascript; charset=utf-8")
            return
        if self.path == "/api/status":
            try:
                models = get_foundry("/models").get("data", [])
                self._json(
                    200,
                    {
                        "ok": True,
                        "endpoint": FOUNDRY_BASE,
                        "model": models[0].get("id") if models else MODEL,
                        "models": models,
                        "device": "NPU",
                        "execution_provider": "QNNExecutionProvider",
                    },
                )
            except Exception as exc:
                self._json(503, {"ok": False, "error": str(exc), "endpoint": FOUNDRY_BASE})
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/api/agent":
            self._json(404, {"error": "Not found"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
            prompt = str(body.get("prompt", "")).strip()
            if not prompt:
                self._json(400, {"error": "Prompt is required"})
                return
            self._json(200, run_agent(prompt))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            self._json(exc.code, {"error": detail})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def log_message(self, fmt, *args):
        print(f"[demo-ui] {self.address_string()} - {fmt % args}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Demo UI: http://{args.host}:{args.port}")
    print(f"Foundry API: {FOUNDRY_BASE}")
    server.serve_forever()


if __name__ == "__main__":
    main()
