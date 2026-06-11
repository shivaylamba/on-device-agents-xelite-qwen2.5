# QAIRT Genie Qwen3-4B Demo

This folder runs a local Qualcomm QAIRT Genie LLM bundle directly on Snapdragon X Elite HTP/NPU, without Microsoft Foundry Local.

The local model used during testing was:

```text
C:\Users\Admin\Documents\executorch-voice-agent\models\qwen3_4b\genie_bundle\qwen3_4b-genie-w4a16-qualcomm_snapdragon_x_elite
```

That folder is not an ONNX model package. It is a QAIRT Genie bundle with compiled QNN context binaries:

```text
qwen3_4b_w4a16_part_1_of_4.bin
qwen3_4b_w4a16_part_2_of_4.bin
qwen3_4b_w4a16_part_3_of_4.bin
qwen3_4b_w4a16_part_4_of_4.bin
genie_config.json
tokenizer.json
```

## Architecture

```text
OpenClaw or local app
  |
  v
OpenAI-compatible Genie shim
  |
  v
QAIRT genie-t2t-run.exe
  |
  v
Genie config + Qwen3 compiled context binaries
  |
  v
QNN HTP backend + Hexagon v73 Skel library
  |
  v
Snapdragon X Elite HTP/NPU
```

The important runtime detail is `ADSP_LIBRARY_PATH`. The CPU-side QNN HTP stub needs this path to find the Hexagon-side Skel library:

```text
C:\Qualcomm\AIStack\QAIRT\2.45.0.260326\lib\hexagon-v73\unsigned
```

Without that variable, Genie may load but fail at backend initialization with errors like `Unable to load backend`, `Failed to allocate memory for IO tensors`, or a native crash while creating the text generator node.

## Direct Genie Test

Run a one-shot Qwen3 prompt:

```powershell
cd "C:\Users\Admin\Documents\microsoft foundary\on-device-agents-xelite-qwen2.5"

.\qairt-genie-demo\scripts\test-qwen3-genie.ps1 `
  -Prompt "What is 2+2? Reply with the number only."
```

Expected behavior:

```text
Using libGenie.so version 1.17.0
[PROMPT]: ...
[BEGIN]: ...
[END]
```

The known-good local setup used:

- QAIRT: `C:\Qualcomm\AIStack\QAIRT\2.45.0.260326`
- ABI: `aarch64-windows-msvc`
- HTP Skel path: `C:\Qualcomm\AIStack\QAIRT\2.45.0.260326\lib\hexagon-v73\unsigned`

## Start the OpenAI-Compatible Shim

```powershell
.\qairt-genie-demo\scripts\start-qwen3-genie-server.ps1 -Port 4102
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:4102/health
Invoke-RestMethod http://127.0.0.1:4102/v1/models
```

Test chat completions:

```powershell
.\qairt-genie-demo\scripts\test-qwen3-genie-server.ps1
```

The server serializes generation requests with a process lock. That is intentional: local HTP/NPU LLM sessions are easier to keep stable when requests are not run concurrently.

The shim also injects a small runtime context so the model can accurately answer demo questions about what is serving it. Qwen3 can emit `<think>` blocks; the HTTP shim strips that reasoning text from the returned chat message and keeps a raw output preview in the `qairt_genie` debug field.

## OpenClaw Provider

Apply the provider config:

```powershell
.\qairt-genie-demo\scripts\apply-openclaw-config.ps1
```

Then use this OpenClaw model id:

```text
qwen3-genie/qwen3-4b-genie
```

Example:

```powershell
openclaw infer model run qwen3-genie/qwen3-4b-genie `
  --prompt "In one sentence, what runtime is serving this model?"
```

Keep OpenClaw prompts short at first. This path launches the Genie runner for each request, so it is useful for demo validation and provider testing, not yet optimized for low-latency chat.

## How This Differs From ONNX Runtime QNN EP

`qairt-onnx-demo` is for ONNX models and ONNX Runtime's `QNNExecutionProvider`.

This folder is for Genie LLM bundles. Genie handles the tokenizer and text generation loop and loads compiled QNN context binaries directly. For the local Qwen3-4B bundle, this is the correct path.
