import re
from pathlib import Path
import chromadb
from chromadb.utils import embedding_functions

SCRIPT_DIR = Path(__file__).resolve().parent #this line will create a path for the script directory
DB_DIR = SCRIPT_DIR / "chroma_db" #this line will create a path for the database directory

def split_into_sections(text): #this function will split the text into sections based on headers
    lines = text.split("\n")
    sections = []
    current_header = "Introduction"
    current_lines = []

    for line in lines: #this loop will iterate through each line in the text and check if it is a header or not
        stripped = line.strip()
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

def ingest_document(filepath, collection):
    """Chunk a document and add it to the collection, tagged with its source filename."""
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    sections = split_into_sections(text)
    filename = Path(filepath).name

    chunks = []
    metadatas = []
    for header, content in sections:
        if not content:
            continue
        for c in chunk_text(content):
            chunks.append(f"{header}: {c}")
            metadatas.append({"source": filename, "section": header})

    # IDs must be unique across the whole collection, not just per-document,
    # so we prefix with the filename to avoid collisions between documents
    ids = [f"{filename}_chunk_{i}" for i in range(len(chunks))]

    collection.add(documents=chunks, metadatas=metadatas, ids=ids)
    print(f"Ingested {filename}: {len(chunks)} chunks")

# --- Setup ---
DB_DIR.mkdir(parents=True, exist_ok=True)
client = chromadb.PersistentClient(path=str(DB_DIR))

ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-mpnet-base-v2")

collection = client.get_or_create_collection(
    name="multi_hero_guides",
    embedding_function=ef
)

# --- Ingest both documents ---
ingest_document(SCRIPT_DIR / "sample_notes.txt", collection)
ingest_document(SCRIPT_DIR / "sample_notes_2.txt", collection)

print("\nTotal documents in collection:", collection.count())

# --- Test retrieval, checking the 'source' metadata on each result ---
def test_query(query, n_results=4):
    results = collection.query(query_texts=[query], n_results=n_results)
    print(f"\nQuery: {query}\n")
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        print(f"{distance:.3f} — [{meta['source']} / {meta['section']}] {doc[:100]}...")

test_query("How should I play Paquito in the late game?")
test_query("Tell me about the Lesley combos")  # adjust wording to fit your 2nd hero