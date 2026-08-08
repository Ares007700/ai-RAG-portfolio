from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

# Pretend these are chunks from a document you'd eventually load from a file
documents = [
    "The FastAPI framework uses Python type hints for validation.",
    "SQLAlchemy is an ORM that maps Python classes to database tables.",
    "Cats are independent animals that sleep most of the day.",
    "JWT tokens are signed, not encrypted, and contain an expiration claim.",
    "The Eiffel Tower is located in Paris, France."
]

doc_embeddings = model.encode(documents)

query = "How does authentication work with tokens?"
query_embedding = model.encode(query)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

scores = [cosine_similarity(query_embedding, doc_emb) for doc_emb in doc_embeddings]

# Pair each score with its document, sort by score descending
ranked = sorted(zip(scores, documents), key=lambda x: x[0], reverse=True)

for score, doc in ranked:
    print(f"{score:.3f} — {doc}")