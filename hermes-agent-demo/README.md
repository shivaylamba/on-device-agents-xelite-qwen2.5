# Hermes Agent Demo

This phase explores Hermes as an agent framework on top of the same local Foundry NPU model route.

## What This Demo Tries To Prove

The goal is to test whether Hermes can use a local NPU-backed model as its LLM backend:

```text
Hermes
  |
  v
LiteLLM
  |
  v
Microsoft Foundry Local
  |
  v
Qwen 2.5 QNN model on Snapdragon NPU
```

## Included Assets

```text
hermes-agent-demo/
|-- config/
|   |-- hermes-custom-provider.yaml
|   `-- hermes-custom-providers.yaml
|-- profiles/
|   `-- npu-agent/
|-- skill/
|   `-- SKILL.md
|-- cron/
|-- scripts/
|   |-- NPU_INDEXER.md
|   `-- test-hermes-agent.ps1
`-- README.md
```

## Why LiteLLM Is Used

Hermes expects a model provider it can talk to through a standard API shape. LiteLLM acts as the compatibility layer:

- Hermes sends OpenAI-style requests to LiteLLM.
- LiteLLM forwards those requests to Foundry Local.
- Foundry Local runs the Qwen 2.5 QNN model on the NPU.

## Configure Hermes

Use the provider shape in:

```text
hermes-agent-demo/config/hermes-custom-provider.yaml
```

The important values are:

```text
Provider/base URL: http://127.0.0.1:4001/v1
API key: sk-win-vivo2
Model name: foundry-npu
```

## Health Checks

Before testing Hermes, verify the backend route:

```powershell
Invoke-RestMethod http://127.0.0.1:5272/v1/models

$headers=@{Authorization='Bearer sk-win-vivo2'}
Invoke-RestMethod http://127.0.0.1:4001/v1/models -Headers $headers
```

The LiteLLM response should include:

```text
foundry-npu
```

## Example Hermes Test

Use a short prompt first:

```powershell
.\scripts\test-hermes-agent.ps1
```

If Hermes supports selecting the configured profile, select the profile that points at:

```text
foundry-npu through http://127.0.0.1:4001/v1
```

## Current Status

This path is experimental.

In local testing, the same backend can answer direct prompts through Foundry and LiteLLM, but full Hermes agent turns may hang or time out. That does not mean Foundry Local or the NPU model is broken. It means the full agent loop is a heavier workload than a simple chat completion.

## Why Agent Turns Are Harder Than Chat

A direct prompt looks like:

```text
User prompt -> model response
```

A Hermes agent turn may include:

- system instructions
- agent rules
- tool definitions
- structured output expectations
- retry behavior
- session state
- planning instructions

That larger prompt and stricter response format can expose model/runtime limitations that do not appear in simple chat.

## Demo Recommendation

For a public Qualcomm demo, use this phase to explain the integration path and current engineering learnings. Use the Microsoft Foundry + Open WebUI phase as the primary working demo unless the Hermes loop has been validated on the target device.
