from sentence_transformers import SentenceTransformer
import numpy as np

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