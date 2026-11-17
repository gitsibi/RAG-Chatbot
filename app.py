
import os
import streamlit as st

from dotenv import load_dotenv
from rag_backend import RAGChatbot


# =========================================
# PART 1: PAGE CONFIGURATION
# =========================================

st.set_page_config(
    page_title="PDF RAG Assistant",
    page_icon="📚",
    layout="wide"
)

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")


# =========================================
# PART 2: CUSTOM CSS
# =========================================

st.markdown("""
<style>

.stApp {
    background-color: #0e1117;
    color: white;
}

.block-container {
    padding-top: 2rem;
    max-width: 1100px;
}

[data-testid="stSidebar"] {
    background-color: #171c28;
}

.main-title {
    font-size: 34px;
    font-weight: 700;
    color: #ffffff;
}

.subtitle {
    color: #a7b0c0;
    font-size: 15px;
    margin-bottom: 25px;
}

.answer-box {
    background-color: #1b2433;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #303b50;
    margin-top: 10px;
}

.source-box {
    background-color: #202a3b;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 8px;
    color: #dce5f5;
}

</style>
""", unsafe_allow_html=True)


# =========================================
# PART 3: SESSION STATE
# =========================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chatbot" not in st.session_state:
    st.session_state.chatbot = None

if "uploaded_name" not in st.session_state:
    st.session_state.uploaded_name = None


# =========================================
# PART 4: INITIALIZE BACKEND
# =========================================

if not api_key:

    st.error(
        "Gemini API key not found. "
        "Please configure your .env file."
    )

    st.stop()


@st.cache_resource
def load_chatbot(key):

    return RAGChatbot(key)


try:

    if st.session_state.chatbot is None:
        st.session_state.chatbot = load_chatbot(api_key)

except Exception as e:

    st.error(f"Backend initialization failed: {e}")
    st.stop()


chatbot = st.session_state.chatbot


# =========================================
# PART 5: SIDEBAR
# =========================================

with st.sidebar:

    st.title("📚 PDF RAG Assistant")

    st.caption("Your intelligent document assistant")

    st.divider()

    st.subheader("Upload Document")

    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type=["pdf"]
    )

    if st.button(
        "Process PDF",
        use_container_width=True
    ):

        if uploaded_file is None:

            st.warning("Please upload a PDF first.")

        else:

            try:

                with st.spinner(
                    "Reading PDF and creating embeddings..."
                ):

                    total_chunks = chatbot.process_pdf(
                        uploaded_file.getvalue(),
                        uploaded_file.name
                    )

                    st.session_state.uploaded_name = (
                        uploaded_file.name
                    )

                    st.session_state.messages = []

                st.success("PDF processed successfully!")

                st.info(
                    f"Created {total_chunks} text chunks."
                )

            except Exception as e:

                st.error(f"PDF processing failed: {e}")

    st.divider()

    st.subheader("Document Status")

    if st.session_state.uploaded_name:

        st.success("Document ready")

        st.write(
            f"📄 {st.session_state.uploaded_name}"
        )

    else:

        st.warning("No document processed yet.")

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []
        st.rerun()


# =========================================
# PART 6: MAIN HEADER
# =========================================

st.markdown(
    '<div class="main-title">🤖 Ask Your PDF</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Upload a document and get intelligent answers '
    'based on its content.'
    '</div>',
    unsafe_allow_html=True
)


# =========================================
# PART 7: DISPLAY CHAT HISTORY
# =========================================

if not st.session_state.messages:

    st.info(
        "👋 Welcome! Upload a PDF from the sidebar "
        "and start asking questions."
    )

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        if message["role"] == "assistant":

            sources = message.get("sources", [])

            if sources:

                with st.expander(
                    f"📖 Retrieved Evidence ({len(sources)} chunks)"
                ):

                    for i, source in enumerate(
                        sources,
                        start=1
                    ):

                        st.markdown(
                            f"**Source {i} — "
                            f"Page {source['page']}**"
                        )

                        st.write(source["content"])

                        st.divider()


# =========================================
# PART 8: USER QUESTION
# =========================================

question = st.chat_input(
    "Ask something about your PDF..."
)

if question:

    if not st.session_state.uploaded_name:

        st.warning(
            "Please upload and process a PDF first."
        )

    else:

        # Store user message
        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        # Generate AI response
        with st.chat_message("assistant"):

            with st.spinner("Searching document..."):

                try:

                    answer, evidence = (
                        chatbot.answer_question(question)
                    )

                    st.markdown(answer)

                    if evidence:

                        with st.expander(
                            "📖 View Retrieved Evidence"
                        ):

                            for i, source in enumerate(
                                evidence,
                                start=1
                            ):

                                st.markdown(
                                    f"**Source {i} — "
                                    f"Page {source['page']}**"
                                )

                                st.write(source["content"])

                                st.divider()

                    # Save answer and evidence
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": evidence
                    })

                except Exception as e:

                    st.error(f"Error: {e}")
