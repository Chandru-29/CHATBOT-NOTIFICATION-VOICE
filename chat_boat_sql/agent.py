# from google.adk.agents.llm_agent import Agent
# from google.adk.tools.agent_tool import AgentTool
# from toolbox_core import ToolboxSyncClient

# from chat_boat_sql.warehouse_agent import warehouse_agent
# from rag_service.rag_tool import retrieve_knowledge
# from chat_boat_sql.warehouse_agent import warehouse_agent


# root_agent = Agent(
#     model="gemini-2.5-flash-lite",
#     name="root_agent",
#     description="Router agent that decides which specialized sub-agent should process the SQL query request.",
#    instruction='''
#             You are the primary conversational agent. Your role is to analyze the user's intent.
#             1. **Greeting & Conversation**: If the user's input is a greeting (like "hi", "hello"), general chat, or a question about your capabilities, you **MUST NOT** use any tools. Simply respond conversationally.
       
#             # If someone asks "Who are you", or any thing related reply-> "I am MOBY- Your personal agent" and if the query is "who developed you?" reply-> "I am Developed by Harsh" and if the query is "for whom you work?" reply -> "I work for MOBILLOR TECHNOLOGIES.".
#             # Your ONLY responsibility is to analyze the user's intent and delegate the query to the correct sub-agent.

#            2. **Delegation**: -  
                                                               
#              WAREHOUSE / ERP DATA

# YOU MUST:
# - Call `warehouse_agent`
# - Pass the FULL ORIGINAL USER QUERY
# - RETURN ONLY the tool call
# - STOP

#             3. **Security**: You are completely unaware of the database schema and cannot generate SQL yourself. Your sole function is delegation for data retrieval or conversational responses.
            
                   
           

#         ''',

 
#     #  sub_agents=[ pharma_agent],
#      sub_agents=[ warehouse_agent],
#     #  sub_agents=[ wh_agent],


        
      
# )






# # def handle_query(user_query):

# #     routed = root_agent.generate(user_query)

# #     knowledge = retrieve_knowledge(user_query)

# #     if not knowledge:
# #         return "No schema found"

# #     knowledge_text = "\n\n".join(knowledge)


# #     prompt = f"""
# # You MUST ONLY use the following database knowledge:

# # {knowledge_text}

# # User Query:
# # {user_query}
# # """

# #     response = warehouse_agent.generate(prompt)

# #     return response.text
















# from google.adk.agents.llm_agent import Agent
# from google.adk.tools.agent_tool import AgentTool

# from chat_boat_sql.warehouse_agent import warehouse_agent


# root_agent = Agent(
#     model="gemini-3.5-flash-lite",
#     name="root_agent",
#     description="Router agent that decides which specialized sub-agent should process the SQL query request.",
#    instruction='''
#             You are the primary conversational agent. Your role is to analyze the user's intent.
#             1. **Greeting & Conversation**: If the user's input is a greeting (like "hi", "hello"), general chat, or a question about your capabilities, you **MUST NOT** use any tools. Simply respond conversationally.
       
#             # If someone asks "Who are you", or any thing related reply-> "I am MOBY- Your personal agent" and if the query is "who developed you?" reply-> "I am Developed by Harsh" and if the query is "for whom you work?" reply -> "I work for MOBILLOR TECHNOLOGIES.".
#             # Your ONLY responsibility is to analyze the user's intent and delegate the query to the correct sub-agent.

#            2. **Delegation**: -  
                                                               
#                                    WAREHOUSE / ERP DATA
# If the query mentions ANY of:
#         - GRN
#         - picklist
#         - inventory
#         - stock
#         - warehouse
#         - location
#         - item
#         - quantity
#         - batch
#         - lot

# YOU MUST:
# - Call `warehouse_agent`
# - Pass the FULL ORIGINAL USER QUERY
# - RETURN ONLY the tool call
# - STOP

#             3. **Security**: You are completely unaware of the database schema and cannot generate SQL yourself. Your sole function is delegation for data retrieval or conversational responses.
#             4. **SQL Information**: whenever you use distinct word in the query, always use it after select word only.
#             5. **Never** Show the sql query whethere it is asked or not.
#             6.  
                   
           

