# Architecture - Hermes Foundry NPU Integration

## Full System Design (reference machine, 2026-05-31)

```text
+----------------------------------------------------------------+
| HERMES AGENT (Windows)                                         |
| C:\Users\<you>\AppData\Local\hermes\                           |
|                                                                |
| Profiles:                                                      |
|   default / orchestrator     npu-agent          coder/writer   |
|   openrouter                 foundry-npu        openrouter     |
|                              NPU-backed                        |
|                                                                |
| custom_providers: foundry-npu -> :4001/v1                      |
+----------------------------|-----------------------------------+
                             v
+----------------------------------------------------------------+
| LiteLLM Proxy (:4001)                                          |
| C:\AI\apps\litellm-win\                                       |
|                                                                |
| model_list:                                                    |
|   foundry-npu          -> openai/qwen2.5-7b-instruct-qnn-npu:3 |
|   foundry-npu-deepseek -> openai/deepseek-r1-distill-...-npu:2 |
|   genie-npu            -> openai/llama3.1-8b-8380-qnn2.38      |
|   lm-studio            -> openai/local-model                   |
|   hermes-groq          -> openai/groq-fast                     |
|                                                                |
| fallback: foundry-npu -> lm-studio -> hermes-groq              |
+----------------------------|-----------------------------------+
                             v
+----------------------------------------------------------------+
| Foundry Local Service (:5272)                                  |
|                                                                |
| Install: winget Microsoft.FoundryLocal v0.8.119.102            |
| Cache: E:\models\foundry\                                      |
| Port: 5272                                                     |
|                                                                |
| Execution providers:                                           |
|   QNNExecutionProvider    -> Hexagon HTP NPU                   |
|   CPUExecutionProvider    -> fallback                          |
|   WebGpuExecutionProvider -> GPU fallback                      |
|                                                                |
| REST API: OpenAI-compatible /v1/chat/completions               |
+----------------------------|-----------------------------------+
                             v
+----------------------------------------------------------------+
| Snapdragon X Elite X1E78100 NPU                                |
| Hexagon v73 DSP / HTP                                          |
|                                                                |
| Downloaded models:                                             |
|   qwen2.5-7b-instruct-qnn:2    2.8G   tool call YES   NPU      |
|   deepseek-r1-7b-qnn:2         3.7G   tool call NO    NPU      |
|   Phi-3-mini-4k-cpu:3          2.5G   tool call NO    CPU      |
+----------------------------------------------------------------+
```

Parallel NPU stack, independent from Foundry:

```text
GenieAPIService (:8912) - llama3.1-8B QNN
C:\AI\AI-hub\  |  QAIRT SDK 2.45.40
LiteLLM genie-npu model -> :8912
```

## Data Flow - Hermes Agent Request

```text
Hermes npu-agent profile
  |
  [1] Hermes -> foundry-npu custom provider
      POST http://localhost:4001/v1/chat/completions
      model: foundry-npu
  |
  [2] LiteLLM :4001 -> model routing
      foundry-npu -> openai/qwen2.5-7b-instruct-qnn-npu:3
      api_base: http://localhost:5272/v1
  |
  [3] Foundry :5272 -> QNN EP -> Hexagon HTP NPU
      response in about 3-5 seconds
  |
  [4] LiteLLM -> Hermes -> tool_calls processing
```

## Alternate Access Modes

```text
# Direct access without LiteLLM
Hermes -> foundry-npu (direct) -> http://localhost:5272/v1

# free-claude-code
fcc -> LLAMACPP_BASE_URL=http://localhost:5272/v1

# Bifrost gateway
Bifrost :4000 -> foundry-local provider -> :5272

# Python SDK
from foundry_local_sdk import FoundryLocalManager
-> .\foundry\app.py
```

## Component Status (2026-05-31)

| Component | Version | Status | Port |
|-----------|---------|--------|------|
| Foundry CLI | 0.8.119.102 | active | - |
| Foundry Service | 0.8.119 | running | 5272 |
| foundry-local-sdk | PyPI latest | installed | - |
| LiteLLM | Windows build | running | 4001 |
| QNN EP | v2.45.40 | registered | - |
| Qwen2.5-7B NPU | qnn-npu:2 | downloaded | - |
| DeepSeek-R1-7B NPU | qnn-npu:2 | downloaded | - |
| GenieAPIService | QAIRT 2.45.40 | running | 8912 |

## Known Limitations

- Foundry CLI v1.2.0 was not available through winget at the time of the original demo.
- `foundry cache list` can return `500 Internal Server Error` on Foundry 0.8.119.
- `usage.completion_tokens` is `0` in some REST responses on Foundry 0.8.119.
- The REST API may need 5-10 seconds to stabilize after model load.
- `DSP_INFO UNSUPPORTED_KEY: 49/50` is a normal QNN warning.
