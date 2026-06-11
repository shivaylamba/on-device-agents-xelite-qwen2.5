import argparse
import json
import os
import subprocess
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class State:
    bundle_path = ""
    qairt_root = ""
    arch = "aarch64-windows-msvc"
    host = "127.0.0.1"
    port = 4102
    model_id = "qwen3-4b-genie"


GENIE_LOCK = threading.Lock()


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
    return json.loads(raw.decode("utf-8-sig"))


def stream_response(handler, completion):
    now = int(time.time())
    chunk_id = f"chatcmpl-qairt-genie-{now}"
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "close")
    handler.end_headers()

    def send(payload):
        body = "data: " + json.dumps(payload) + "\n\n"
        handler.wfile.write(body.encode("utf-8"))
        handler.wfile.flush()

    send(
        {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": now,
            "model": State.model_id,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant"},
                    "text": "",
                    "finish_reason": None,
                }
            ],
        }
    )
    send(
        {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": now,
            "model": State.model_id,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": completion},
                    "text": completion,
                    "finish_reason": None,
                }
            ],
        }
    )
    send(
        {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": now,
            "model": State.model_id,
            "choices": [
                {"index": 0, "delta": {}, "text": "", "finish_reason": "stop"}
            ],
        }
    )
    handler.wfile.write(b"data: [DONE]\n\n")
    handler.wfile.flush()
    handler.close_connection = True


def build_prompt(messages):
    chunks = [
        (
            "<|im_start|>system\n"
            "Runtime context: you are Qwen3-4B served locally through Qualcomm "
            "QAIRT Genie on Snapdragon X Elite HTP/NPU. Be concise and do not "
            "claim TensorFlow, PyTorch, cloud, or GPU unless the user explicitly "
            "asks a separate general question.<|im_end|>"
        )
    ]
    for message in messages:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, list):
            content = " ".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
            )
        if role not in {"system", "user", "assistant"}:
            role = "user"
        chunks.append(f"<|im_start|>{role}\n{content}<|im_end|>")

    chunks.append("<|im_start|>assistant\n")
    return "\n".join(chunks)


def make_env():
    qairt = State.qairt_root
    bin_dir = os.path.join(qairt, "bin", State.arch)
    lib_dir = os.path.join(qairt, "lib", State.arch)
    skel_dir = os.path.join(qairt, "lib", "hexagon-v73", "unsigned")
    env = os.environ.copy()
    env["QAIRT_SDK_ROOT"] = qairt
    env["QAIRT_HOME"] = qairt
    env["QNN_SDK_ROOT"] = qairt
    env["ADSP_LIBRARY_PATH"] = skel_dir + ";"
    env["PATH"] = bin_dir + os.pathsep + lib_dir + os.pathsep + env.get("PATH", "")
    return env


def extract_completion(stdout):
    if "[BEGIN]:" in stdout and "[END]" in stdout:
        start = stdout.index("[BEGIN]:") + len("[BEGIN]:")
        end = stdout.index("[END]", start)
        return clean_completion(stdout[start:end].strip())
    return clean_completion(stdout.strip())


def clean_completion(text):
    original = text.strip()
    if "</think>" in text:
        text = text.split("</think>", 1)[1]
    if "<think>" in text:
        text = text.split("<think>", 1)[0]
    cleaned = text.strip()
    if cleaned:
        return cleaned
    return original.replace("<think>", "").replace("</think>", "").strip()


def run_genie(prompt):
    exe = os.path.join(State.qairt_root, "bin", State.arch, "genie-t2t-run.exe")
    config = os.path.join(State.bundle_path, "genie_config.json")
    if not os.path.exists(exe):
        raise FileNotFoundError(f"genie-t2t-run.exe not found: {exe}")
    if not os.path.exists(config):
        raise FileNotFoundError(f"genie_config.json not found: {config}")

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".txt", delete=False
    ) as handle:
        handle.write(prompt)
        prompt_file = handle.name

    try:
        with GENIE_LOCK:
            completed = subprocess.run(
                [exe, "-c", "genie_config.json", "--prompt_file", prompt_file],
                cwd=State.bundle_path,
                env=make_env(),
                capture_output=True,
                text=True,
                timeout=300,
            )
    finally:
        try:
            os.remove(prompt_file)
        except OSError:
            pass

    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(f"Genie exited with {completed.returncode}\n{output}")
    return extract_completion(output), output


