#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGY_DIR="$HOME/devtools/agylocal"
VENV_DIR="$AGY_DIR/.venv"
GEMINI_MD="$HOME/.gemini/GEMINI.md"

echo "1. Pulling gemma4:26b via Ollama..."
ollama pull gemma4:26b

echo "2. Setting up Python virtual environment at $VENV_DIR..."
mkdir -p "$AGY_DIR"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
"$VENV_DIR/bin/pip" install --upgrade pip google-antigravity

echo "3. Copying workhorse scripts and config to $AGY_DIR..."
cp "$SCRIPT_DIR/workhorse.py" "$AGY_DIR/"
cp "$SCRIPT_DIR/config.json" "$AGY_DIR/"
cp "$SCRIPT_DIR/agy_interactive.py" "$AGY_DIR/"
cp "$SCRIPT_DIR/agy_ollama.py" "$AGY_DIR/"
cp "$SCRIPT_DIR/agy_sample.py" "$AGY_DIR/"
chmod +x "$AGY_DIR/workhorse.py"

echo "4. Ensuring Hybrid Model Architecture rule in $GEMINI_MD..."
mkdir -p "$(dirname "$GEMINI_MD")"
RULE="- Hybrid Model Architecture (Thinking + Local Workhorse): Use Gemini 4 Argon via Gemini AGY (\`~/.gemini/antigravity-cli/settings.json\`) for thinking, planning, architecture, and verification, and ALWAYS delegate workhorse execution tasks to the local \`gemma4:26b\` model via \`$AGY_DIR/.venv/bin/python $AGY_DIR/workhorse.py -w <workspace> \"<task>\"\` configured in \`$AGY_DIR/config.json\`."

if [ -f "$GEMINI_MD" ]; then
    if ! grep -q "Hybrid Model Architecture" "$GEMINI_MD"; then
        printf "\n%s\n" "$RULE" >> "$GEMINI_MD"
    fi
else
    printf "## Gemini Added Memories\n%s\n" "$RULE" > "$GEMINI_MD"
fi

echo "Setup complete! Test with:"
echo "  $VENV_DIR/bin/python $AGY_DIR/workhorse.py -w $(pwd) \"List files in this directory\""
