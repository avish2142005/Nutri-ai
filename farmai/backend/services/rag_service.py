"""RAG (Retrieval-Augmented Generation) Service.

Provides semantic retrieval over the agricultural knowledge base.
Falls back gracefully if sentence-transformers / faiss are not available,
using a simple keyword-overlap scorer instead.
"""
import os
import json
import glob
import logging

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "knowledge_base", "docs")
INDEX_PATH = os.path.join(BASE_DIR, "knowledge_base", "faiss_index.bin")
CHUNKS_PATH = os.path.join(BASE_DIR, "knowledge_base", "chunks.json")
CHUNK_CHARS = 1800
OVERLAP_CHARS = 300

# ── lazy-loaded globals ────────────────────────────────────────────────────────
_model = None
_index = None
_chunks: list[str] = []

# ── graceful import ─────────────────────────────────────────────────────────────
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    import faiss as _faiss
    _SEMANTIC_AVAILABLE = True
except Exception as _e:
    _SEMANTIC_AVAILABLE = False
    logger.warning("sentence-transformers/faiss not available; using keyword fallback. (%s)", _e)


# ── helpers ──────────────────────────────────────────────────────────────────────
def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping char-based chunks."""
    result = []
    start = 0
    while start < len(text):
        end = min(start + CHUNK_CHARS, len(text))
        result.append(text[start:end])
        start += CHUNK_CHARS - OVERLAP_CHARS
    return result


def _load_all_docs() -> tuple[list[str], list[str]]:
    """Return (raw_chunks, source_labels) for every markdown doc found."""
    all_chunks: list[str] = []
    sources: list[str] = []
    md_files = glob.glob(os.path.join(DOCS_DIR, "*.md"))
    for md_file in md_files:
        filename = os.path.basename(md_file)
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                text = f.read()
            for chunk in _chunk_text(text):
                all_chunks.append(chunk)
                sources.append(filename)
        except Exception as exc:
            logger.warning("Could not read %s: %s", md_file, exc)
    return all_chunks, sources


def build_index() -> None:
    """Build FAISS index from docs directory and persist to disk."""
    global _model, _index, _chunks

    raw_chunks, _ = _load_all_docs()
    if not raw_chunks:
        logger.warning("No markdown docs found under %s – skipping index build.", DOCS_DIR)
        return

    _chunks = raw_chunks

    if not _SEMANTIC_AVAILABLE:
        logger.warning("Semantic libs unavailable – persisting only text chunks.")
        with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
            json.dump(_chunks, f)
        return

    logger.info("Loading sentence-transformer model…")
    _model = SentenceTransformer("all-MiniLM-L6-v2")

    logger.info("Encoding %d chunks…", len(_chunks))
    embeddings = _model.encode(_chunks, show_progress_bar=False).astype("float32")

    dim = embeddings.shape[1]
    _index = _faiss.IndexFlatL2(dim)
    _index.add(embeddings)

    _faiss.write_index(_index, INDEX_PATH)
    with open(CHUNKS_PATH, "w", encoding="utf-8") as f:
        json.dump(_chunks, f)
    logger.info("FAISS index built with %d vectors (dim=%d).", len(_chunks), dim)


def _ensure_index() -> None:
    """Load persisted index, or build it on first call."""
    global _model, _index, _chunks

    if _chunks:
        return  # already loaded

    # Try loading from disk
    if os.path.exists(CHUNKS_PATH):
        with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
            _chunks = json.load(f)
        logger.info("Loaded %d chunks from disk.", len(_chunks))
    else:
        logger.info("No persisted index – building now…")
        build_index()
        return

    if _SEMANTIC_AVAILABLE and os.path.exists(INDEX_PATH):
        import numpy as np  # noqa: F401
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _index = _faiss.read_index(INDEX_PATH)
        logger.info("FAISS index loaded from disk (%d vectors).", _index.ntotal)


def _keyword_retrieve(query: str, top_k: int = 4) -> list[str]:
    """Simple keyword-overlap fallback when FAISS is unavailable."""
    query_words = set(query.lower().split())
    scored = [
        (sum(1 for w in query_words if w in chunk.lower()), chunk)
        for chunk in _chunks
    ]
    scored.sort(key=lambda x: -x[0])
    return [c for _, c in scored[:top_k] if _]


def retrieve(query: str, top_k: int = 4) -> list[str]:
    """Return top-k relevant text chunks for the given query."""
    _ensure_index()

    if not _chunks:
        return []

    if _SEMANTIC_AVAILABLE and _index is not None:
        query_vec = _model.encode([query]).astype("float32")
        distances, indices = _index.search(query_vec, top_k)
        return [_chunks[i] for i in indices[0] if 0 <= i < len(_chunks)]

    return _keyword_retrieve(query, top_k)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    build_index()
    print("Done. Chunks:", len(_chunks))
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
        results = retrieve(q)
        print(f"\n=== Top results for: {q!r} ===")
        for i, r in enumerate(results, 1):
            print(f"\n--- {i} ---\n{r[:400]}")
