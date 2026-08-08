"""Small script to test sentence embeddings and cosine similarity."""

import numpy as np

try:
    from sentence_transformers import SentenceTransformer  # type: ignore[import]
except ImportError as exc:
    raise ImportError(
        "sentence-transformers is required to run this script. "
        "Install it with: pip install sentence-transformers"
    ) from exc

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    "The cat sat on the mat.",
    "A feline rested on the rug.",
    "I need to fix my car's engine."
]

embeddings = model.encode(sentences)

print("Shape of one embedding:", embeddings[0].shape)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print("Sentence 1 vs 2 (similar meaning):", cosine_similarity(embeddings[0], embeddings[1]))
print("Sentence 1 vs 3 (different meaning):", cosine_similarity(embeddings[0], embeddings[2]))