from dotenv import load_dotenv
from livekit import agents
from livekit.plugins import deepgram, openai, silero
import os

load_dotenv()

async def entrypoint(ctx: agents.JobContext):
    """
    This is the entrypoint for the agent.
    It's called when a new job is created.
    """
    await ctx.connect()
  
    my_azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    my_azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    my_azure_deployment_name = "gpt-4o-mini" 

    session = agents.AgentSession(
        # vad=silero.VAD(), 
        stt=deepgram.STT(
            model="nova-2-general",
        ),
        tts=deepgram.TTS(
            model="aura-asteria-en",
        ),
        llm=openai.LLM.with_azure(
            azure_deployment=my_azure_deployment_name,
            api_key=my_azure_api_key,
            azure_endpoint=my_azure_endpoint,
        )
    )

    await session.start(
        room=ctx.room,
        agent=agents.Agent(instructions="You are a helpful voice AI assistant.")
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
