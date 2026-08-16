import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLE_FILE = SCRIPT_DIR / "sample_notes.txt"
DB_DIR = SCRIPT_DIR / "chroma_db"

def split_into_sections(text):
    """Split text into (header, content) pairs based on short standalone lines."""
    lines = text.split("\n")
    sections = []
    current_header = "Introduction"  # default for text before any detected header
    current_lines = []

    for line in lines:
        stripped = line.strip()
        # Heuristic: a "header" line is short, non-empty, and doesn't end in sentence punctuation
        is_header = (
            0 < len(stripped) < 40
            and not stripped.endswith((".", "!", "?", ",", ":"))
            and not stripped.startswith(("-", "*"))
        )
        if is_header:
            if current_lines:
                sections.append((current_header, " ".join(current_lines).strip()))
            current_header = stripped
            current_lines = []
        else:
            if stripped:
                current_lines.append(stripped)

    if current_lines:
        sections.append((current_header, " ".join(current_lines).strip()))

    return sections

def chunk_text(text, chunk_size=600, overlap_sentences=1):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    result_chunks = []
    current_chunk = []
    current_length = 0

    for sentence in sentences:
        if current_length + len(sentence) > chunk_size and current_chunk:
            result_chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-overlap_sentences:]
            current_length = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += len(sentence)

    if current_chunk:
        result_chunks.append(" ".join(current_chunk))

    return result_chunks

with open(SAMPLE_FILE, "r", encoding="utf-8") as f:
    sample_text = f.read()

sections = split_into_sections(sample_text)
print(f"Detected {len(sections)} sections:")
for header, content in sections:
    print(f"  - {header} ({len(content)} chars)")

# Chunk each section separately, prepending the header to every chunk
final_chunks = []
for header, content in sections:
    if not content:
        continue
    section_chunks = chunk_text(content)
    for c in section_chunks:
        final_chunks.append(f"{header}: {c}")

print(f"\nTotal chunks: {len(final_chunks)}")

DB_DIR.mkdir(parents=True, exist_ok=True)
client = chromadb.PersistentClient(path=str(DB_DIR))

sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-mpnet-base-v2"
)

collection = client.get_or_create_collection(
    name="paquito_guide_headers",
    embedding_function=sentence_transformer_ef
)

collection.add(
    documents=final_chunks,
    ids=[f"chunk_{i}" for i in range(len(final_chunks))]
)

print("Total documents in collection:", collection.count())

query = "How should I play Paquito in the late game?"
results = collection.query(query_texts=[query], n_results=6)

print(f"\nQuery: {query}\n")
for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"{distance:.3f} — {doc[:150]}...")
    print()