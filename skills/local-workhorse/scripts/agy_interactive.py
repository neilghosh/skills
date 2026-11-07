import asyncio
from google.antigravity import CapabilitiesConfig, LocalOpenAIAgentConfig
from google.antigravity.hooks import policy
from google.antigravity.utils.interactive import run_interactive_loop

MODEL_NAME = "gemma4:26b"

async def main():
    config = LocalOpenAIAgentConfig(
        model=MODEL_NAME,
        base_url="http://localhost:11434/v1",
        capabilities=CapabilitiesConfig(),
        policies=[policy.allow_all()],
    ).lightweight()

    await run_interactive_loop(config)

if __name__ == "__main__":
    asyncio.run(main())
