# Troubleshooting - Hermes Foundry NPU Integration

## Quick Diagnostics

```powershell
# 1. SDK-managed Foundry bridge
cd .\foundry
$env:FOUNDRY_MODEL = 'qwen2.5-0.5b'
.\start-foundry.ps1 --test

# 2. Loaded models from the SDK web service
curl http://localhost:5272/v1/models

# 3. Optional LiteLLM proxy
curl http://localhost:4001/health
# Expected: {"status": "healthy"}

# 4. Python API test
python .\foundry\test_api.py
```

## Errors and Fixes

### "Connection refused: localhost:5272"

The SDK-managed bridge is not running.

```powershell
cd .\foundry
.\start-foundry.ps1
```

### "Connection refused: localhost:4001"

LiteLLM proxy is not running.

```powershell
cd C:\AI\apps\litellm-win
.\start.ps1
```

### `/v1/models` Is Empty After `foundry service start`

You started the standalone CLI service. This repo now uses the SDK-managed web service started by `manager.start_web_service()` after `model.load()`.

```powershell
foundry service stop
cd .\foundry
$env:FOUNDRY_MODEL = 'qwen2.5-0.5b'
.\start-foundry.ps1 --test
```

### "WinError 10054 - remote host forcefully closed"

The model is not loaded, or the service is still warming up immediately after load.

```powershell
foundry model load qwen2.5-7b
Start-Sleep -Seconds 8
python .\foundry\test_api.py
```

### "WinError 10061 - connection refused" after loading

The service is internally restarting after model load. Wait 5-10 seconds.

```powershell
Start-Sleep -Seconds 10
curl http://localhost:5272/v1/models
```

### "Failed to process model #0 on page 1"

This is a Foundry 0.8.119 catalog API bug. Model loading and inference can still work.

### "DSP_INFO UNSUPPORTED_KEY: 49" or "50"

This is a Qualcomm QNN SDK diagnostic message. It can be ignored when inference is working.

### "foundry cache list -> 500 Internal Server Error"

This is a Foundry 0.8.119 bug. Check the model cache on disk instead.

### Foundry Service Crashes During Model Load

Check free memory:

```powershell
Get-CimInstance Win32_OperatingSystem |
  Select-Object @{Name='FreeGB';Expression={[math]::Round($_.FreePhysicalMemory / 1048576, 1)}}
```

If free memory is below 8 GB, close Open WebUI, Bifrost, or other large apps.

### "foundry service set --port" Is Ignored

Some winget builds have service setting issues. Try:

```powershell
foundry service stop
foundry service set --port 5272
foundry service start
foundry service status
```

### Tool Calling Does Not Work in Hermes `npu-agent`

1. If you are using DeepSeek-R1-7B, switch to Qwen2.5-7B:

   ```powershell
   foundry model unload deepseek-r1-7b
   foundry model load qwen2.5-7b
   ```

2. If `tool_choice: auto` skips tools, use required tool mode:

   ```yaml
   agent:
     tool_use_enforcement: required
   ```

3. If you are bypassing LiteLLM, the client may not know the model supports function calling. Use LiteLLM on `:4001` for the `npu-agent` profile.

### Hermes `npu-agent`: "Provider not found: foundry-npu"

LiteLLM is not running or the custom provider config is wrong.

```powershell
cd C:\AI\apps\litellm-win
.\start.ps1
```

Check:

```yaml
custom_providers:
- base_url: http://localhost:4001/v1
model:
  default: foundry-npu
```

### ChromaDB Indexer Timeout

The `run_incremental_index.py` wrapper may time out after 120 seconds.

Run the NPU indexer directly with a smaller batch:

```powershell
$py = 'C:\Users\<you>\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe'
& $py C:\Users\<you>\AppData\Local\hermes\scripts\system_doc_indexer_npu.py --incremental --batch-size 10
```

Or increase the Hermes cron timeout in `jobs.json`.

### `vault_health_check.py` Script Not Found

Check that the cron job points to the actual script path:

```json
"script": "vault_health_check.py --dir C:\\Users\\<you>\\Documents\\gaiagent\\gaiagent"
```

## Full Startup Order

```powershell
# 1. SDK-managed Foundry bridge and model load
cd .\foundry
$env:FOUNDRY_MODEL = 'qwen2.5-0.5b'
.\start-foundry.ps1 --test

# 2. LiteLLM proxy
cd C:\AI\apps\litellm-win
.\start.ps1

# 3. Optional Bifrost
cd C:\AI\apps\bifrost
.\start-bifrost.ps1

# 4. Hermes
hermes

# 5. Verification
python .\foundry\test_api.py
```
