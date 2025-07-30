import asyncio
import os
from dotenv import load_dotenv
from livekit import agents
from livekit.plugins import deepgram, openai, silero
import os

load_dotenv()

# --- 1. DEFINE YOUR LANGGRAPH AGENT BRAIN (This remains the same) ---

class GraphState(TypedDict):
    messages: list

def create_langgraph_workflow() -> Runnable:
    """Creates a LangGraph workflow for the customer support agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a friendly and helpful customer support agent for a company called 'Gadget World'. Keep your responses concise and to the point. Be polite and professional. Your name is Aura."),
            ("placeholder", "{messages}"),
        ]
    )
    llm = AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    )
    
    chain = prompt | llm | StrOutputParser()

    def agent_node(state: GraphState):
        return {"messages": [chain.invoke(state)]}

    workflow = StateGraph(GraphState)
    workflow.add_node("agent", agent_node)
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)
    return workflow.compile()

# --- 2. DEFINE THE AGENT'S ENTRYPOINT (Final Corrected Version) ---
async def entrypoint(ctx: JobContext):
    """
    This is the entrypoint for the agent. It's called when a new job is created.
    """
    print(f"--- AGENT JOB STARTED FOR ROOM: {ctx.room.name} ---")

    audio_track_ready = asyncio.Event()
    user_audio_track = None

    # This callback now compares track.kind to its integer value (0 for audio)
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        nonlocal user_audio_track
        
        # DEBUG: Let's see what track.kind actually is
        print(f"DEBUG: New track subscribed. Kind: {track.kind}, Type: {type(track.kind)}")

        # SOLUTION: Compare with the integer value 0 for AUDIO. This is the most robust fix.
        if track.kind == 0 and user_audio_track is None:
            print(f"--- SUBSCRIBED TO USER AUDIO TRACK: {participant.identity} ---")
            user_audio_track = track
            audio_track_ready.set()

    # Connect to the room first
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
            api_key=os.environ["DEEPGRAM_API_KEY"],
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
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        worker_type=WorkerType.ROOM  
    )
    cli.run_app(opts)