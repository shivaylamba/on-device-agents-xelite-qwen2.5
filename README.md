# On-Device Agents on Snapdragon X Elite with Qwen 2.5

This repository is organized as a multi-phase demo path for running local AI experiences on Snapdragon X Elite class Windows devices with Qualcomm NPU acceleration.

The goal is to show a practical progression:

1. Run a Qwen 2.5 model locally through Microsoft Foundry Local on the Snapdragon NPU.
2. Put a usable chat interface on top with Open WebUI for the Foundry demo.
3. Explore agent frameworks, first with Hermes and then with OpenClaw, using the same local NPU-backed model route.
4. Explore lower-level QAIRT paths that target the HTP/NPU without Microsoft Foundry Local.

## Repository Structure

```text
.
|-- microsoft-foundry-demo/
|   |-- README.md
|   |-- config/
|   |   `-- litellm-foundry.yaml
|   |-- foundry/
|   |-- litellm/
|   |-- openwebui/
|   |-- demo-ui/
|   |-- safe-proxy/
|   `-- scripts/
|-- hermes-agent-demo/
|   |-- README.md
|   |-- config/
|   |   `-- hermes-custom-provider.yaml
|   |-- profiles/
|   |-- skill/
|   |-- cron/
|   `-- scripts/
|-- openclaw-demo/
|   |-- README.md
|   |-- config/
|   |   `-- openclaw-provider.jsonc
|   `-- scripts/
|-- qairt-onnx-demo/
|   |-- README.md
|   |-- runtime/
|   |-- scripts/
|   `-- openclaw/
|-- qairt-genie-demo/
|   |-- README.md
|   |-- runtime/
|   |-- scripts/
|   `-- openclaw/
`-- README.md
```

## Architecture

The core runtime path is:

```text
User
  |
  v
Open WebUI / Hermes / OpenClaw
  |
  v
LiteLLM OpenAI-compatible proxy
  |
  v
Safe serialized NPU proxy
  |
  v
Microsoft Foundry Local
  |
  v
Qwen 2.5 QNN model on Snapdragon NPU
```

Foundry Local is the model runtime. The safe proxy serializes requests, clamps long contexts, and disables OpenAI-style parallel tool payloads before traffic reaches the QNN NPU session. LiteLLM then exposes that protected route as an OpenAI-compatible API that tools and agent frameworks can consume. Open WebUI gives us the most reliable demo surface for conversation. Hermes and OpenClaw are used to explore agent loops on the same local backend.

## Current Demo Status

| Phase | Goal | Status |
| --- | --- | --- |
| Microsoft Foundry demo | Local Qwen 2.5 inference on Snapdragon NPU with Open WebUI | Primary working demo path |
| Hermes agent demo | Run Hermes against the Foundry NPU model through LiteLLM | Experimental |
| OpenClaw demo | Run OpenClaw against the Foundry NPU model through LiteLLM | Model inference works; minimal full-agent smoke test works |
| QAIRT / ONNX Runtime QNN demo | Run QNN Execution Provider directly against HTP/NPU without Foundry | Scaffold plus local QNN EP probe |
| QAIRT Genie Qwen3 demo | Run a local Qwen3-4B Genie bundle directly on HTP/NPU | Direct Genie inference works with `ADSP_LIBRARY_PATH` set |

## Why Three Phases?

The phases separate the demo into clear layers:

- **Foundry Local + Open WebUI** proves the local model and NPU path.
- **Hermes** tests whether an agent framework can use the same local model route.
- **OpenClaw** tests a second agent framework and gives a more direct model-provider validation path.
- **QAIRT / ONNX Runtime QNN EP** tests the lower-level HTP runtime path for ONNX models without Foundry Local's model catalog or chat server.
- **QAIRT Genie** tests a compiled LLM bundle path where Genie owns tokenization and text generation.

This separation is important because simple local inference and full agent execution are not the same workload. A direct prompt can succeed while a full agent loop may fail due to longer prompts, structured output requirements, tool definitions, retries, or runtime context handling.

## Prerequisites

- Windows on Snapdragon X Elite or compatible Snapdragon NPU hardware.
- Microsoft Foundry Local installed.
- Python 3.11 or 3.12.
- A local Qwen 2.5 QNN/NPU model available through Foundry Local.
- LiteLLM for the OpenAI-compatible proxy.
- Open WebUI for the UI demo.
- Hermes CLI for the Hermes phase.
- OpenClaw CLI for the OpenClaw phase.

## Suggested Demo Flow

1. Start with `microsoft-foundry-demo`.
2. Verify Foundry Local exposes the Qwen 2.5 NPU model.
3. Start LiteLLM using `microsoft-foundry-demo/config/litellm-foundry.yaml`.
4. Connect Open WebUI to LiteLLM.
5. Run prompts that highlight local, private, on-device inference.
6. Move to `hermes-agent-demo` to show the attempted Hermes integration path.
7. Move to `openclaw-demo` to show the OpenClaw model-provider validation and agent-loop experiment.

## What Code Is Included

This repository now includes the runnable assets used during local testing:

- Foundry Local Python bridge: `microsoft-foundry-demo/foundry/app.py`
- Foundry launcher and test client: `microsoft-foundry-demo/foundry/`
- LiteLLM launcher and config: `microsoft-foundry-demo/litellm/` and `microsoft-foundry-demo/config/`
- Safe serialized NPU proxy: `microsoft-foundry-demo/safe-proxy/`
- Open WebUI launcher, installer, pipe, and tool code: `microsoft-foundry-demo/openwebui/`
- Small custom demo UI created during testing: `microsoft-foundry-demo/demo-ui/`
- Hermes provider/profile/skill/cron assets: `hermes-agent-demo/`
- OpenClaw provider config and smoke-test scripts: `openclaw-demo/`
- QAIRT / ONNX Runtime QNN EP probe, runner, and agent server scaffold: `qairt-onnx-demo/`
- QAIRT Genie Qwen3 runner, OpenAI-compatible shim, and OpenClaw provider config: `qairt-genie-demo/`

## Important Note About Agent Loops

The Foundry Local NPU model can answer direct prompts, but full agent frameworks add heavier prompts, tool schemas, planning instructions, memory/session metadata, and strict response formatting. That larger workload can expose runtime or compatibility issues that do not appear in plain chat.

For a reliable public demo, use Open WebUI as the main interface and frame Hermes/OpenClaw as agent-framework integration experiments unless the full agent loop has been validated on the target device.

## NPU Runtime Safety

The `GroupQueryAttention seqlens_k[0] is out of range` failure is handled as a runtime safety issue, not as an ordinary application exception. The repo includes these mitigations:

- `microsoft-foundry-demo/safe-proxy/` serializes all NPU chat completion requests.
- requests are clamped to small output sizes by default.
- long message history is trimmed before reaching Foundry.
- OpenAI tool payloads are stripped by default for the NPU route.
- `microsoft-foundry-demo/scripts/restart-npu-runtime.ps1` clears a dirty NPU session after a runtime failure.
- `microsoft-foundry-demo/scripts/upgrade-foundry-local.ps1` checks for a newer Foundry Local runtime.
- `openclaw-demo/workspace-minimal/` keeps OpenClaw startup context small enough for the NPU route.
