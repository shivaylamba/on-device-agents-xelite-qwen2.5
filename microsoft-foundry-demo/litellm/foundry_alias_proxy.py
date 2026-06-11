"""
Tiny OpenAI-compatible alias proxy for local OpenClaw demos.

It keeps the same endpoint shape as the LiteLLM proxy used by the docs:
  http://127.0.0.1:4001/v1

The only alias it provides is:
  foundry-npu -> qwen2.5-7b-instruct-qnn-npu
"""

import argparse
import json
import os
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = os.environ.get("FOUNDRY_ALIAS_UPSTREAM", "http://127.0.0.1:5299/v1").rstrip("/")
ALIAS_MODEL = os.environ.get("FOUNDRY_ALIAS_MODEL", "foundry-npu")
TARGET_MODEL = os.environ.get("FOUNDRY_TARGET_MODEL", "qwen2.5-7b-instruct-qnn-npu")


def _json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _raw_response(handler, status, content_type, body):
    handler.send_response(status)
    handler.send_header("Content-Type", content_type or "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


def _forward_chat(payload):
    forwarded = dict(payload)
    if forwarded.get("model") == ALIAS_MODEL:
        forwarded["model"] = TARGET_MODEL

    data = json.dumps(forwarded).encode("utf-8")
    request = urllib.request.Request(
        f"{UPSTREAM}/chat/completions",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return response.status, response.headers.get("Content-Type"), response.read()


class Handler(BaseHTTPRequestHandler):
    server_version = "FoundryAliasProxy/0.1"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path in {"/health", "/v1/health"}:
            _json_response(
                self,
                200,
                {
                    "ok": True,
                    "upstream": UPSTREAM,
                    "alias_model": ALIAS_MODEL,
                    "target_model": TARGET_MODEL,
                },
            )
            return

        if self.path == "/v1/models":
            _json_response(
                self,
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": ALIAS_MODEL,
                            "object": "model",
                            "created": 1677610602,
                            "owned_by": "local-foundry-alias",
                        }
                    ],
                },
            )
            return

        _json_response(self, 404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            _json_response(self, 404, {"error": {"message": "not found"}})
            return

        try:
            status, content_type, body = _forward_chat(_read_json(self))
            _raw_response(self, status, content_type, body)
        except urllib.error.HTTPError as exc:
            body = exc.read()
            _raw_response(self, exc.code, exc.headers.get("Content-Type"), body)
        except Exception as exc:
            _json_response(self, 502, {"error": {"message": str(exc), "type": "alias_proxy_error"}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4001)
    args = parser.parse_args()

    print(f"[Foundry Alias Proxy] Endpoint: http://{args.host}:{args.port}/v1")
    print(f"[Foundry Alias Proxy] Upstream:  {UPSTREAM}")
    print(f"[Foundry Alias Proxy] Model:     {ALIAS_MODEL} -> {TARGET_MODEL}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
