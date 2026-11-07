---
name: local-workhorse
description: Configures and operates the Hybrid Model Architecture combining a frontier thinking model in Antigravity CLI with a local Ollama gemma4:26b workhorse agent via the Antigravity Python SDK.
---

# Local Workhorse (`gemma4:26b` + Antigravity SDK)

This skill packages and operates the **Hybrid Model Architecture**:
- **Thinking Model (`Gemini 4 Argon (Medium)` via Antigravity CLI)**: Handles thinking, planning, architecture, task decomposition, and verification (`~/.gemini/antigravity-cli/settings.json`).
- **Workhorse Model (`gemma4:26b` via local Ollama + Antigravity Python SDK)**: Executes file creation, code edits, and command tasks locally (`~/devtools/agylocal/workhorse.py`).

## Files in `scripts/`

- `workhorse.py`: CLI runner using `google.antigravity.LocalOpenAIAgentConfig` against `http://localhost:11434/v1` (`gemma4:26b`).
- `config.json`: Defines the `thinking` and `workhorse` model roles, endpoint, and capabilities (`file_reads`, `file_writes`, `command_execution`).
- `setup.sh`: One-step bootstrap script for any new machine (pulls `gemma4:26b`, creates `~/devtools/agylocal/.venv`, installs `google-antigravity`, copies scripts, and registers the global rule in `~/.gemini/GEMINI.md`).
- `agy_interactive.py`: Interactive TUI loop backed by local `gemma4:26b`.
- `agy_ollama.py`: Minimal one-shot Ollama + Antigravity SDK example.
- `agy_sample.py`: Minimal LiteRT-LM (`~/.litert-lm/models/gemma4-26b/model.litertlm`) example.

## One-Step Setup (New Machine)

```bash
./skills/local-workhorse/scripts/setup.sh
```

## Delegation Command

Always delegate workhorse execution tasks from the thinking model to the local `gemma4:26b` workhorse:

```bash
~/devtools/agylocal/.venv/bin/python ~/devtools/agylocal/workhorse.py -w <workspace> "<task>"
```

## Global Rule (`~/.gemini/GEMINI.md`)

```markdown
- Hybrid Model Architecture (Thinking + Local Workhorse): Use Gemini 4 Argon via Gemini AGY (`~/.gemini/antigravity-cli/settings.json`) for thinking, planning, architecture, and verification, and ALWAYS delegate workhorse execution tasks to the local `gemma4:26b` model via `/Users/neilghosh/devtools/agylocal/.venv/bin/python /Users/neilghosh/devtools/agylocal/workhorse.py -w <workspace> "<task>"` configured in `/Users/neilghosh/devtools/agylocal/config.json`.
```
