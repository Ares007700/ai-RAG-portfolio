import chromadb

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(name="test_docs")

documents = [
    "The FastAPI framework uses Python type hints for validation.",
    "SQLAlchemy is an ORM that maps Python classes to database tables.",
    "Cats are independent animals that sleep most of the day.",
    "JWT tokens are signed, not encrypted, and contain an expiration claim.",
    "The Eiffel Tower is located in Paris, France."
]

# Chroma handles embedding internally by default — no manual encode() needed
collection.add(
    documents=documents,
    ids=[f"doc_{i}" for i in range(len(documents))]
)
print("Total documents in collection:", collection.count())
results = collection.query(
    query_texts=["How does authentication work with tokens?"],
    n_results=3
)

for doc, distance in zip(results["documents"][0], results["distances"][0]):
    print(f"{distance:.3f} — {doc}")