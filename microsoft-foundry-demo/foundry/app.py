"""
Foundry Local NPU Bridge - Snapdragon X Elite
SDK: foundry-local-sdk-winml
Endpoint: http://127.0.0.1:5272/v1

Usage:
  python app.py                  # keep-alive mode
  python app.py --test           # SDK init + chat test
  python app.py --setup-only     # one-shot setup probe, then exit

Model selection:
  $env:FOUNDRY_MODEL = 'qwen2.5-7b'       # fuller tool-calling model
  $env:FOUNDRY_MODEL = 'qwen2.5-0.5b'     # fast local smoke test
  $env:FOUNDRY_MODEL = 'deepseek-r1-7b'   # reasoning (no tool calling)
"""

import os
import sys
import time

try:
    from foundry_local_sdk import Configuration, FoundryLocalManager
except ImportError:
    print("[ERROR] foundry-local-sdk-winml is not installed.")
    print("Run: python -m pip install foundry-local-sdk-winml openai")
    sys.exit(1)

MODEL_ALIAS = os.environ.get("FOUNDRY_MODEL", "qwen2.5-7b")
FOUNDRY_PORT = int(os.environ.get("FOUNDRY_PORT", "5272"))
FOUNDRY_HOST = os.environ.get("FOUNDRY_HOST", "127.0.0.1")


def foundry_url() -> str:
    return f"http://{FOUNDRY_HOST}:{FOUNDRY_PORT}"


def init_foundry() -> FoundryLocalManager:
    print(f"[Foundry] Initializing... model={MODEL_ALIAS}")
    config = Configuration(
        app_name="snapdragon_agent",
        web=Configuration.WebService(urls=foundry_url()),
    )
    FoundryLocalManager.initialize(config)
    manager = FoundryLocalManager.instance

    current_ep = ""

    def ep_progress(ep_name: str, percent: float):
        nonlocal current_ep
        if ep_name != current_ep:
            if current_ep:
                print()
            current_ep = ep_name
        print(f"\r  EP: {ep_name:<35} {percent:5.1f}%", end="", flush=True)

    print("[Foundry] Checking execution providers (QNN/WinML)...")
    manager.download_and_register_eps(progress_callback=ep_progress)
    if current_ep:
        print()

    model = manager.catalog.get_model(MODEL_ALIAS)
    if model is None:
        print(f"[ERROR] Model not found: {MODEL_ALIAS}")
        print("Available models: foundry model list")
        sys.exit(1)

    print(f"[Foundry] Model: {MODEL_ALIAS}")
    print(f"[Foundry] Variant ID: {model.id}")
    runtime = getattr(getattr(model, "info", None), "runtime", None)
    device = getattr(runtime, "device_type", getattr(model, "device", "auto"))
    print(f"[Foundry] Device: {device}")

    def dl_progress(percent: float):
        print(f"\r  Download: {percent:.1f}%", end="", flush=True)

    model.download(dl_progress)
    print()
    print("[Foundry] Loading model onto NPU...")
    model.load()
    print("[Foundry] Starting OpenAI-compatible web service...")
    manager.start_web_service()
    print(f"[Foundry] Ready - {foundry_url()}/v1")
    print(f"[Foundry] Model ID: {model.id}")
    return manager


def print_integration_info(manager):
    m = manager.catalog.get_model(MODEL_ALIAS)
    mid = m.id if m else MODEL_ALIAS
    base_url = (manager.urls[0] if getattr(manager, "urls", None) else foundry_url()) + "/v1"
    print()
    print("=" * 55)
    print("AGENT INTEGRATION")
    print("=" * 55)
    print(f"  base_url : {base_url}")
    print("  api_key  : foundry-local")
    print(f"  model    : {mid}")
    print()
    print("Hermes custom_providers:")
    print("  - name: foundry-npu")
    print(f"    base_url: {base_url}")
    print("    api_key: foundry-local")
    print(f"    model: {mid}")
    print()
    print("LiteLLM litellm_config.yaml:")
    print(f"  model: openai/{mid}")
    print(f"  api_base: {base_url}")
    print()
    print("free-claude-code .env:")
    print(f"  LLAMACPP_BASE_URL=http://localhost:{FOUNDRY_PORT}/v1")
    print("=" * 55)


def quick_test(manager):
    try:
        import openai
    except ImportError:
        print("[WARNING] openai is not installed, skipping test.")
        return

    m = manager.catalog.get_model(MODEL_ALIAS)
    mid = m.id if m else MODEL_ALIAS
    base_url = (manager.urls[0] if getattr(manager, "urls", None) else foundry_url()) + "/v1"

    client = openai.OpenAI(
        base_url=base_url,
        api_key="foundry-local",
    )
    print("[Test] Chat completion...")
    try:
        resp = client.chat.completions.create(
            model=mid,
            messages=[{"role": "user", "content": "Say a short English greeting."}],
            max_tokens=60,
            stream=False,
        )
        print(f"[Test] Response: {resp.choices[0].message.content}")
    except Exception as e:
        print(f"[Test] Error: {e}")
        print("[INFO] Keep this bridge running; the SDK web service owns the loaded model.")


def main():
    print()
    print("=" * 55)
    print("Foundry Local NPU Bridge - Snapdragon X Elite")
    print(f"Model: {MODEL_ALIAS}  Port: {FOUNDRY_PORT}")
    print("=" * 55)
    print()

    manager = init_foundry()
    print_integration_info(manager)

    if "--test" in sys.argv:
        quick_test(manager)

    if "--setup-only" in sys.argv:
        print("[INFO] Setup probe complete. Keep-alive mode is required for a persistent endpoint.")
        return

    print("[Foundry] Running - press Ctrl+C to stop")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n[Foundry] Stopping...")
        manager.stop_web_service()
        m = manager.catalog.get_model(MODEL_ALIAS)
        if m:
            m.unload()
        print("[Foundry] Model unloaded from memory.")


if __name__ == "__main__":
    main()
