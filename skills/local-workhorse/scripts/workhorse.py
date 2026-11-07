#!/usr/bin/env python3
"""Local Workhorse Agent runner powered by Antigravity SDK + Ollama (gemma4:26b)."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

from google.antigravity import Agent, CapabilitiesConfig, LocalOpenAIAgentConfig
from google.antigravity.hooks import policy

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config(config_path: Path = CONFIG_PATH) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_workhorse(prompt: str, workspace: str | None = None, config_path: Path = CONFIG_PATH) -> None:
    cfg = load_config(config_path)
    wh = cfg["workhorse"]

    caps_cfg = wh.get("capabilities", {})
    capabilities = CapabilitiesConfig(
        file_reads=caps_cfg.get("file_reads", True),
        file_writes=caps_cfg.get("file_writes", True),
        command_execution=caps_cfg.get("command_execution", True),
        subagents=caps_cfg.get("subagents", False),
        mcp=caps_cfg.get("mcp", False),
    )

    target_workspace = os.path.abspath(workspace or os.getcwd())
    os.chdir(target_workspace)

    agent_config = LocalOpenAIAgentConfig(
        model=wh["model"],
        base_url=wh["base_url"],
        system_instructions=wh.get("system_instructions"),
        capabilities=capabilities,
        policies=[policy.allow_all()] if wh.get("allow_all_policies", True) else None,
        workspaces=[target_workspace],
    )
    if wh.get("lightweight", True):
        agent_config = agent_config.lightweight()

    print(
        f"[Workhorse: {wh['model']} @ {wh['base_url']} | Workspace: {target_workspace}]",
        file=sys.stderr,
        flush=True,
    )

    async with Agent(agent_config) as agent:
        response = await agent.chat(prompt)

        async def _log_tools():
            async for call in response.tool_calls:
                print(f"\n[Tool] {call.name}({call.args})", file=sys.stderr, flush=True)

        tool_task = asyncio.create_task(_log_tools())
        async for token in response:
            sys.stdout.write(token)
            sys.stdout.flush()
        print()
        await tool_task


def main() -> None:
    parser = argparse.ArgumentParser(description="Run local gemma4:26b workhorse task.")
    parser.add_argument("prompt", nargs="+", help="Task prompt for the workhorse model")
    parser.add_argument(
        "-w",
        "--workspace",
        default=os.getcwd(),
        help="Target workspace directory (default: current directory)",
    )
    parser.add_argument(
        "-c",
        "--config",
        default=str(CONFIG_PATH),
        help="Path to config.json",
    )
    args = parser.parse_args()
    task_prompt = " ".join(args.prompt)
    asyncio.run(run_workhorse(task_prompt, workspace=args.workspace, config_path=Path(args.config)))


if __name__ == "__main__":
    main()
