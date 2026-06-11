# Open WebUI Demo Launcher

This runs Open WebUI as the chat interface for the local Foundry NPU endpoint.

```powershell
.\foundry\start-foundry.ps1
.\.openwebui-venv\Scripts\python.exe .\openwebui\install-demo-agent.py
.\openwebui\start-openwebui.ps1
```

Open WebUI will be available at:

```text
http://127.0.0.1:8080
```

The launcher sets:

- `OPENAI_API_BASE_URLS=http://127.0.0.1:5272/v1`
- `OPENAI_API_KEYS=foundry-local`
- `DEFAULT_MODELS=snapdragon-npu-agent`
- `WEBUI_AUTH=False`

The installer creates:

- Native Open WebUI tool: `snapdragon_npu_demo`
- Workspace model wrapper: `snapdragon-npu-agent`
- Always-on model tool IDs: `snapdragon_npu_demo`
- Reliable pipe model: `snapdragon_npu_agent_pipe`

The demo now defaults to the Qwen2.5 7B NPU model:

```text
qwen2.5-7b-instruct-qnn-npu
```

For a smaller smoke-test model, start Foundry with another model and pass the Open WebUI model ID:

```powershell
$env:FOUNDRY_MODEL = "qwen2.5-1.5b"
.\foundry\start-foundry.ps1
.\openwebui\start-openwebui.ps1 -Model "qwen2.5-1.5b-instruct-qnn-npu"
```

After changing the base model, rerun:

```powershell
$env:OPENWEBUI_BASE_MODEL = "qwen2.5-1.5b-instruct-qnn-npu"
.\.openwebui-venv\Scripts\python.exe .\openwebui\install-demo-agent.py
```