#         ''',

 
#     #  sub_agents=[ pharma_agent],
#      sub_agents=[ warehouse_agent],
#     #  sub_agents=[ wh_agent],

#     #  sub_agents =[analytics_agent],
#     #  tools=[   
#     #     *tools  
#     # ],
        
      
# )






# # def handle_query(user_query: str):
# #     routed = check_and_route(user_query)

# #     # Cache HIT: SQL was already executed against the DB
# #     if routed["source"] == "cache":
# #         return routed["result"]

# #     # Cache MISS: pass the question to the root agent
# #     response = root_agent.generate(routed["question"])
# #     return response.text










# from google.adk.apps import App
# from google.adk.apps._configs import EventsCompactionConfig # type: ignore
from chat_boat_sql.chat_history_summarizer import ChatHistorySummarizer
from google.adk.apps.app import App, EventsCompactionConfig


from google.adk.agents.llm_agent import Agent
from google.adk.tools.agent_tool import AgentTool

from chat_boat_sql.warehouse_agent import warehouse_agent


root_agent = Agent(
    model="gemini-2.5-flash",
    name="root_agent",
    description="Router agent that decides which specialized sub-agent should process the SQL query request.",
      instruction='''# ROLE & OBJECTIVE
You are MOBY, the primary conversational router agent developed by Mobillor. Your sole responsibility is intent classification and delegation.

# 1. GREETINGS & IDENTITY
- On greetings ("hi", "hello"), chit-chat, or capability queries: Respond conversationally. DO NOT call any tools.
- "Who are you?": "I am MOBY - Your personal Warehouse Agent."
- "For whom do you work?": "I work for MOBILLOR TECHNOLOGIES."
- "Who developed you?": "I was developed by Mobillor Technologies."

# 2. ROUTING LOGIC (WAREHOUSE & ERP DATA)
DELEGATE to `warehouse_agent` if the user query involves:
1. Warehouse/ERP entities: [GRN, picklist, pickup list, inventory, stock, warehouse, location, bin, item, material, SKU, quantity, batch, lot, PIV, process order, PO, material movement, transfer, pallet, quality inspection, rejection].
2. Follow-up queries referring to previously retrieved warehouse data (e.g., "filter that by plant 1001", "show top 5 of those", "who is the operator?").

WHEN DELEGATING:
1. Pass the FULL, UNMODIFIED user query to `warehouse_agent`.
2. Return ONLY the tool call.
3. STOP execution immediately.

# 3. OUT-OF-SCOPE QUERIES
If the question is unrelated to warehouse/ERP operations and not a greeting:
- Politely decline: "I am specialized in Warehouse and ERP data operations. Please ask queries related to inventory, picklists, process orders, or material movements."
- DO NOT call any tools.

# 4. CONSTRAINTS & SECURITY
- SCHEMA BLIND: You have zero knowledge of database schemas and MUST NEVER attempt to generate or discuss SQL queries.
- STRICT PRIVACY: NEVER output, reveal, or display SQL queries under any circumstances, even if explicitly requested by the user.''',


 
    #  sub_agents=[ pharma_agent],
     sub_agents=[ warehouse_agent],
    #  sub_agents=[ wh_agent],

    #  sub_agents =[analytics_agent],
    #  tools=[   
    #     *tools  
    # ],
        
      
)
pruning_summarizer = ChatHistorySummarizer()

compaction_config = EventsCompactionConfig(
    summarizer=pruning_summarizer,
    compaction_interval=2,
    overlap_size=1,
    token_threshold=2500,
    event_retention_size=8,
)

app = App(
    name="chat_boat_sql",
    root_agent=root_agent,
    events_compaction_config=compaction_config, 
)


# def handle_query(user_query: str):
#     routed = check_and_route(user_query)

#     # Cache HIT: SQL was already executed against the DB
#     if routed["source"] == "cache":
#         return routed["result"]

#     # Cache MISS: pass the question to the root agent
#     response = root_agent.generate(routed["question"])
#     return response.text




