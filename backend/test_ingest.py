import re
from pathlib import Path

try:
    import chromadb  # type: ignore[import]
except ModuleNotFoundError as exc:
    raise ImportError("chromadb package not found. Install it with 'pip install chromadb'") from exc

SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLE_FILE = SCRIPT_DIR / "sample_notes.txt"
DB_DIR = SCRIPT_DIR / "chroma_db"

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

chunks = chunk_text(sample_text)
print(f"Chunking into {len(chunks)} pieces...")

DB_DIR.mkdir(parents=True, exist_ok=True)
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_or_create_collection(name="paquito_guide")

collection.add(
    documents=chunks,
    ids=[f"chunk_{i}" for i in range(len(chunks))]
)

print("Total documents in collection:", collection.count())

# Now actually test retrieval with a real question about the content
query = "How should I play Paquito in the late game?"
results = collection.query(query_texts=[query], n_results=6)

print(f"\nQuery: {query}\n")
for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"{distance:.3f} — {doc[:150]}...")
    print()