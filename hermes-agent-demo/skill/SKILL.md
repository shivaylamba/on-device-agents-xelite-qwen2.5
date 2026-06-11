---
name: foundry-npu
description: "Operate Foundry Local NPU: start Snapdragon X Elite NPU models, configure tool calling, bridge through LiteLLM, and troubleshoot Qwen2.5-7B NPU agent usage."
version: 1.1.0
author: OWL
tags: [npu, foundry, litellm, qwen, snapdragon, tool-calling, local-llm, windows]
---

# Foundry Local NPU - Skill

## Trigger Conditions

Use this skill when the user asks about:

- Starting Foundry or the Foundry service.
- Loading an NPU model or starting Qwen on NPU.
- NPU tool calling or Qwen agent mode.
- Foundry errors such as connection refused on port 5272.
- LiteLLM routing to Foundry or an NPU proxy.
- Running DeepSeek-R1 locally on NPU.

## System Architecture

```text
Hermes Agent
  |
  +-- custom_providers[foundry-npu]  ->  http://localhost:4001/v1  (LiteLLM)
  |                                                 |
  |                                         LiteLLM :4001
  |                                                 |
  |                                         Foundry :5272
  |                                                 |
  |                                    QNN EP (Hexagon HTP NPU)
  |                                                 |
  |                             Qwen2.5-7B-Instruct NPU (tool calling)
  |                             DeepSeek-R1-7B NPU    (reasoning)
  |
  +-- direct access without LiteLLM:
        custom_providers[foundry-npu-direct]  ->  http://localhost:5272/v1
```

## NPU Models (current as of 2026-05-31)

| Alias | Variant ID (Foundry) | Device | Tool Calling | Size |
|-------|----------------------|--------|--------------|------|
| `qwen2.5-7b` | `qwen2.5-7b-instruct-qnn-npu:3` | NPU | YES | 6.8 GB |
| `deepseek-r1-7b` | `deepseek-r1-distill-qwen-7b-qnn-npu:2` | NPU | NO | 3.7 GB |
| `qwen2.5-1.5b` | `qwen2.5-1.5b-instruct-qnn-npu:3` | NPU | YES | ~1 GB |
| `phi-4-mini-reasoning` | `Phi-4-mini-reasoning-qnn-npu` | NPU | NO | 2.78 GB |
| `phi-3-mini-4k` | `Phi-3-mini-4k-instruct-generic-cpu:3` | CPU | NO | 2.5 GB |

Default agent model: `qwen2.5-7b` - NPU, tool calling, works well for English.
Reasoning model: `deepseek-r1-7b` - NPU, chain-of-thought style reasoning, no tool calling.

## Startup

### 1. Foundry Service (required)

```powershell
cd .\foundry
$env:FOUNDRY_MODEL = 'deepseek-r1-7b'   # or 'qwen2.5-7b'
.\start-foundry.ps1
```

Successful startup: `[Foundry] Ready - http://127.0.0.1:5272/v1`

Load a model separately if the service is already running:

```powershell
foundry model load deepseek-r1-7b
# Expected: "Model deepseek-r1-7b loaded successfully"
```

### 2. LiteLLM Proxy (optional Hermes routing)

```powershell
cd C:\AI\apps\litellm-win
.\start.ps1
```

### 3. API Test

```powershell
python .\foundry\test_api.py
```

## Hermes custom_providers Config

### Via LiteLLM (recommended for agent usage and tool-calling routing)

```yaml
custom_providers:
- api_key: sk-win-vivo2
  api_mode: chat_completions
  base_url: http://localhost:4001/v1
  model: foundry-npu
  name: foundry-npu
```

### Direct Foundry API (without LiteLLM)

```yaml
custom_providers:
- api_key: foundry-local
  api_mode: chat_completions
  base_url: http://localhost:5272/v1
  model: deepseek-r1-distill-qwen-7b-qnn-npu:2
  name: foundry-npu
```

## Tool Calling

| Mode | Qwen2.5-7B | DeepSeek-R1-7B |
|------|------------|----------------|
| `required` | YES | NO |
| `auto` | limited | NO |
| `none` | YES | YES |

Foundry natively converts Qwen `<tool_call>` XML into OpenAI `tool_calls` JSON.

## Performance (reference machine)

| Model | Response Time | Tokens/s (estimate) | Context |
|-------|---------------|---------------------|---------|
| Qwen2.5-7B NPU | 3-5s | ~15-25 | 28672 |
| DeepSeek-R1-7B NPU | 2-4s | ~20-30 | 32768 |

## Known Issues

- `DSP_INFO UNSUPPORTED_KEY: 49/50` is a normal QNN warning and can be ignored.
- `Failed to process model #0 on page 1` is a Foundry 0.8.119 catalog bug and does not block inference.
- The REST API may need ~5 seconds after model load before it responds reliably.
- `usage.completion_tokens` is not returned by Foundry 0.8.119, so tokens/s cannot be calculated automatically.

## Troubleshooting

### Connection Refused on :5272

```powershell
cd .\foundry
$env:FOUNDRY_MODEL = 'qwen2.5-0.5b'
.\start-foundry.ps1 --test
cd .\foundry
.\start-foundry.ps1
```

### Connection Refused on :4001

```powershell
cd C:\AI\apps\litellm-win
.\start.ps1
```

### Model Does Not Respond (WinError 10054)

```powershell
# Wait 5-10 seconds after model load, then retry.
foundry model load qwen2.5-7b
Start-Sleep 8
python .\foundry\test_api.py
```

### Switch Models

```powershell
foundry model unload deepseek-r1-7b
foundry model load qwen2.5-7b
```
