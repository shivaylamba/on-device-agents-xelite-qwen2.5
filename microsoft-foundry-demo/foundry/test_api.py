import json
import time
import urllib.request

BASE = "http://127.0.0.1:5272"
# Adjust these values if `foundry model list` reports different variant IDs.
MODELS = {
    "qwen2.5-0.5b-npu-rest": "qwen2.5-0.5b-instruct-qnn-npu",
    "qwen2.5-0.5b-npu": "qwen2.5-0.5b-instruct-qnn-npu:1",
    "qwen2.5-1.5b-npu-rest": "qwen2.5-1.5b-instruct-qnn-npu",
    "qwen2.5-1.5b-npu": "qwen2.5-1.5b-instruct-qnn-npu:3",
    "deepseek-r1-7b": "deepseek-r1-distill-qwen-7b-qnn-npu:2",
    "qwen2.5-7b-npu-rest": "qwen2.5-7b-instruct-qnn-npu",
    "qwen2.5-7b": "qwen2.5-7b-instruct-qnn-npu:3",
}


def get(path, timeout=10):
    req = urllib.request.Request(BASE + path)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def post(path, payload, timeout=90):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE + path,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.loads(r.read())
    return resp, time.time() - t0


print("=== /v1/models ===")
try:
    data = get("/v1/models")
    loaded = [m["id"] for m in data.get("data", [])]
    for mid in loaded:
        print(f"  {mid}")
except Exception as e:
    print(f"  ERROR: {e}")
    print("  Run: $env:FOUNDRY_MODEL='qwen2.5-0.5b'; python foundry/app.py")
    exit(1)

active_model = None
for alias, variant_id in MODELS.items():
    if variant_id in loaded:
        active_model = variant_id
        print(f"\nActive model: {alias} ({variant_id})")
        break

if not active_model:
    print("\nNo NPU model is loaded.")
    print("Run: $env:FOUNDRY_MODEL='qwen2.5-0.5b'; python foundry/app.py")
    exit(1)

print("\nWaiting for the service to stabilize...")
for i in range(6):
    time.sleep(2)
    try:
        get("/v1/models", timeout=3)
        print(f"  [{i + 1}] OK")
        break
    except Exception as e:
        print(f"  [{i + 1}] Waiting... ({type(e).__name__})")

print("\n=== Chat test ===")
try:
    resp, elapsed = post(
        "/v1/chat/completions",
        {
            "model": active_model,
            "messages": [{"role": "user", "content": "Say five English words."}],
            "max_tokens": 60,
            "stream": False,
        },
    )
    content = resp["choices"][0]["message"]["content"]
    usage = resp.get("usage", {})
    ctoks = usage.get("completion_tokens", 0)
    print(f"  Response ({elapsed:.1f}s): {content}")
    if ctoks:
        print(f"  Tokens: {ctoks} | {ctoks / elapsed:.1f} tok/s")
    else:
        print("  (completion_tokens is unavailable due to a Foundry 0.8.119 bug)")
except Exception as e:
    print(f"  ERROR: {e}")
    print("  Tip: keep foundry/app.py running and retry after the model finishes loading.")

if "qwen2.5" in active_model:
    print("\n=== Tool calling test (Qwen2.5-7B) ===")
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "Returns the current time",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }
    ]
    try:
        resp, elapsed = post(
            "/v1/chat/completions",
            {
                "model": active_model,
                "messages": [
                    {
                        "role": "user",
                        "content": "What is the current time? Use the get_current_time tool.",
                    }
                ],
                "tools": tools,
                "tool_choice": "required",
                "max_tokens": 100,
                "stream": False,
            },
            timeout=30,
        )
        choice = resp["choices"][0]
        if choice.get("message", {}).get("tool_calls"):
            tc = choice["message"]["tool_calls"][0]
            print(f"  Tool call: {tc['function']['name']} ({elapsed:.1f}s)")
            print("  Tool calling: OK")
        else:
            print(f"  Tool calling: not called ({elapsed:.1f}s)")
            print(f"  Content: {choice.get('message', {}).get('content', '')[:100]}")
    except Exception as e:
        print(f"  ERROR: {e}")
