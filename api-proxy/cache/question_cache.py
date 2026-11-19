import time
import re

class QuestionCache:
    def __init__(self, ttl=25):
        """
        ttl = cache expiry in seconds
        default = 10 seconds
        """
        self.cache = {}
        self.ttl = ttl

    def normalize(self, question: str) -> str:
        """
        Same normalization as Node-RED
        """
        
        return re.sub(
            r"\s+",
            "_",
            question.strip().lower()
        )
    def get(self, question: str):
        """
        Return cached response if valid
        """ 
        key = self.normalize(question)

        if key not in self.cache:
            return None

        item = self.cache[key]

        # Expired
        if item["expiry"] < time.time():
            del self.cache[key]
            return None

        print(f"⚡ Question Cache HIT: {key}")

        return item["response"]

    def set(self, question: str, response):
        """
        Store response in cache
        """
        key = self.normalize(question)

        self.cache[key] = {
            "response": response,
            "expiry": time.time() + self.ttl
        }

        print(f"✅ Question Cached: {key}")

    def cleanup(self):
        """
        Remove expired entries
        """
        current_time = time.time()

        expired_keys = [
            key
            for key, value in self.cache.items()
            if value["expiry"] < current_time
        ]

        for key in expired_keys:
            del self.cache[key]

