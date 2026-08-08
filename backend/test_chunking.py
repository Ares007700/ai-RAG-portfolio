import re

def chunk_text(text, chunk_size=600, overlap_sentences=1):
    # Split into sentences (simple version — splits on . ! ? followed by space/newline)
    sentences = re.split(r'(?<=[.!?])\s+', text)  #it will split the text into sentences based on punctuation marks followed by whitespace
    
    result_chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) > chunk_size and current_chunk:
            result_chunks.append(" ".join(current_chunk))
            # keep last N sentences for overlap
            current_chunk = current_chunk[-overlap_sentences:]
            current_length = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    if current_chunk:
        result_chunks.append(" ".join(current_chunk))
    
    return result_chunks

with open("sample_notes.txt", "r", encoding="utf-8") as f:
    sample_text = f.read()

chunks = chunk_text(sample_text)

print(f"Document length: {len(sample_text)} characters")
print(f"Number of chunks: {len(chunks)}")
print()
for i, c in enumerate(chunks):
    print(f"--- Chunk {i} ---")
    print(c)
    print()