from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma


PERSIST_DIRECTORY = "vectorstore"


def load_pdf(file) -> str:
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def chunk_text(text: str, source_name: str) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    chunks = splitter.split_text(text)

    return [
        {
            "text": chunk,
            "metadata": {
                "source": source_name,
            },
        }
        for chunk in chunks
    ]


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def create_vectorstore(all_chunks: list[dict]):
    embeddings = get_embeddings()

    texts = [chunk["text"] for chunk in all_chunks]
    metadatas = [chunk["metadata"] for chunk in all_chunks]

    db = Chroma.from_texts(
        texts=texts,
        embedding=embeddings,
        metadatas=metadatas,
        persist_directory=PERSIST_DIRECTORY,
    )

    return db


def load_existing_vectorstore():
    embeddings = get_embeddings()

    return Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
    )


def retrieve_context(db, question: str, k: int = 5) -> tuple[str, list[str]]:
    docs = db.similarity_search(question, k=k)

    context_parts = []
    sources = []

    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "Unknown source")
        sources.append(source)

        context_parts.append(
            f"[Source {i}: {source}]\n{doc.page_content}"
        )

    unique_sources = sorted(set(sources))

    return "\n\n".join(context_parts), unique_sources