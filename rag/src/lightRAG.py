import asyncio
import inspect
import nest_asyncio

nest_asyncio.apply()
import os
import logging
import streamlit as st
from dotenv import load_dotenv

from lightrag import LightRAG, QueryParam
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.utils import EmbeddingFunc
from lightrag.kg.shared_storage import initialize_pipeline_status

from pydantic_ai.messages import ModelRequest, ModelResponse

load_dotenv()

WORKING_DIR = "resources/data"
DOCUMENT_DIR = "resources/documents"

logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.INFO)

if not os.path.exists(WORKING_DIR):
    os.mkdir(WORKING_DIR)


async def initialize_rag():
    rag = LightRAG(
        working_dir=WORKING_DIR,
        llm_model_func=ollama_model_complete,
        llm_model_name=str(os.environ.get("RAG_MODEL")),
        llm_model_max_async=4,
        llm_model_max_token_size=int(os.environ.get("RAG_MODEL_MAX_TOKENS")),
        llm_model_kwargs={
            "host": str(os.environ.get("OLLAMA_URL")),
            "options": {"num_ctx": int(os.environ.get("NUM_CTX"))},
        },
        embedding_func=EmbeddingFunc(
            embedding_dim=int(os.environ.get("EMBEDDING_DIM")),
            max_token_size=int(os.environ.get("EMBEDDING_MODEL_MAX_TOKENS")),
            func=lambda texts: ollama_embed(
                texts,
                embed_model=str(os.environ.get("EMBEDDING_MODEL")),
                host=str(os.environ.get("OLLAMA_URL")),
            ),
        ),
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag


async def print_stream(stream):
    async for chunk in stream:
        print(chunk, end="", flush=True)


def display_message_part(part):
    # user-prompt
    if part.part_kind == "user-prompt":
        with st.chat_message("user"):
            st.markdown(part.content)
    # assistant response
    else:
        with st.chat_message("assistant"):
            st.markdown(part.content)


def load_data(rag):
    for file_name in os.listdir(DOCUMENT_DIR):
        file_path = os.path.join(DOCUMENT_DIR, file_name)
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                rag.insert(f.read())
            print(f"Inserted document {file_name}")


async def generate_streaming_response(user_input):
    """Generate streaming response from RAG system"""
    # Request streaming response by setting stream=True
    response_generator = st.session_state.rag.query(
        user_input,
        param=QueryParam(mode=str(os.environ.get("MODE")), stream=True),
    )

    # Check if response is an async generator as expected
    if not inspect.isasyncgen(response_generator):
        # If not streaming, just return the response directly
        return response_generator

    full_response = ""
    message_placeholder = st.empty()

    # Stream the response chunks
    async for chunk in response_generator:
        if chunk:
            full_response += chunk
            # Display with a blinking cursor to indicate ongoing generation
            message_placeholder.markdown(full_response + "▌")

    # Final response without the cursor
    message_placeholder.markdown(full_response)
    return full_response


async def main():
    st.title("LightRAG System")

    if "rag" not in st.session_state:
        with st.spinner("Initializing RAG system..."):
            try:
                rag = await initialize_rag()
                st.session_state.rag = rag
                load_data(rag)
                st.success("RAG system initialized successfully!")
            except Exception as e:
                st.error(f"Failed to initialize RAG system: {str(e)}")
                return
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat history
    for msg in st.session_state.messages:
        if isinstance(msg, dict):
            if msg["role"] == "user":
                with st.chat_message("user"):
                    st.markdown(msg["content"])
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
        elif isinstance(msg, ModelRequest) or isinstance(msg, ModelResponse):
            for part in msg.parts:
                display_message_part(part)

    # Get user input
    user_input = st.chat_input("Which project would you like to explore?")

    if user_input:
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Generate and display streaming response
        with st.chat_message("assistant"):
            response = await generate_streaming_response(user_input)

        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        # Force a rerun to update the UI with the new messages
        st.rerun()


if __name__ == "__main__":
    asyncio.run(main())
