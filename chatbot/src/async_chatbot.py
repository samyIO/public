import asyncio
import argparse
import os
import nest_asyncio
import streamlit as st
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

# Parse command line arguments
parser = argparse.ArgumentParser(description="Chat AI with configurable model settings")
parser.add_argument(
    "--model", type=str, help="Model name to use (default: llama3.1:8b)"
)
parser.add_argument(
    "--model_provider", type=str, help="Model provider to use (default: ollama)"
)
args = parser.parse_args()

# required to run nested async event loops
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Get model settings with priority: command line args > env vars > defaults
MODEL = args.model or os.getenv("CHAT_MODEL", "llama3.1:8b")
MODEL_PROVIDER = args.model_provider or os.getenv("MODEL_PROVIDER", "ollama")

# Configure the UI
st.set_page_config(page_title="Chat AI", page_icon="🤖", layout="wide")

# Initialize model parameters only once
MODEL_PARAMS = {"model": MODEL, "model_provider": MODEL_PROVIDER}


def initialize_model():
    """Initialize the model once and store it in session state"""
    try:
        return init_chat_model(**MODEL_PARAMS)
    except Exception as e:
        st.error(f"Failed to initialize model: {e}")
        return None


async def generate_streaming_response() -> str:
    """Generate streaming response from RAG system"""
    try:
        messages = st.session_state.messages
        # Initialize the model within the same async context where it's used
        model = st.session_state.model
        response_generator = model.astream(messages)
        full_response = ""
        message_placeholder = st.empty()

        # coroutine handling requires async consumption
        # because the default callback manager functions
        # need to be awaited
        async for chunk in response_generator:
            if chunk:
                full_response += chunk.content
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        return full_response
    except Exception as e:
        print(f"Error: {e}")
        return f"An error occurred: {e}"


async def main():
    st.title("Chat AI")

    # Display model information
    st.sidebar.markdown(f"**Using model:** {MODEL_PARAMS['model']}")
    st.sidebar.markdown(f"**Provider:** {MODEL_PARAMS['model_provider']}")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Initialize model only once per session
    if "model" not in st.session_state:
        with st.spinner("Initializing model..."):
            st.session_state.model = initialize_model()

    # Display chat history
    for msg in st.session_state.messages:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])

    # Get user input
    user_input = st.chat_input("Enter a message...")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate and display streaming response
        with st.chat_message("assistant"):
            response = await generate_streaming_response()

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Force a rerun to update the UI with the new messages
        st.rerun()


if __name__ == "__main__":
    asyncio.run(main())
