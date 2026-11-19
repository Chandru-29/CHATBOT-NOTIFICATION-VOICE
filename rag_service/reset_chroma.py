import chromadb
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_DB_PATH = os.path.join(BASE_DIR, "vector_store")

client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

print("Collections before deletion:")
print([c.name for c in client.list_collections()])

try:
    client.delete_collection("knowledge")
    print("\n'knowledge' collection deleted successfully.")
except Exception as e:
    print(f"\nCould not delete collection: {e}")

print("\nCollections after deletion:")
print([c.name for c in client.list_collections()])
