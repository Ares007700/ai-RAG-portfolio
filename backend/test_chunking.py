def chunk_text(text, chunk_size=800, overlap=80):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

with open("sample_notes.txt", "r", encoding="utf-8") as f:
    text = f.read()

chunks = chunk_text(text)

print(f"Document length: {len(text)} characters")
print(f"Number of chunks: {len(chunks)}")
print()
for i, c in enumerate(chunks):
    print(f"--- Chunk {i} ---")
    print(c)
    print()