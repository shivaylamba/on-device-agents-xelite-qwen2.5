# NPU Agent Profile - Delegation Guide

## Profile: `npu-agent`

Specialist Hermes profile for using models that run on the Snapdragon X Elite NPU through Foundry Local and an optional LiteLLM proxy.

Default model: `qwen2.5-7b-instruct-qnn-npu:3` (tool calling, 28K context)
Reasoning model: `deepseek-r1-distill-qwen-7b-qnn-npu:2` (reasoning, no tool calling)

## Architecture

```text
Default Hermes / orchestrator profile
  |
  delegate_task(model="npu-agent")  OR  kanban assignee: npu-agent
  |
  v
npu-agent profile
  model.default: foundry-npu
  custom_providers[foundry-npu] -> http://localhost:4001/v1 (LiteLLM)
                                              |
                                    Foundry :5272 -> Qwen2.5-7B NPU
```

## Delegation from the Orchestrator

```python
result = delegate_task(
    model="npu-agent",
    prompt="Your task is: ...",
    toolsets=["file", "terminal"],
)
```

```yaml
assignee: npu-agent
title: "Daily journal entry"
skill: foundry-npu
```

## When to Use It

| Scenario | Use NPU agent? |
|----------|----------------|
| Daily routine tasks such as journals and summaries | YES |
| Local or sensitive data that should not go to the cloud | YES |
| Large context window needed (28K) | YES |
| Tool calling with `required` mode | YES, with Qwen2.5-7B |
| Complex multi-turn reasoning | NO, use the orchestrator or a cloud model |
| Ollama model required | NO, use an Ollama-specific profile |

## Profile Limits

| Limit | Value |
|-------|-------|
| Max output tokens | 4096 |
| Context window | 28672 |
| Tool calling | Reliable in `required` mode |
| Response time | 3-8s |
| Reasoning effort | medium (`config.yaml`) |

## Hermes Commands

```powershell
hermes profile use npu-agent
npu-agent
hermes cron list
hermes cron run npu-daily-journal
hermes cron pause npu-daily-journal
```

## References

- Skill: `C:\Users\<you>\AppData\Local\hermes\skills\foundry-npu\SKILL.md`
- Config: `C:\Users\<you>\AppData\Local\hermes\profiles\npu-agent\config.yaml`
- Foundry app: this repo's `foundry\` folder
- LiteLLM: `C:\AI\apps\litellm-win\`
