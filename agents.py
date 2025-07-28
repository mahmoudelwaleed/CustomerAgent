import asyncio
import os
from dotenv import load_dotenv

# Import the new recommended components: cli and WorkerOptions
from livekit.agents import JobContext, AgentSession, WorkerOptions, cli ,WorkerType

# Import the LLM adapter and plugins
from livekit.agents import llm as llm_v1 
from livekit.plugins import deepgram

# Import LangChain components
from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import Runnable
from langchain.schema.output_parser import StrOutputParser

# Load environment variables from .env file
load_dotenv()

# --- 1. DEFINE YOUR LANGCHAIN AGENT BRAIN (This remains the same) ---
def create_langchain_runnable() -> Runnable:
    """Creates a basic LangChain runnable for the customer support agent."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a friendly and helpful customer support agent for a company called 'Gadget World'. "
                "Keep your responses concise and to the point. Be polite and professional. "
                "Your name is Aura.",
            ),
            ("human", "{user_input}"),
        ]
    )
    llm = AzureChatOpenAI(
        azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    )
    chain = prompt | llm | StrOutputParser()
    return chain

# --- 2. DEFINE THE AGENT'S ENTRYPOINT (Replaces job_request_cb) ---
async def entrypoint(ctx: JobContext):
    """
    This is the entrypoint for the agent. It's called when a new job is created.
    """
    print(f"Agent received a job for room: {ctx.room.name}")
    
    langchain_runnable = create_langchain_runnable()
    
    # The AgentSession setup is the same as before
    session = AgentSession(
        context=ctx,
        stt=deepgram.STT(api_key=os.environ["DEEPGRAM_API_KEY"]),
        llm=llm_v1.LangchainLLM(chain=langchain_runnable),
        tts=deepgram.TTS(
            api_key=os.environ["DEEPGRAM_API_KEY"],
            model="aura-asteria-en",
        ),
    )
    await session.run()

# --- 3. THE NEW MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # This is the new, recommended way to run the agent
    # It replaces the manual Worker initialization and loop.
    
    # Create WorkerOptions to configure the worker
    opts = WorkerOptions(
        entrypoint_fnc=entrypoint,
        # worker_type=WorkerType.ROOM  
    )

    # Run the agent using the CLI helper
    cli.run_app(opts)