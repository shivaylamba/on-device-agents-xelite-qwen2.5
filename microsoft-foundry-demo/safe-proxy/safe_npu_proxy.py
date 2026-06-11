import argparse
import json
import os
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


UPSTREAM = os.environ.get("SAFE_PROXY_UPSTREAM", "http://127.0.0.1:5272/v1").rstrip("/")
HOST = os.environ.get("SAFE_PROXY_HOST", "127.0.0.1")
PORT = int(os.environ.get("SAFE_PROXY_PORT", "5299"))
MAX_TOKENS = int(os.environ.get("SAFE_PROXY_MAX_TOKENS", "128"))
MAX_MESSAGES = int(os.environ.get("SAFE_PROXY_MAX_MESSAGES", "8"))
MAX_MESSAGE_CHARS = int(os.environ.get("SAFE_PROXY_MAX_MESSAGE_CHARS", "12000"))
REQUEST_TIMEOUT = int(os.environ.get("SAFE_PROXY_REQUEST_TIMEOUT", "180"))
STRIP_OPENAI_TOOLS = os.environ.get("SAFE_PROXY_STRIP_OPENAI_TOOLS", "true").lower() in {
    "1",
    "true",
    "yes",
}

NPU_LOCK = threading.Lock()


def _json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _sse_chat_response(handler, payload):
    choice = (payload.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    delta = choice.get("delta") or {}
    content = message.get("content") or delta.get("content") or ""
    model = payload.get("model", "foundry-npu")
    created = payload.get("created", int(time.time()))
    response_id = payload.get("id", "safe-npu-proxy")

    chunks = [
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": content},
                    "finish_reason": None,
                }
            ],
        },
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": choice.get("finish_reason") or "stop",
                }
            ],
        },
    ]

    body = "".join(f"data: {json.dumps(chunk)}\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    encoded = body.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.end_headers()
    handler.wfile.write(encoded)


def _read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    return json.loads(handler.rfile.read(length).decode("utf-8"))


def _trim_text(value, max_chars):
    if not isinstance(value, str) or len(value) <= max_chars:
        return value
    return value[:max_chars] + "\n\n[truncated by safe NPU proxy]"


def _sanitize_messages(messages):
    if not isinstance(messages, list):
        return messages

    selected = messages[-MAX_MESSAGES:]
    sanitized = []
    for message in selected:
        if not isinstance(message, dict):
            continue
        item = dict(message)
        content = item.get("content")
        if isinstance(content, str):
            item["content"] = _trim_text(content, MAX_MESSAGE_CHARS)
        elif isinstance(content, list):
            trimmed_parts = []
            budget = MAX_MESSAGE_CHARS
            for part in content:
                if not isinstance(part, dict):
                    continue
                new_part = dict(part)
                if isinstance(new_part.get("text"), str):
                    new_part["text"] = _trim_text(new_part["text"], max(0, budget))
                    budget -= len(new_part["text"])
                trimmed_parts.append(new_part)
                if budget <= 0:
                    break
            item["content"] = trimmed_parts
        sanitized.append(item)
    return sanitized


def _sanitize_chat_payload(payload):
    clean = dict(payload)
    clean["max_tokens"] = min(int(clean.get("max_tokens") or MAX_TOKENS), MAX_TOKENS)
    clean["stream"] = False
    clean["messages"] = _sanitize_messages(clean.get("messages", []))

    if STRIP_OPENAI_TOOLS:
        clean.pop("tools", None)
        clean.pop("tool_choice", None)
        clean.pop("parallel_tool_calls", None)

    return clean


def _forward(method, path, payload=None):
    url = f"{UPSTREAM}{path}"
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
        raw = response.read()
        if not raw:
            return response.status, {}
        return response.status, json.loads(raw.decode("utf-8"))


def _is_attention_cache_error(exc):
    text = str(exc)
    return "GroupQueryAttention" in text or "seqlens_k" in text


class Handler(BaseHTTPRequestHandler):
    server_version = "SafeNPUProxy/0.1"

    def log_message(self, fmt, *args):
        print(f"[{time.strftime('%H:%M:%S')}] {self.address_string()} {fmt % args}")

    def do_GET(self):
        if self.path in {"/health", "/v1/health"}:
            _json_response(
                self,
                200,
                {
                    "ok": True,
                    "upstream": UPSTREAM,
                    "max_tokens": MAX_TOKENS,
                    "max_messages": MAX_MESSAGES,
                    "serialized": True,
                    "strip_openai_tools": STRIP_OPENAI_TOOLS,
                },
            )
            return

        if self.path == "/v1/models":
            try:
                status, payload = _forward("GET", "/models")
                _json_response(self, status, payload)
            except Exception as exc:
                _json_response(self, 502, {"error": {"message": str(exc), "type": "upstream_error"}})
            return

        _json_response(self, 404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            _json_response(self, 404, {"error": {"message": "not found"}})
            return

        try:
            raw_payload = _read_json(self)
            client_requested_stream = bool(raw_payload.get("stream"))
            payload = _sanitize_chat_payload(raw_payload)
        except Exception as exc:
            _json_response(self, 400, {"error": {"message": f"invalid JSON payload: {exc}"}})
            return

        with NPU_LOCK:
            try:
                status, response = _forward("POST", "/chat/completions", payload)
                if client_requested_stream and status == 200:
                    _sse_chat_response(self, response)
                else:
                    _json_response(self, status, response)
            except urllib.error.HTTPError as exc:
                body = exc.read().decode("utf-8", errors="replace")
                message = body or str(exc)
                status = 503 if _is_attention_cache_error(message) else exc.code
                _json_response(
                    self,
                    status,
                    {
                        "error": {
                            "message": message,
                            "type": "npu_attention_cache_error" if status == 503 else "upstream_http_error",
                            "hint": (
                                "Restart the Foundry bridge to clear the NPU session, then retry with a smaller "
                                "prompt. The safe proxy serialized the request and clamped max_tokens."
                            )
                            if status == 503
                            else None,
                        }
                    },
                )
            except Exception as exc:
                status = 503 if _is_attention_cache_error(exc) else 502
                _json_response(
                    self,
                    status,
                    {
                        "error": {
                            "message": str(exc),
                            "type": "npu_attention_cache_error" if status == 503 else "upstream_error",
                        }
                    },
                )


def main():
    global UPSTREAM

    parser = argparse.ArgumentParser(description="Serialized OpenAI-compatible proxy for Foundry NPU models.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--upstream", default=UPSTREAM)
    args = parser.parse_args()

    UPSTREAM = args.upstream.rstrip("/")

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"[Safe NPU Proxy] Listening on http://{args.host}:{args.port}/v1")
    print(f"[Safe NPU Proxy] Upstream: {UPSTREAM}")
    print(f"[Safe NPU Proxy] Serialized requests: yes")
    print(f"[Safe NPU Proxy] Max tokens: {MAX_TOKENS}")
    print(f"[Safe NPU Proxy] Max messages: {MAX_MESSAGES}")
    server.serve_forever()


if __name__ == "__main__":
    main()
