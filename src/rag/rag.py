from pathlib import Path
import re

from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

DATA_DIR = Path(__file__).parent.parent / "data"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def _parse_markdown_sections(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    docs = []
    current_heading = None
    current_lines = []

    for line in text.splitlines():
        match = re.match(r"^(#{1,3})\s+(.+)", line)
        if match:
            if current_heading is not None and current_lines:
                docs.append(Document(
                    page_content="\n".join(current_lines).strip(),
                    metadata={"section": current_heading, "source": path.name},
                ))
            current_heading = match.group(2).strip()
            current_lines = []
        else:
            stripped = line.strip()
            if stripped:
                current_lines.append(stripped)

    if current_heading is not None and current_lines:
        docs.append(Document(
            page_content="\n".join(current_lines).strip(),
            metadata={"section": current_heading, "source": path.name},
        ))

    return docs


def _load_documents() -> list[Document]:
    docs = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)

    for path in DATA_DIR.glob("**/*"):
        if path.suffix == ".md" and path.is_file():
            sections = _parse_markdown_sections(path)
            for section in sections:
                if len(section.page_content) > 400:
                    chunks = splitter.split_documents([section])
                    docs.extend(chunks)
                else:
                    docs.append(section)
        elif path.suffix == ".txt" and path.is_file():
            text = path.read_text(encoding="utf-8")
            chunks = splitter.create_documents(
                [text], metadatas=[{"source": path.name}]
            )
            docs.extend(chunks)

    return docs


def _build_vectorstore() -> FAISS:
    docs = _load_documents()
    embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
    return FAISS.from_documents(docs, embeddings)


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
    results = []
    for doc in docs:
        section = doc.metadata.get("section")
        prefix = f"[{section}]\n" if section else ""
        results.append(f"{prefix}{doc.page_content}")
    return "\n\n".join(results)
