# OpenClaw Demo

This phase explores OpenClaw as an agent framework on top of the same local Foundry NPU model route.

## What This Demo Shows

OpenClaw gives us two useful test levels:

1. A direct model-provider test with `openclaw infer model run`.
2. A full agent-loop test with `openclaw agent`.

The direct model-provider test is the clean validation that OpenClaw can reach the local NPU model through LiteLLM.

## Included Assets

```text
openclaw-demo/
|-- config/
|   `-- openclaw-provider.jsonc
|-- scripts/
|   |-- apply-openclaw-config.ps1
|   |-- test-openclaw-infer.ps1
|   `-- test-openclaw-agent.ps1
|-- workspace-minimal/
|   |-- AGENTS.md
|   `-- USER.md
`-- README.md
```

## Architecture

```text
OpenClaw
  |
  v
LiteLLM OpenAI-compatible endpoint
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

LiteLLM should be configured to route `foundry-npu` through:

```text
http://127.0.0.1:5299/v1
```

That safe proxy serializes and clamps NPU requests before forwarding them to raw Foundry Local.

The apply script also points OpenClaw at `workspace-minimal`, disables code mode, and limits concurrency. This keeps the OpenClaw system prompt small enough for the NPU-backed model route.

Apply the config patch to the local OpenClaw config:

```powershell
.\scripts\apply-openclaw-config.ps1
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
.\scripts\test-openclaw-infer.ps1
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
.\scripts\test-openclaw-agent.ps1
```

## Current Status

The direct OpenClaw model-provider test works.

The minimal full-agent smoke test also works when OpenClaw is configured with:

- the safe serialized NPU proxy
- `tools.profile = minimal`
- `codeMode.enabled = false`
- a tiny workspace under `workspace-minimal`
- concurrency set to 1

In local testing, the full-agent smoke test returned:

```text
protected agent route works.
```

Heavier OpenClaw workspaces or code-mode prompts can still overflow OpenClaw's own precheck before a request reaches the NPU model. The safe proxy reduces the chance of low-level Foundry/QNN attention-layer failures after aborted or oversized requests, but it cannot fully fix runtime bugs inside the NPU execution provider.

## What The Error Means

An error mentioning `GroupQueryAttention` or sequence lengths is not a normal application error. It is a model-runtime execution error inside the NPU-backed attention layer.

In simple terms:

- direct prompt: small request, works
- full agent loop: larger request with tool schemas, planning, memory, and strict output format
- larger request can stress context/cache handling in the runtime

## Demo Recommendation

Use `openclaw infer model run` as the simplest OpenClaw validation demo. Use `openclaw agent` only with the included minimal workspace/config for public demos.
