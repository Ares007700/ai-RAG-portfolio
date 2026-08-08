import re

def chunk_text(text, chunk_size=500, overlap_sentences=1):
    # Split into sentences (simple version — splits on . ! ? followed by space/newline)
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            # keep last N sentences for overlap
            current_chunk = current_chunk[-overlap_sentences:]
            current_length = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks