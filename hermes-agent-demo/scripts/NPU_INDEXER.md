# NPU Indexer Documentation

Source in the original setup: `C:\Users\<you>\AppData\Local\hermes\scripts\NPU_INDEXER_README.md`

## `system_doc_indexer_npu.py` - NPU-Optimized ChromaDB Indexer

Script path: `C:\Users\<you>\AppData\Local\hermes\scripts\system_doc_indexer_npu.py`
Python: `C:\Users\<you>\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe`

### Performance

| Metric | CPU Version | NPU Batch Version |
|--------|-------------|-------------------|
| Embedding calls | 28,780 calls (1/chunk) | ~68 calls (25/chunks) |
| Duration | ~12 hours | ~5-8 minutes |
| CPU temperature | 90 C | 60-70 C |

Reason for speedup: Ollama `/api/embed` batch endpoint with 25 chunks per request.

### Indexed Scope (default vault-only)

| Label | Folder | Files |
|-------|--------|-------|
| VAULT | `C:\Users\<you>\Documents\gaiagent\gaiagent` | 293 |
| HERMES-skills | `C:\Users\<you>\AppData\Local\hermes\skills` | 506 |
| HERMES-config | `C:\Users\<you>\AppData\Local\hermes` | 33 |
| Total | | 832 |

### Output

ChromaDB: `C:\Users\<you>\Documents\gaiagent\chromadb_data\`
Collection: `gaiagent_system_docs` (`bge-m3`, 1024 dimensions)

### Usage

```powershell
$py = 'C:\Users\<you>\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe'

# First index
& $py C:\Users\<you>\AppData\Local\hermes\scripts\system_doc_indexer_npu.py

# Daily incremental maintenance
& $py C:\Users\<you>\AppData\Local\hermes\scripts\system_doc_indexer_npu.py --incremental

# Full rebuild
& $py C:\Users\<you>\AppData\Local\hermes\scripts\system_doc_indexer_npu.py --force

# Dry run
& $py C:\Users\<you>\AppData\Local\hermes\scripts\system_doc_indexer_npu.py --dry-run
```

### Cron Integration Issues (2026-05-31)

- `daily-system-reindex` timed out after 120 seconds because the `run_incremental_index.py` wrapper was slow.
- Fix by pointing the cron `script` field directly to `system_doc_indexer_npu.py --incremental`, or increase the Hermes cron timeout.

### Requirement

Ollama service must be running and the `bge-m3` model must be available:

```powershell
ollama serve
ollama pull bge-m3
```
