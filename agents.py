# import asyncio
# import os
# from dotenv import load_dotenv
# from typing import TypedDict

# # Import LiveKit components
# from livekit.agents import JobContext, AgentSession, WorkerOptions, cli, WorkerType
# from livekit.plugins import deepgram, langchain

# # Import LangChain and LangGraph components
# from langchain_openai import AzureChatOpenAI
# from langchain.prompts import ChatPromptTemplate
# from langchain.schema.runnable import Runnable
# from langchain.schema.output_parser import StrOutputParser
# from langgraph.graph import StateGraph, END

# # Load environment variables from .env file
# load_dotenv()

# # --- 1. DEFINE YOUR LANGGRAPH AGENT BRAIN (This remains the same) ---

# class GraphState(TypedDict):
#     messages: list

# def create_langgraph_workflow() -> Runnable:
#     """Creates a LangGraph workflow for the customer support agent."""
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", "You are a friendly and helpful customer support agent for a company called 'Gadget World'. Keep your responses concise and to the point. Be polite and professional. Your name is Aura."),
#             ("placeholder", "{messages}"),
#         ]
#     )
#     llm = AzureChatOpenAI(
#         azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
#     )
    
#     chain = prompt | llm | StrOutputParser()

#     def agent_node(state: GraphState):
#         return {"messages": [chain.invoke(state)]}

#     workflow = StateGraph(GraphState)
#     workflow.add_node("agent", agent_node)
#     workflow.set_entry_point("agent")
#     workflow.add_edge("agent", END)
#     return workflow.compile()

# # (Keep all your other imports and code the same)

# # --- 2. DEFINE THE AGENT'S ENTRYPOINT ---
# async def entrypoint(ctx: JobContext):
#     """
#     This is the entrypoint for the agent. It's called when a new job is created.
#     """
#     print(f"--- AGENT JOB STARTED FOR ROOM: {ctx.room.name} ---")
#     await ctx.connect()
#     print("--- AGENT CONNECTED TO ROOM ---")

#     langgraph_workflow = create_langgraph_workflow()
    
#     session = AgentSession(
#         stt=deepgram.STT(api_key=os.environ["DEEPGRAM_API_KEY"]),
#         llm=langchain.LLMAdapter(graph=langgraph_workflow),
#         tts=deepgram.TTS(
#             api_key=os.environ["DEEPGRAM_API_KEY"],
#             model="aura-asteria-en",
#         ),
#     )

#     # ***** ADD THESE DEBUG LISTENERS *****
#     @session.on("track_subscribed")
#     def on_track_subscribed(track, publication, participant):
#         print(f"Track subscribed: {publication.kind}, participant: {participant.identity}")

#     @session.on("stt_interim_transcript")
#     def on_stt_interim_transcript(transcript: str):
#         print(f"STT Interim: '{transcript}'")

#     @session.on("stt_final_transcript")
#     def on_stt_final_transcript(transcript: str):
#         print(f"STT Final: '{transcript}'")

#     @session.on("llm_response")
#     def on_llm_response(text: str):
#         print(f"LLM Response: '{text}'")
    
#     await session.run(ctx)

# # --- 3. THE NEW MAIN EXECUTION BLOCK (This remains the same) ---
# if __name__ == "__main__":
#     opts = WorkerOptions(
#         entrypoint_fnc=entrypoint,
#         worker_type=WorkerType.ROOM  
#     )
#     cli.run_app(opts)


import asyncio
from dotenv import load_dotenv

# Only import the essentials for this test
from livekit.agents import JobContext, WorkerOptions, cli, WorkerType

# Load environment variables
load_dotenv()

async def entrypoint(ctx: JobContext):
    # If this message prints, the agent was successfully assigned to the room.
    # This is the single most important thing we are testing for.
    print("--- ✅ SUCCESS: AGENT RECEIVED JOB FOR ROOM:", ctx.room.name, "---")
    
    # We'll just wait here for a bit to keep the job alive for testing.
    await asyncio.sleep(60)
    print("--- AGENT JOB FINISHED ---")

if __name__ == "__main__":
    print("--- Starting Minimal Agent Worker ---")

    # Ensure WorkerOptions is configured correctly
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        worker_type=WorkerType.ROOM,
    )

    # Run the agent using the CLI helper
    cli.run_app(opts)