class Handler(BaseHTTPRequestHandler):
    server_version = "Qwen3GenieOpenAI/0.1"

    def log_message(self, fmt, *args):
        return

    def do_GET(self):
        print(f"[Qwen3 Genie] GET {self.path}", flush=True)
        if self.path in {"/health", "/v1/health"}:
            json_response(
                self,
                200,
                {
                    "ok": True,
                    "runtime": "qairt-genie",
                    "model": State.model_id,
                    "bundle_path": State.bundle_path,
                    "qairt_root": State.qairt_root,
                    "arch": State.arch,
                    "adsp_library_path": os.path.join(
                        State.qairt_root, "lib", "hexagon-v73", "unsigned"
                    ),
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
                            "owned_by": "local-qairt-genie",
                        }
                    ],
                },
            )
            return

        json_response(self, 404, {"error": {"message": "not found"}})

    def do_POST(self):
        print(f"[Qwen3 Genie] POST {self.path}", flush=True)
        if self.path != "/v1/chat/completions":
            json_response(self, 404, {"error": {"message": "not found"}})
            return

        try:
            payload = read_json(self)
        except json.JSONDecodeError as exc:
            json_response(
                self,
                400,
                {"error": {"message": f"invalid JSON body: {exc}", "type": "bad_request"}},
            )
            return

        print(
            f"[Qwen3 Genie] stream={bool(payload.get('stream'))} model={payload.get('model')}",
            flush=True,
        )
        prompt = build_prompt(payload.get("messages", []))
        try:
            completion, raw = run_genie(prompt)
        except Exception as exc:
            json_response(
                self,
                500,
                {
                    "error": {
                        "message": str(exc),
                        "type": "genie_runtime_error",
                    }
                },
            )
            return

        print(
            f"[Qwen3 Genie] completion ready len={len(completion)} preview={completion[:120]!r}",
            flush=True,
        )

        if payload.get("stream"):
            stream_response(self, completion)
            return

        now = int(time.time())
        json_response(
            self,
            200,
            {
                "id": f"chatcmpl-qairt-genie-{now}",
                "object": "chat.completion",
                "created": now,
                "model": State.model_id,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": completion},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                },
                "qairt_genie": {
                    "arch": State.arch,
                    "raw_output_preview": raw[:1000],
                },
            },
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=State.host)
    parser.add_argument("--port", type=int, default=State.port)
    parser.add_argument(
        "--bundle",
        default=(
            r"C:\Users\Admin\Documents\executorch-voice-agent\models\qwen3_4b"
            r"\genie_bundle\qwen3_4b-genie-w4a16-qualcomm_snapdragon_x_elite"
        ),
    )
    parser.add_argument(
        "--qairt-root", default=r"C:\Qualcomm\AIStack\QAIRT\2.45.0.260326"
    )
    parser.add_argument(
        "--arch",
        choices=[
            "aarch64-windows-msvc",
            "arm64x-windows-msvc",
            "x86_64-windows-msvc",
        ],
        default=State.arch,
    )
    args = parser.parse_args()

    State.host = args.host
    State.port = args.port
    State.bundle_path = args.bundle
    State.qairt_root = args.qairt_root
    State.arch = args.arch

    print(f"[Qwen3 Genie] Endpoint: http://{args.host}:{args.port}/v1")
    print(f"[Qwen3 Genie] Bundle:   {State.bundle_path}")
    print(f"[Qwen3 Genie] QAIRT:    {State.qairt_root}")
    print(f"[Qwen3 Genie] Arch:     {State.arch}")
    print(
        "[Qwen3 Genie] ADSP:     "
        + os.path.join(State.qairt_root, "lib", "hexagon-v73", "unsigned")
    )
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
