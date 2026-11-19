# import time
# import re

# class QuestionCache:
#     def __init__(self, ttl=100):
#         self.cache = {}
#         self.ttl = ttl

#     def normalize(self, question: str) -> str:
#         return re.sub(
#             r"\s+",
#             "_",
#             question.strip().lower()
#         )

#     def get(self, question: str):

#         key = self.normalize(question)

#         if key not in self.cache:
#             return None

#         item = self.cache[key]

#         if item["expiry"] < time.time():
#             del self.cache[key]
#             return None

#         print(f"⚡ Question Cache HIT: {key}")

#         return item["response"]

#     def set(self, question: str, response):

#         key = self.normalize(question)

#         self.cache[key] = {
#             "response": response,
#             "expiry": time.time() + self.ttl
#         }

#         print(f"✅ Question Cached: {key}")

#     def cleanup(self):

#         current_time = time.time()

#         expired_keys = [
#             key
#             for key, value in self.cache.items()
#             if value["expiry"] < current_time
#         ]

#         for key in expired_keys:
#             del self.cache[key]

#     # -------------------------
#     # NEW METHODS
#     # -------------------------

#     def clear(self):
#         """Clear the entire cache."""
#         count = len(self.cache)
#         self.cache.clear()
#         print(f"🗑️ Question Cache Cleared ({count} entries removed)")

#     def size(self):
#         """Return number of cached questions."""
#         return len(self.cache)

#     def keys(self):
#         """List all cached questions."""
#         return list(self.cache.keys())






from question_cache import QuestionCache

cache = QuestionCache()

cache.clear()