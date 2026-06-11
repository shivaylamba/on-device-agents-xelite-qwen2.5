# Integration Examples - Hermes + Foundry NPU

## 1. Hermes `npu-agent` Profile (recommended)

Use this for daily routine tasks, local or sensitive data, Obsidian journal workflows, and tool calling.

```yaml
model:
  provider: custom
  default: foundry-npu

custom_providers:
- api_key: sk-win-vivo2
  api_mode: chat_completions
  base_url: http://localhost:4001/v1
  model: foundry-npu
  name: foundry-npu

providers:
  foundry-npu:
    request_timeout_seconds: 180
```

Start it:

```powershell
hermes profile use npu-agent
npu-agent
```

## 2. Default Hermes Profile with Direct Foundry Access

Use this for occasional NPU calls from the main profile without LiteLLM.

```yaml
custom_providers:
- api_key: foundry-local
  api_mode: chat_completions
  base_url: http://localhost:5272/v1
  model: deepseek-r1-distill-qwen-7b-qnn-npu:2
  name: foundry-npu
```

```text
/model custom:foundry-npu
```

## 3. Orchestrator Delegation to the NPU Agent

```python
result = delegate_task(
    model="npu-agent",
    prompt="Write the daily summary and save it to the Obsidian vault.",
    toolsets=["file", "terminal"],
    timeout=300,
)
```

```yaml
assignee: npu-agent
title: "Generate weekly report"
skill: foundry-npu
prompt: |
  Generate a weekly report from the logs/ folder.
```

## 4. LiteLLM Proxy Model Routing

Use LiteLLM when multiple clients need NPU access, such as Hermes, free-claude-code, or OpenWebUI.

```yaml
- model_name: foundry-npu
  litellm_params:
    model: openai/qwen2.5-7b-instruct-qnn-npu:3
    api_base: http://localhost:5272/v1
    api_key: foundry-local
    timeout: 180
  model_info:
    mode: chat
    supports_function_calling: true
```

```text
Hermes npu-agent -> :4001 -> :5272 (foundry-npu)
free-claude-code -> :4001 -> :5272 (llamacpp provider)
OpenWebUI        -> :4001 -> :5272 (OpenAI endpoint)
```

## 5. free-claude-code Integration

Use this when a coding agent should run against the NPU for simpler tasks.

```env
LLAMACPP_BASE_URL="http://localhost:5272/v1"
MODEL_HAIKU=llamacpp/deepseek-r1-distill-qwen-7b-qnn-npu:2
```

## 6. Bifrost Gateway Integration

Use this when Bifrost should route requests to the local NPU.

```json
"foundry-local": {
  "keys": [{
    "name": "foundry-npu",
    "value": "foundry-key",
    "weight": 1,
    "models": [
      "deepseek-r1-7b",
      "deepseek-r1-distill-qwen-7b-qnn-npu:2",
      "qwen2.5-7b",
      "qwen2.5-7b-instruct-qnn-npu:3"
    ]
  }],
  "network_config": {
    "base_url": "http://localhost:5272",
    "default_request_timeout_in_seconds": 300
  },
  "custom_provider_config": {
    "base_provider_type": "openai",
    "is_key_less": true
  }
}
```

## 7. Python SDK Direct Call

Use this when you need SDK-level model lifecycle control.

```python
from foundry_local_sdk import Configuration, FoundryLocalManager
import openai

config = Configuration(app_name="snapdragon_agent")
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance
manager.download_and_register_eps()

model = manager.catalog.get_model("qwen2.5-7b")
model.download()
model.load()

client = openai.OpenAI(
    base_url="http://127.0.0.1:5272/v1",
    api_key="foundry-local",
)
resp = client.chat.completions.create(
    model=model.id,
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100,
)
print(resp.choices[0].message.content)
```

## 8. Cron Job on NPU

Use this when a scheduled task should run on the local NPU.

```json
{
  "name": "npu-daily-journal",
  "prompt": "...",
  "skills": ["foundry-npu"],
  "model": null,
  "profile": "npu-agent",
  "schedule": {"kind": "cron", "expr": "0 8 * * *"},
  "deliver": "local",
  "enabled_toolsets": ["file", "terminal"]
}
```

Requirement: the SDK-managed Foundry bridge and LiteLLM proxy must be running at the scheduled time.

## 9. Windows Task Scheduler Startup

Use this when Foundry and LiteLLM should start automatically after login.

```powershell
$foundryAction = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument '-WindowStyle Hidden -File "<repo>\foundry\start-foundry.ps1"'
$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
    -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask `
    -TaskName 'FoundryNPUStartup' `
    -Action $foundryAction -Trigger $trigger `
    -Settings $settings -RunLevel Highest -Force
```

```powershell
$litellmAction = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument '-WindowStyle Hidden -File "C:\AI\apps\litellm-win\start.ps1"'
$trigger2 = New-ScheduledTaskTrigger -AtLogOn
$trigger2.Delay = 'PT60S'
Register-ScheduledTask `
    -TaskName 'LiteLLMProxyStartup' `
    -Action $litellmAction -Trigger $trigger2 `
    -Settings $settings -RunLevel Highest -Force
```

Management commands:

```powershell
Get-ScheduledTask | Where-Object TaskName -match 'Foundry|LiteLLM' | Select TaskName, State
Start-ScheduledTask -TaskName 'FoundryNPUStartup'
Start-ScheduledTask -TaskName 'LiteLLMProxyStartup'
Disable-ScheduledTask -TaskName 'FoundryNPUStartup'
Unregister-ScheduledTask -TaskName 'FoundryNPUStartup' -Confirm:$false
```

Notes:

- `PT60S` delay gives Foundry time to load the model before LiteLLM starts.
- `-WindowStyle Hidden` keeps startup tasks in the background.
- `-RunLevel Highest` may be needed for service and networking commands.
- To set a model in the scheduled task, add `$env:FOUNDRY_MODEL='qwen2.5-7b';` to the argument.
