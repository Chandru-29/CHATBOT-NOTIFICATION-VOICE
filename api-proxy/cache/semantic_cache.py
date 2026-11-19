# # import os
# # import json
# # import time
# # import hashlib
# # import chromadb

# # from dotenv import load_dotenv

# # load_dotenv()


# # class SemanticCache:

# #     def __init__(self):

# #         db_path = os.getenv("CHROMA_DB_PATH")

# #         self.threshold = float(
# #             os.getenv(
# #                 "SEMANTIC_CACHE_THRESHOLD",
# #                 "0.99"
# #             )
# #         )

# #         collection_name = os.getenv(
# #             "SEMANTIC_CACHE_COLLECTION",
# #             "semantic_cache"
# #         )

# #         print(f" Chroma Path : {db_path}")

# #         self.client = chromadb.PersistentClient(
# #             path=db_path
# #         )

# #         self.collection = self.client.get_or_create_collection(
# #             name=collection_name
# #         )

# #         print(
# #             f"✅ Semantic Cache Connected : {collection_name}"
# #         )

# #     # ---------------------------------------------------
# #     # STORE
# #     # ---------------------------------------------------

# #     def store(
# #         self,
# #         question,
# #         embedding,
# #         response,
# #         limit=None
# #     ):

# #         try:

# #             cache_id = hashlib.sha256(
# #                 f"{question}_{limit}".encode()
# #             ).hexdigest()

# #             self.collection.upsert(

# #                 ids=[cache_id],

# #                 documents=[question],

# #                 embeddings=[embedding],

# #                 metadatas=[

# #                     {

# #                         "question": question,

# #                         "limit": str(limit),

# #                         "created_at": str(time.time()),

# #                         "response": json.dumps(response)

# #                     }

# #                 ]

# #             )

# #             print(
# #                 f"✅ Semantic Cache Stored : {question}"
# #             )

# #         except Exception as e:

# #             print(
# #                 "Semantic Cache Store Error :",
# #                 str(e)
# #             )
              
# #     # ---------------------------------------------------
# #     # SEARCH
# #     # ---------------------------------------------------

# #     def search(
# #         self,
# #         embedding,
# #         limit=None
# #     ):

# #         try:

# #             results = self.collection.query(

# #                 query_embeddings=[embedding],

# #                 n_results=1,

# #                 include=[
# #                     "metadatas",
# #                     "distances"
# #                 ]

# #             )

# #             if not results["ids"][0]:

# #                 return None

# #             metadata = results["metadatas"][0][0]

# #             distance = results["distances"][0][0]

# #             similarity = 1 - distance

# #             print(
# #                 f"Semantic Similarity : {similarity}"
# #             )

# #             # Threshold check

# #             if similarity < self.threshold:

# #                 return None

# #             # Limit check

# #             if str(limit) != metadata.get("limit"):

# #                 return None

# #             print("⚡ Semantic Cache HIT")

# #             return json.loads(
# #                 metadata["response"]
# #             )

# #         except Exception as e:

# #             print(
# #                 "Semantic Cache Search Error :",
# #                 str(e)
# #             )

#             # return None









# import os
# import json
# import time
# import hashlib
# import chromadb

# from dotenv import load_dotenv

# load_dotenv()


# class SemanticCache:

#     def __init__(self):

#         db_path = os.getenv("CHROMA_DB_PATH")

#         self.threshold = float(
#             os.getenv(
#                 "SEMANTIC_CACHE_THRESHOLD",
#                 "0.99"
#             )
#         )

#         # Cache TTL (10 seconds)
#         self.ttl = int(
#             os.getenv(
#                 "SEMANTIC_CACHE_TTL",
#                 "10"
#             )
#         )

#         collection_name = os.getenv(
#             "SEMANTIC_CACHE_COLLECTION",
#             "semantic_cache"
#         )

#         print(f"Chroma Path : {db_path}")

#         self.client = chromadb.PersistentClient(
#             path=db_path
#         )

#         self.collection = self.client.get_or_create_collection(
#             name=collection_name
#         )

#         print(
#             f"✅ Semantic Cache Connected : {collection_name}"
#         )

#     # ---------------------------------------------------
#     # STORE
#     # ---------------------------------------------------

#     def store(
#         self,
#         question,
#         embedding,
#         response,
#         limit=None
#     ):

#         try:

#             cache_id = hashlib.sha256(
#                 f"{question}_{limit}".encode()
#             ).hexdigest()

#             self.collection.upsert(

#                 ids=[cache_id],

#                 documents=[question],

#                 embeddings=[embedding],

#                 metadatas=[

#                     {

#                         "question": question,

#                         "limit": str(limit),

#                         "created_at": str(time.time()),

#                         "response": json.dumps(response)

#                     }

#                 ]

#             )

#             print(
#                 f"✅ Semantic Cache Stored : {question}"
#             )

#         except Exception as e:

#             print(
#                 "Semantic Cache Store Error :",
#                 str(e)
#             )

#     # ---------------------------------------------------
#     # SEARCH
#     # ---------------------------------------------------

#     def search(
#         self,
#         embedding,
#         limit=None
#     ):

#         try:

#             results = self.collection.query(

#                 query_embeddings=[embedding],

#                 n_results=1,

#                 include=[
#                     "metadatas",
#                     "distances"
#                 ]

#             )

#             if not results["ids"][0]:
#                 return None

#             metadata = results["metadatas"][0][0]
#             cache_id = results["ids"][0][0]

#             # -----------------------------
#             # TTL CHECK
#             # -----------------------------
          
#             created_at = float(metadata["created_at"])

#             if time.time() - created_at > self.ttl:

#                 print("🗑 Semantic Cache Expired")

#                 return None

#             # -----------------------------
#             # SIMILARITY CHECK
#             # -----------------------------
#             distance = results["distances"][0][0]

#             similarity = 1 - distance

#             print(
#                 f"Semantic Similarity : {similarity}"
#             )

#             if similarity < self.threshold:
#                 return None

#             # -----------------------------
#             # LIMIT CHECK
#             # -----------------------------
#             if str(limit) != metadata.get("limit"):
#                 return None

#             print("⚡ Semantic Cache HIT")

#             return json.loads(
#                 metadata["response"]
#             )

#         except Exception as e:

#             print(
#                 "Semantic Cache Search Error :",
#                 str(e)
#             )

#             return None