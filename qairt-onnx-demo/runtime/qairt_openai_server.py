import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class State:
    model_path = None
    backend = "htp"
    model_id = "qairt-onnx"


def json_response(handler, status, payload):
    body = json.dumps(payload, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8"))


class Handler(BaseHTTPRequestHandler):
    server_version = "QAIRTOnnxAgent/0.1"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        if self.path in {"/health", "/v1/health"}:
            json_response(
                self,
                200,
                {
                    "ok": True,
                    "runtime": "onnxruntime-qnn",
                    "backend": State.backend,
                    "model_path": State.model_path,
                    "note": "This is a scaffold endpoint. A full chat route needs a QNN-compatible generative model.",
                },
            )
            return

        if self.path == "/v1/models":
            json_response(
                self,
                200,
                {
                    "object": "list",
                    "data": [
                        {
                            "id": State.model_id,
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "local-qairt-onnx",
                        }
                    ],
                },
            )
            return

        json_response(self, 404, {"error": {"message": "not found"}})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            json_response(self, 404, {"error": {"message": "not found"}})
            return

        _payload = read_json(self)
        json_response(
            self,
            501,
            {
                "error": {
                    "message": (
                        "QAIRT/ONNX server is running, but chat completions require a "
                        "QNN-compatible generative ONNX/ORT GenAI model plus tokenizer/generation code."
                    ),
                    "type": "not_implemented",
                    "model_path": State.model_path,
                    "backend": State.backend,
                }
            },
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4101)
    parser.add_argument("--model", default="")
    parser.add_argument("--backend", choices=["htp", "cpu"], default="htp")
    args = parser.parse_args()

    State.model_path = args.model or None
    State.backend = args.backend
    print(f"[QAIRT/ONNX] Endpoint: http://{args.host}:{args.port}/v1")
    print(f"[QAIRT/ONNX] Backend:  {State.backend}")
    print(f"[QAIRT/ONNX] Model:    {State.model_path or '(none)'}")
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
