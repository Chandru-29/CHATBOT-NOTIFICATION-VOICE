from sentence_transformers import SentenceTransformer


class EmbeddingService:

    def __init__(self):

        print("[INFO] Loading Embedding Model...")

        self.model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

        print("[INFO] Embedding Model Ready")

    def embed(self, text: str):

        return self.model.encode(text).tolist()


# Singleton Instance
embedding_service = EmbeddingService()