import asyncio
from google.antigravity import Agent, LocalOpenAIAgentConfig
from google.antigravity.hooks import policy

MODEL_NAME = "gemma4:26b"

async def main():
    print(f"Using local Ollama model: {MODEL_NAME}. Please wait for local inference to complete...")

    config = LocalOpenAIAgentConfig(
        model=MODEL_NAME,
        base_url="http://localhost:11434/v1",
        policies=[policy.allow_all()],
    ).lightweight()

    async with Agent(config) as agent:
        response = await agent.chat("What files are in the current directory?")
        async for token in response:
            print(token, end="", flush=True)
        print()

if __name__ == "__main__":
    asyncio.run(main())
