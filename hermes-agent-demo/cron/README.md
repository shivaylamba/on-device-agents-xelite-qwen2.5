# Hermes Cron Jobs - Foundry NPU Jobs

## npu-daily-journal

| Field | Value |
|-------|-------|
| ID | `de72595f8c54` |
| Schedule | `0 8 * * *` (daily at 08:00) |
| Profile | `npu-agent` |
| Skill | `foundry-npu` |
| Deliver | `local` |
| Status | enabled |

Purpose: run Qwen2.5-7B on the NPU and write a daily journal entry into an Obsidian vault.

Requirement: the SDK-managed Foundry bridge (`:5272`) and LiteLLM proxy (`:4001`) must be running at 08:00.

### Manual Run

```powershell
hermes cron run npu-daily-journal
```

### Management

```powershell
hermes cron list
hermes cron pause npu-daily-journal
hermes cron resume npu-daily-journal
```

## Related Cron Jobs That Touch NPU Workflows

### daily-system-reindex

- Schedule: `0 3 * * *`
- Script: `run_incremental_index.py` (ChromaDB NPU indexer)
- Status: error after 120-second timeout in the original setup
- Fix: increase timeout or pass `--incremental --batch-size 10`

### daily-vault-health

- Schedule: `0 6 * * *`
- Script: `vault_health_check.py`
- Status: error in the original setup because of a script path mismatch
- Fix: verify the script path

### hermes-best-practices-sync

- Schedule: `0 6 * * 1` (weekly on Monday)
- Model: `google/gemini-2.5-flash` through OpenRouter
- Does not use the NPU, but audits Foundry config

## Startup Order

```powershell
# 1. SDK-managed Foundry bridge and model load
cd .\foundry
$env:FOUNDRY_MODEL = 'qwen2.5-7b'
.\start-foundry.ps1

# 2. LiteLLM proxy
cd C:\AI\apps\litellm-win
.\start.ps1

# 3. Hermes runs the cron jobs
hermes
```
