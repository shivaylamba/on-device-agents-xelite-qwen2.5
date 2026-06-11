# OpenClaw Demo

This phase explores OpenClaw as an agent framework on top of the same local Foundry NPU model route.

## What This Demo Shows

OpenClaw gives us two useful test levels:

1. A direct model-provider test with `openclaw infer model run`.
2. A full agent-loop test with `openclaw agent`.

The direct model-provider test is the clean validation that OpenClaw can reach the local NPU model through LiteLLM.

## Architecture

```text
OpenClaw
  |
  v
LiteLLM OpenAI-compatible endpoint
  |
  v
Microsoft Foundry Local
  |
  v
Qwen 2.5 QNN model on Snapdragon NPU
```

## Configure OpenClaw

Use the config shape in:

```text
openclaw-demo/config/openclaw-provider.jsonc
```

The important values are:

```text
Provider id: foundry-npu
Model id: foundry-npu
Base URL: http://127.0.0.1:4001/v1
API key: sk-win-vivo2
```

## Health Checks

Before testing OpenClaw, verify Foundry and LiteLLM:

```powershell
Invoke-RestMethod http://127.0.0.1:5272/v1/models

$headers=@{Authorization='Bearer sk-win-vivo2'}
Invoke-RestMethod http://127.0.0.1:4001/v1/models -Headers $headers
```

## Test 1: Direct OpenClaw Model Inference

This is the recommended smoke test:

```powershell
openclaw infer model run --local `
  --model foundry-npu/foundry-npu `
  --prompt "Reply exactly: OpenClaw is using Foundry Local on Snapdragon NPU." `
  --json
```

Expected output:

```json
{
  "ok": true,
  "provider": "foundry-npu",
  "model": "foundry-npu",
  "outputs": [
    {
      "text": "OpenClaw is using Foundry Local on Snapdragon NPU."
    }
  ]
}
```

This proves:

```text
OpenClaw -> LiteLLM -> Foundry Local -> Snapdragon NPU
```

## Test 2: Full OpenClaw Agent Loop

This is the experimental test:

```powershell
openclaw agent --local `
  --agent main `
  --session-key agent:main:npu-smoke `
  --model foundry-npu/foundry-npu `
  --message "Reply in one short sentence: what runtime stack are you using?" `
  --thinking off `
  --timeout 300 `
  --json
```

## Current Status

The direct OpenClaw model-provider test works.

The full agent loop is experimental and may time out with the current Qwen 2.5 7B QNN NPU route. In local testing, long agent attempts also exposed low-level Foundry/QNN runtime errors in the attention layer after aborted or oversized requests.

## What The Error Means

An error mentioning `GroupQueryAttention` or sequence lengths is not a normal application error. It is a model-runtime execution error inside the NPU-backed attention layer.

In simple terms:

- direct prompt: small request, works
- full agent loop: larger request with tool schemas, planning, memory, and strict output format
- larger request can stress context/cache handling in the runtime

## Demo Recommendation

Use `openclaw infer model run` as the OpenClaw validation demo. Treat `openclaw agent` as an engineering experiment until the full loop is stable on the target hardware and model runtime.

