# Microsoft Foundry Demo

This phase demonstrates local inference on Snapdragon NPU using Microsoft Foundry Local, Qwen 2.5, LiteLLM, and Open WebUI.

## What This Demo Shows

- A Qwen 2.5 model running locally through Microsoft Foundry Local.
- NPU-backed execution through the QNN model build.
- An OpenAI-compatible API layer through LiteLLM.
- A polished chat UI through Open WebUI.

## Included Code

```text
microsoft-foundry-demo/
|-- foundry/
|   |-- app.py
|   |-- start-foundry.ps1
|   `-- test_api.py
|-- litellm/
|   `-- start-litellm.ps1
|-- safe-proxy/
|   |-- safe_npu_proxy.py
|   `-- start-safe-proxy.ps1
|-- openwebui/
|   |-- start-openwebui.ps1
|   |-- install-demo-agent.py
|   |-- functions/
|   |   `-- snapdragon_npu_agent_pipe.py
|   `-- tools/
|       `-- snapdragon_npu_demo.py
|-- demo-ui/
|   |-- server.py
|   `-- static/
|-- config/
|   `-- litellm-foundry.yaml
`-- scripts/
    |-- start-demo-stack.ps1
    |-- restart-npu-runtime.ps1
    |-- health-check.ps1
    |-- test-safe-proxy.ps1
    `-- upgrade-foundry-local.ps1
```

## Architecture

```text
User
  |
  v
Open WebUI
  |
  v
LiteLLM proxy
  |
  v
Safe serialized NPU proxy
  |
  v
Foundry Local /v1 endpoint
  |
  v
Qwen 2.5 QNN model on Snapdragon NPU
```

Open WebUI is used here only as the user interface. The model itself is still running locally through Foundry Local. The safe proxy exists to keep agent-style traffic from overwhelming the QNN NPU session.

## Model Route

The intended model route is:

```text
Open WebUI model name: foundry-npu
LiteLLM model name: foundry-npu
Safe proxy endpoint: http://127.0.0.1:5299/v1
Foundry model id: qwen2.5-7b-instruct-qnn-npu
Runtime: Microsoft Foundry Local
Device: Snapdragon NPU
```

## Check Or Upgrade Foundry Local

```powershell
.\scripts\upgrade-foundry-local.ps1
```

If winget reports no upgrade, continue with the safe proxy path below. The proxy mitigations are still useful on older Foundry versions.

On the tested machine, winget reported no newer package than Foundry Local `0.8.119`.

## Start Foundry Local

Start Foundry Local with the included bridge:

```powershell
cd microsoft-foundry-demo
$env:PYTHON = "C:\Program Files\Python312-arm64\python.exe"
$env:FOUNDRY_MODEL = "qwen2.5-7b"
$env:FOUNDRY_PORT = "5272"
.\foundry\start-foundry.ps1
```

The expected endpoint is:

```text
http://127.0.0.1:5272/v1
```

Verify the model endpoint:

```powershell
Invoke-RestMethod http://127.0.0.1:5272/v1/models
```

You should see a model similar to:

```text
qwen2.5-7b-instruct-qnn-npu
```

## Start LiteLLM

Start the safe proxy first:

```powershell
.\safe-proxy\start-safe-proxy.ps1 `
  -Python "C:\Program Files\Python312-arm64\python.exe" `
  -Upstream http://127.0.0.1:5272/v1 `
  -Port 5299
```

Test the safe proxy:

```powershell
.\scripts\test-safe-proxy.ps1
```

Then start LiteLLM. The included LiteLLM config points at the safe proxy, not raw Foundry:

```powershell
.\litellm\start-litellm.ps1 -HostName 127.0.0.1 -Port 4001
```

Verify the LiteLLM route:

```powershell
$headers=@{Authorization='Bearer sk-win-vivo2'}
Invoke-RestMethod http://127.0.0.1:4001/v1/models -Headers $headers
```

Expected model:

```text
foundry-npu
```

## Connect Open WebUI

In Open WebUI, add an OpenAI-compatible connection:

```text
Base URL: http://127.0.0.1:4001/v1
API Key: sk-win-vivo2
Model: foundry-npu
```

Then start a chat using `foundry-npu`.

To run the included Open WebUI launcher:

```powershell
.\openwebui\start-openwebui.ps1 -HostName 127.0.0.1 -Port 8080
```

By default this points Open WebUI at LiteLLM:

```text
http://127.0.0.1:4001/v1
```

To install the included demo pipe/tool into Open WebUI's local database:

```powershell
.\.openwebui-venv\Scripts\python.exe .\openwebui\install-demo-agent.py
```

To run the smaller custom UI created during local testing:

```powershell
python .\demo-ui\server.py --host 127.0.0.1 --port 8081
```

## One-Command Local Launcher

The helper script starts Foundry, waits for the model endpoint, starts LiteLLM, and then starts Open WebUI:

```powershell
.\scripts\start-demo-stack.ps1
```

To recover after a `GroupQueryAttention` or `seqlens_k` failure:

```powershell
.\scripts\restart-npu-runtime.ps1
```

To verify the whole stack:

```powershell
.\scripts\health-check.ps1
```

## Demo Prompts

Use short prompts first:

```text
Explain in one paragraph why on-device AI matters for enterprise PCs.
```

```text
Create a concise Qualcomm demo narration for a Snapdragon NPU running a local Qwen model.
```

```text
Summarize the benefits of local inference: latency, privacy, cost, and offline use.
```

## What To Highlight

- The request stays local on the Windows device.
- The model is served from Foundry Local.
- The QNN model targets Snapdragon NPU acceleration.
- Open WebUI is only the frontend, not the model host.
- LiteLLM makes the local runtime compatible with OpenAI-style tooling.

## Known Limitations

The Open WebUI chat path is the most reliable demo path. Full agent loops are tested separately in the Hermes and OpenClaw folders because they add heavier prompts, tool schemas, and structured output requirements.

The safe proxy reduces the chance of NPU attention/cache failures, but it cannot fully fix bugs inside the Foundry/QNN runtime. If the error appears, restart the NPU runtime and retry with a smaller prompt.
