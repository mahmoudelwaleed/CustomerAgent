import asyncio
import os
from dotenv import load_dotenv
from typing import TypedDict

# Import LiveKit components
from livekit import rtc
from livekit.agents import JobContext, AgentSession, WorkerOptions, cli, WorkerType
from livekit.plugins import deepgram, langchain

# Import LangChain and LangGraph components
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import Runnable
from langchain.schema.output_parser import StrOutputParser
from langgraph.graph import StateGraph, END

# Load environment variables from .env file
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
    print("--- AGENT CONNECTED TO ROOM, WAITING FOR USER AUDIO ---")

    # Wait until the audio track is ready
    try:
        await asyncio.wait_for(audio_track_ready.wait(), timeout=20.0)
    except asyncio.TimeoutError:
        print("--- NO AUDIO TRACK RECEIVED, TIMING OUT ---")
        return

    # Initialize the agent session
    langgraph_workflow = create_langgraph_workflow()
    
    session = AgentSession(
        stt=deepgram.STT(api_key=os.environ["DEEPGRAM_API_KEY"]),
        llm=langchain.LLMAdapter(graph=langgraph_workflow),
        tts=deepgram.TTS(
            api_key=os.environ["DEEPGRAM_API_KEY"],
            model="aura-asteria-en",
        ),
    )

    # Add debug listeners
    @session.on("stt_final_transcript")
    def on_stt_final_transcript(transcript: str):
        print(f"STT Final: '{transcript}'")

    @session.on("llm_response")
    def on_llm_response(text: str):
        print(f"LLM Response: '{text}'")
    
    # Run the session with the user's audio track
    await session.run(user_input=user_audio_track)

# --- 3. THE MAIN EXECUTION BLOCK (This remains the same) ---
if __name__ == "__main__":
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        worker_type=WorkerType.ROOM  
    )
    cli.run_app(opts)