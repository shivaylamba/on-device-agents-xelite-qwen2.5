# QAIRT / ONNX Runtime QNN EP Demo

This folder explores the lower-level Snapdragon HTP/NPU path:

```text
Agent or local app
  |
  v
OpenAI-compatible shim or direct Python runner
  |
  v
ONNX Runtime
  |
  v
QNN Execution Provider
  |
  v
QAIRT / QNN HTP backend
  |
  v
Snapdragon X Elite HTP/NPU
```

This is different from the Microsoft Foundry demo. Foundry Local gives us a model catalog, model download/load, tokenizer handling, and an OpenAI-compatible chat service. QAIRT / ONNX Runtime QNN EP is lower level: you bring a QNN-compatible ONNX or ORT GenAI model, and ONNX Runtime runs the graph through the Qualcomm QNN backend.

## Current Local Finding

On this machine, the Python package `onnxruntime-qnn` is installed and can register `QNNExecutionProvider`:

```text
onnxruntime-qnn: installed
QNN EP library: onnxruntime_providers_qnn.dll
HTP backend: QnnHtp.dll
```

Plain `import onnxruntime` initially lists CPU/Azure providers only. The QNN provider must be registered from the `onnxruntime_qnn` package before creating sessions.

## Important Model Requirement

The QNN HTP backend is not a drop-in runtime for arbitrary floating-point ONNX models. It generally needs a QNN-supported, static-shape, quantized model. A tiny floating-point toy graph may run through CPU fallback, which is not proof that the NPU executed it.

For LLM-style agents, this path also needs a tokenizer and generation loop, usually via an ONNX Runtime GenAI-compatible model package or custom generation code.

## Install / Check

```powershell
cd "C:\Users\Admin\Documents\microsoft foundary\on-device-agents-xelite-qwen2.5"

.\qairt-onnx-demo\scripts\check-qnn-ep.ps1
```

If `onnxruntime-qnn` is missing:

```powershell
python -m pip install onnxruntime-qnn
```

## Probe QNN EP

```powershell
.\qairt-onnx-demo\scripts\check-qnn-ep.ps1
```

Expected:

```text
QNNExecutionProvider registered: true
QnnHtp.dll found: true
QnnCpu.dll found: true
```

## Run an ONNX Model with QNN EP

Put a QNN-compatible model under:

```text
qairt-onnx-demo/models/
```

Then run:

```powershell
.\qairt-onnx-demo\scripts\run-onnx-qnn.ps1 `
  -Model .\qairt-onnx-demo\models\your-model.onnx `
  -Backend htp
```

The runner accepts optional JSON inputs:

```powershell
.\qairt-onnx-demo\scripts\run-onnx-qnn.ps1 `
  -Model .\qairt-onnx-demo\models\your-model.onnx `
  -Backend htp `
  -Inputs .\qairt-onnx-demo\models\sample-inputs.json
```

If QNN cannot own the graph, the runner reports the actual session providers and warns about CPU fallback.

## Toy Model Fallback Check

This repo includes a tiny FP32 Add model generator:

```powershell
.\qairt-onnx-demo\scripts\test-toy-model.ps1 -Backend htp
```

This is mainly a sanity check for the runner. On many Snapdragon HTP/QNN setups, this tiny floating-point model will fall back to `CPUExecutionProvider`. That is expected and useful: it proves the script is honest about whether QNN actually owns the graph.

## Agent Server Scaffold

This folder also includes an OpenAI-compatible server scaffold:

```powershell
.\qairt-onnx-demo\scripts\start-qairt-openai-server.ps1 `
  -Model .\qairt-onnx-demo\models\your-qnn-model.onnx `
  -Backend htp `
  -Port 4101
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:4101/health
Invoke-RestMethod http://127.0.0.1:4101/v1/models
```

This is not yet a full LLM chat server. It is a thin scaffold for exposing a lower-level ONNX/QNN model endpoint to agent frameworks. A complete LLM route needs a QNN-compatible generative model plus tokenizer/generation code.

## OpenClaw Config

Apply the experimental provider:

```powershell
.\qairt-onnx-demo\scripts\apply-openclaw-config.ps1
```

Then OpenClaw can target:

```text
qairt-onnx/qairt-onnx
```

Again, this provider is only useful after a chat-capable ONNX/QNN model server is running on port `4101`.

## When To Use This Instead Of Foundry

Use Foundry Local when you want the fastest path to a working local LLM demo.

Use QAIRT / ONNX Runtime QNN EP when you want:

- direct control over ONNX Runtime provider options
- direct HTP backend experiments
- custom compiled or quantized ONNX models
- benchmarking outside Foundry
- a lower-level developer story for Qualcomm AI Runtime

## References

- ONNX Runtime QNN Execution Provider: https://onnxruntime.ai/docs/execution-providers/QNN-ExecutionProvider.html
- ONNX Runtime QNN package docs: https://github.com/onnxruntime/onnxruntime-qnn/blob/main/docs/execution_providers/QNN-ExecutionProvider.md
