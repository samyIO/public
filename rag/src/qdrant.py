import streamlit as st
from qdrant.db_manager import VectorDbManager
from qdrant.llm_manager import LlmManager


def main():
    st.set_page_config(
        page_title="Project Information Retriever", page_icon="🔍", layout="wide"
    )

    st.title("Project Information Guide")
    st.write(
        "Ask questions about a portfolio project and get answers based on retrieved information."
    )

    # Initialize the database manager
    db_manager = VectorDbManager()
    db_manager.init_qdrant("projects")

    # Initialize the LLM manager
    llm_manager = LlmManager()

    # Create input field for user questions
    user_input = st.text_input("Enter your question:")

    # Add a button to trigger the search
    if st.button("Get Answer") or user_input:
        with st.spinner("Retrieving information..."):
            # Retrieve information from the vector database
            raw_retrieval = db_manager.retrieve_information(user_input)
            voted_retrieval = db_manager.majority_vote(raw_retrieval)

            # Display retrieved documents (expandable)
            with st.expander("View retrieved documents"):
                for i, result in enumerate(raw_retrieval):
                    st.markdown(f"### Document {i+1}")
                    st.write(f"### Source: \n {result.metadata["source"]}")
                    st.write(f"### Content: \n {result.metadata["document"]}")
                    st.divider()

            # Display majority voted documents
            with st.expander("View majority voted documents"):
                i = 0
                for result in voted_retrieval:
                    st.markdown(f"### Document {i+1}")
                    st.write(f"### Source: \n {result.metadata["source"]}")
                    st.write(f"### Content: \n {result.metadata["document"]}")
                    st.divider()
                    i += 1

            # Generate response using LLM
            with st.spinner("Generating response..."):
                response = llm_manager.generate_response(
                    user_input=user_input, retrieval=voted_retrieval
                )

            # Display the response
            st.subheader("Answer:")
            st.write(response)

    # Add some information about how it works
    with st.sidebar:
        st.header("How it works")
        st.write(
            """
        1. Your question is used to search the vector database.
        2. Relevant documents are retrieved.
        3. A majority voting system selects the most relevant documents.
        4. An LLM generates a comprehensive answer based on the retrieved information.
        """
        )

        st.header("About")
        st.write(
            """
        This app uses:
        - Qdrant for vector similarity search
        - A custom LLM manager for response generation
        - Streamlit for the user interface
        """
        )


if __name__ == "__main__":
    main()
