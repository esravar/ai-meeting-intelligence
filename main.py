import os
import shutil
import streamlit as st
from pathlib import Path
import tempfile

from transcribe import transcribe_audio
from meeting_notes import generate_meeting_notes
from pdf_generator import create_meeting_pdf

from rag import (
    load_pdf,
    chunk_text,
    create_vectorstore,
    load_existing_vectorstore,
    retrieve_context,
    PERSIST_DIRECTORY,
)
from llm import ask_llm


st.set_page_config(
    page_title="Corporate Knowledge Assistant",
    layout="wide",
)

st.title("Corporate Knowledge Assistant")
st.caption("Multi-document RAG + Agentic AI MVP")

if "db" not in st.session_state:
    st.session_state.db = None

if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []


st.subheader("1. Upload source documents")

uploaded_pdf_files = st.file_uploader(
    "Upload one or more PDF documents",
    type=["pdf"],
    accept_multiple_files=True,
    key="pdf_uploader",
)

uploaded_audio_files = st.file_uploader(
    "Upload one or more meeting audio files",
    type=["mp3", "wav", "m4a", "aiff"],
    accept_multiple_files=True,
    key="audio_uploader",
)

process_sources = st.button("Process Sources / Create Knowledge Base")

if process_sources:
    if not uploaded_pdf_files and not uploaded_audio_files:
        st.warning("Please upload at least one PDF or audio file.")
    else:
        st.success("Processing started.")

col1, col2 = st.columns(2)

with col1:
    create_kb = st.button("Create / Rebuild Knowledge Base")

with col2:
    clear_kb = st.button("Clear Knowledge Base")


if clear_kb:
    if os.path.exists(PERSIST_DIRECTORY):
        shutil.rmtree(PERSIST_DIRECTORY)

    st.session_state.db = None
    st.session_state.indexed_files = []

    st.success("Knowledge base cleared.")


if create_kb:
    if not uploaded_pdf_files and not uploaded_audio_files:
        st.warning("Please upload at least one PDF or audio file.")
    else:
        all_chunks = []
        indexed_files = []

        # 1) PDF files
        if uploaded_pdf_files:
            with st.spinner("Reading and chunking PDFs..."):
                for file in uploaded_pdf_files:
                    text = load_pdf(file)
                    chunks = chunk_text(text, source_name=file.name)

                    all_chunks.extend(chunks)
                    indexed_files.append(
                        {
                            "file": file.name,
                            "type": "PDF",
                            "chunks": len(chunks),
                        }
                    )

        # 2) Audio files - şimdilik sadece placeholder
        if uploaded_audio_files:
            generated_dir = Path("generated_meeting_notes")
            generated_dir.mkdir(exist_ok=True)

            with st.spinner("Transcribing audio and generating meeting notes..."):
                for audio_file in uploaded_audio_files:
                    st.info(f"Processing audio: {audio_file.name}")

                    suffix = Path(audio_file.name).suffix

                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(audio_file.read())
                        temp_audio_path = tmp.name

                    transcript = transcribe_audio(temp_audio_path)

                    with st.expander(f"Transcript: {audio_file.name}"):
                        st.write(transcript)

                    meeting_notes = generate_meeting_notes(transcript)

                    with st.expander(f"Generated meeting notes: {audio_file.name}"):
                        st.write(meeting_notes)

                    pdf_path = generated_dir / f"{Path(audio_file.name).stem}_meeting_notes.pdf"

                    create_meeting_pdf(
                        text=meeting_notes,
                        output_path=str(pdf_path),
                    )

                    chunks = chunk_text(
                        meeting_notes,
                        source_name=pdf_path.name,
                    )

                    all_chunks.extend(chunks)

                    indexed_files.append(
                        {
                            "file": pdf_path.name,
                            "type": "Generated PDF from Audio",
                            "chunks": len(chunks),
                        }
                    )

                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label=f"Download generated PDF: {pdf_path.name}",
                            data=f,
                            file_name=pdf_path.name,
                            mime="application/pdf",
                        )

        if all_chunks:
            st.write(f"Total chunks created: {len(all_chunks)}")

            with st.spinner("Creating embeddings and vector database..."):
                st.session_state.db = create_vectorstore(all_chunks)

            st.session_state.indexed_files = indexed_files
            st.success("Knowledge base created successfully.")
        else:
            st.warning("No text chunks were created yet. Audio transcription is not connected yet.")

st.divider()

st.subheader("2. Knowledge base status")

if st.session_state.indexed_files:
    st.write("Indexed documents:")

    for item in st.session_state.indexed_files:
        st.write(f"- {item['file']} — {item['chunks']} chunks")
else:
    st.info("No documents indexed yet.")


if st.session_state.db is None and os.path.exists(PERSIST_DIRECTORY):
    if st.button("Load Existing Knowledge Base"):
        st.session_state.db = load_existing_vectorstore()
        st.success("Existing knowledge base loaded.")


st.divider()

st.subheader("3. Ask questions across all documents")

question = st.text_input(
    "Ask a question",
    placeholder="Example: What were the unresolved risks across the meetings?",
)

if question:
    if st.session_state.db is None:
        st.warning("Please create or load a knowledge base first.")
    else:
        with st.spinner("Retrieving relevant context..."):
            context, sources = retrieve_context(
                st.session_state.db,
                question,
                k=5,
            )

        with st.expander("Retrieved context"):
            st.write(context)

        result = ask_llm(context, question)

        st.write(result["answer"])

        if result["model_used"]:
            st.caption(f"Model used: {result['model_used']}")

        st.subheader("Sources used")
        for source in sources:
            st.write(f"- {source}")