from pathlib import Path

from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import CharacterTextSplitter, MarkdownTextSplitter

DATA_DIR = Path(__file__).parent.parent / "data"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _load_documents() -> list[str]:
    lines = []
    for path in DATA_DIR.glob("**/*"):
        if path.suffix in {".md", ".txt"} and path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped:
                    lines.append(stripped)
    return lines


def _build_vectorstore() -> FAISS:
    raw_lines = _load_documents()

    md_splitter = MarkdownTextSplitter(chunk_size=300, chunk_overlap=30)
    char_splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=30)

    md_chunks = md_splitter.create_documents(raw_lines)
    char_chunks = char_splitter.create_documents(raw_lines)

    all_chunks = md_chunks + char_chunks
    texts = list({doc.page_content for doc in all_chunks if doc.page_content.strip()})

    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.from_texts(texts, embeddings)


_vectorstore: FAISS | None = None


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = _build_vectorstore()
    return _vectorstore


@tool
def zelda_rag(query: str) -> str:
    """Search the Zelda knowledge base for information about characters, items, places, and lore."""
    docs = get_vectorstore().similarity_search(query, k=4)
    return "\n\n".join(doc.page_content for doc in docs)
