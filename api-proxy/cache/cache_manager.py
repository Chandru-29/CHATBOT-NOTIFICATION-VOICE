from .question_cache import QuestionCache
# from .semantic_cache import SemanticCache


class CacheManager:

    def __init__(self):

        # Question Cache
        self.question_cache = QuestionCache(ttl=10)

        # Semantic Cache
        # self.semantic_cache = SemanticCache()

    # ------------------------------------------------
    # Question Cache
    # ------------------------------------------------

    def get_question_cache(self, question):

        return self.question_cache.get(question)

    def store_question_cache(self, question, response):

        self.question_cache.set(question, response)


    # ------------------------------------
    # Semantic Cache Search
    # ------------------------------------

    # # def get_semantic_cache(
    #     self,
    #     embedding,
    #     limit=None
    # ):

        # return self.semantic_cache.search(

        #     embedding=embedding,

        #     limit=limit

        # )

    
#     # ------------------------------------------------
#     # Semantic Cache
#     # ------------------------------------------------

#     def store_semantic_cache(
#         self,
#         question,
#         embedding,
#         response,
#         limit=None
#     ):

#         self.semantic_cache.store(

#             question=question,

#             embedding=embedding,

#             response=response,

#             limit=limit

#         )


cache_manager = CacheManager()