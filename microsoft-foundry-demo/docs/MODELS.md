# NPU Models - Foundry Local

## Current Catalog (2026-05-31)

### Downloaded Models

| Alias | Variant ID | Device | Tool Calling | Size | Status |
|-------|------------|--------|--------------|------|--------|
| `qwen2.5-7b` | `qwen2.5-7b-instruct-qnn-npu:3` | NPU | YES | 6.8 GB | available |
| `deepseek-r1-7b` | `deepseek-r1-distill-qwen-7b-qnn-npu:2` | NPU | NO | 3.7 GB | downloaded |
| `phi-3-mini-4k` | `Phi-3-mini-4k-instruct-generic-cpu:3` | CPU | NO | 2.5 GB | downloaded |

### Available NPU Models in the Foundry Catalog

| Alias | Variant ID | Device | Tool Calling | Size |
|-------|------------|--------|--------------|------|
| `qwen2.5-1.5b` | `qwen2.5-1.5b-instruct-qnn-npu:3` | NPU | YES | ~1 GB |
| `phi-4-mini-reasoning` | `Phi-4-mini-reasoning-qnn-npu` | NPU | NO | 2.78 GB |
| `deepseek-r1-14b` | `deepseek-r1-distill-qwen-14b-qnn-npu` | NPU | NO | 7.12 GB |

## Model Selection Guide

```text
Agent task that needs tool calling?
  YES -> qwen2.5-7b (NPU, reliable with tool_choice=required)
  NO  -> deepseek-r1-7b (NPU, reasoning-oriented)

Need lower memory or faster startup?
  -> qwen2.5-1.5b (NPU, tool calling, ~1 GB)

Need CPU fallback?
  -> phi-3-mini-4k (CPU, 4K context)
```

## Performance Benchmarks (reference machine, measured over Wi-Fi)

| Model | First Response | Tokens/s (estimate) | Context | Mode |
|-------|----------------|---------------------|---------|------|
| Qwen2.5-7B NPU | 3-5s | 15-25 | 28672 | chat |
| DeepSeek-R1-7B NPU | 2-4s | 20-30 | 32768 | reasoning |
| Phi-3-mini-4k CPU | 8-15s | 5-10 | 4096 | chat |

Exact tokens/s cannot be measured on Foundry 0.8.119 because of the `usage.completion_tokens=0` bug.

## Model Lifecycle Commands

```powershell
foundry model list
foundry model download qwen2.5-7b
foundry model download deepseek-r1-7b
foundry model load qwen2.5-7b
foundry model unload deepseek-r1-7b
foundry model load qwen2.5-7b
foundry cache remove phi-3-mini-4k
foundry cache cd E:\models\foundry
```

## Model File Structure Example (DeepSeek-R1-7B)

```text
E:\models\foundry\
  deepseek-r1-distill-qwen-7b-qnn-npu-2\v2\
    deepseek_r1_7b_cb_1.bin   0.825 GB
    deepseek_r1_7b_cb_2.bin   0.825 GB
    deepseek_r1_7b_cb_3.bin   0.825 GB
    deepseek_r1_7b_cb_4.bin   0.825 GB
    deepseek_r1_7b_ctx_v1.0.onnx_ctx.onnx
    deepseek_r1_7b_iter_v1.0.onnx_ctx.onnx
    deepseek_r1_7b_embeddings_quant_v1.0.onnx  0.341 GB
    deepseek_r1_7b_head_quant_v1.0.onnx        0.341 GB
```

## LiteLLM Model Mapping

```yaml
foundry-npu: openai/qwen2.5-7b-instruct-qnn-npu:3
foundry-npu-deepseek: openai/deepseek-r1-distill-qwen-7b-qnn-npu:2
```

## Hermes Model References

```text
/model custom:foundry-npu          # through LiteLLM proxy to Qwen2.5-7B
/model custom:foundry-npu (direct) # direct :5272 access

model="openai/qwen2.5-7b-instruct-qnn-npu:3"
api_base="http://localhost:4001/v1"
```
