
# from fastapi import Request, APIRouter
# from fastapi.responses import JSONResponse
# import httpx
# import asyncio
# import json
# import os
# import re
# import time 

# from dotenv import load_dotenv

# from db import upsert_token_usage
# from cache import cache_manager
# from embedding_service import embedding_service

# router = APIRouter()
# load_dotenv()

# ADK_BASE_URL = os.getenv("ADK_BASE_URL")
# # ADK_BASE_URL= "https://ai-chatbot.mobillor.net/dev_api"

# client = httpx.AsyncClient(timeout=60.0)


# # ---------------------------------------------------
# # TOKEN TRACKING
# # ---------------------------------------------------

# async def track_tokens(raw_payload, userId, sessionId):

#     # print ('raw_payload',payload)
#     try:

#         print("track_tokens called:", userId, sessionId)

#         try:
#             events = json.loads(raw_payload)
#         except Exception:
#             print("Invalid JSON → skipping")
#             return

#         if isinstance(events, dict):
#             events = [events]

#         elif not isinstance(events, list):
#             print("Unexpected format:", type(events))
#             return

#         totalTokens = 0
#         promptTokens = 0
#         completionTokens = 0

#         for event in events:

#             usage = event.get("usageMetadata")

#             if not usage:
#                 continue

#             totalTokens += usage.get("totalTokenCount", 0)
#             promptTokens += usage.get("promptTokenCount", 0)
#             completionTokens += usage.get("candidatesTokenCount", 0)

#         print("Tokens:", totalTokens)

#         upsert_token_usage(

#             userId,

#             sessionId,

#             totalTokens,

#             promptTokens,

#             completionTokens

#         )

#         print("Stored in DB:", userId, sessionId)

#     except Exception as e:

#         print("Token tracking error:", str(e))


# # ---------------------------------------------------
# # QUESTION EXTRACTION
# # ---------------------------------------------------

# def extract_question(payload):

#     if payload.get("newMessage"):

#         parts = payload["newMessage"].get("parts", [])

#         if parts and "text" in parts[0]:

#             return parts[0]["text"]

#     return (

#         payload.get("question")

#         or payload.get("message")

#         or ""

#     )

# def extract_limit(question: str):

#     match = re.search(r"\b\d+\b", question)

#     if match:
#         return int(match.group())

#     return None


# # ---------------------------------------------------
# # RUN API
# # ---------------------------------------------------

# @router.post("/dev/proxy/run")
# async def proxy_run(request: Request):

#     start_total = time.perf_counter()

#     try:

#         # payload = await request.json()
#         t = time.perf_counter()
#         payload = await request.json()
#         json_time = time.perf_counter() - t
        
#         print ('payload',payload)

#         userId = payload.get("userId", "unknown_user")
#         sessionId = payload.get("sessionId", "default_session")

#         # question = extract_question(payload)
#         # limit = extract_limit(question)
#         t = time.perf_counter()

#         question = extract_question(payload)
#         limit = extract_limit(question)

#         question_time = time.perf_counter() - t

#         embedding = None

#         # ---------------------------------------------------
#         # LEVEL 1 : QUESTION CACHE
#         # ---------------------------------------------------

#         if question:

#             # cached_response = cache_manager.get_question_cache(question)

#             t = time.perf_counter()
#             cached_response = cache_manager.get_question_cache(question)
#             cache_lookup_time = time.perf_counter() - t

#             if cached_response:

#                 print("⚡ Returning Question Cache Response")

#                 return JSONResponse(

#                     content=cached_response,

#                     status_code=200

#                 )

#         # ---------------------------------------------------
#         # GENERATE EMBEDDING
#         # ---------------------------------------------------

#         # if question:

#         #     embedding = await asyncio.to_thread(

#         #         embedding_service.embed,

#         #         question

#         #     )

#         # ---------------------------------------------------
#         # LEVEL 2 : SEMANTIC CACHE
#         # ---------------------------------------------------

#         # if embedding:

#         #     cached_response = cache_manager.get_semantic_cache(

#         #         embedding=embedding,

#         #         limit=limit

#         #     )

#             # if cached_response:

#             #     print("⚡ Returning Semantic Cache Response")

#             #     # Promote to Question Cache

#             #     cache_manager.store_question_cache(

#             #         question,

#             #         cached_response

#             #     )

#             #     return JSONResponse(

#             #         content=cached_response,

#             #         status_code=200

#             #     )

#         # ---------------------------------------------------
#         # CALL ADK
#         # ---------------------------------------------------

#         url = f"{ADK_BASE_URL}/run"
#         print(url)
        
#         t = time.perf_counter()
#         response = await client.post(

#             url,

#             json=payload,

#             headers={

#                 "Content-Type": "application/json"

#             }

#         )
#         adk_time = time.perf_counter() - t

#         # print('response',payload)
#         print("response status:", response.status_code)
#         print("response headers:", dict(response.headers))
#         print("response text:", response.text)

#         raw_text = response.text

#         # ---------------------------------------------------
#         # TOKEN TRACKING
#         # ---------------------------------------------------

#         asyncio.create_task(

#             track_tokens(

#                 raw_text,

#                 userId,

#                 sessionId

#             )

#         )

#         # ---------------------------------------------------
#         # RETURN RESPONSE
#         # ---------------------------------------------------

#         try:
#             t = time.perf_counter()
#             response_json = response.json()
#             response_parse_time = time.perf_counter() - t

#             if question:
                
#                 t = time.perf_counter()
#                 cache_manager.store_question_cache(

#                     question,

#                     response_json

#                 )
#                 cache_store_time = time.perf_counter() - t

#             # if question and embedding:

#             #     cache_manager.store_semantic_cache(

#             #         question=question,

#             #         embedding=embedding,

#             #         response=response_json,

#             #         limit=limit

#             #     )
#             total_time = time.perf_counter() - start_total

#             print(f"""
#             ============================================================
#             PERFORMANCE REPORT
#             ============================================================
#             JSON Parsing         : {json_time*1000:.2f} ms
#             Question Extraction  : {question_time*1000:.2f} ms
#             Question Cache       : {cache_lookup_time*1000:.2f} ms
#             ADK Call             : {adk_time:.2f} sec
#             Response Parsing     : {response_parse_time*1000:.2f} ms
#             Cache Store          : {cache_store_time*1000:.2f} ms
#             ------------------------------------------------------------
#             TOTAL                : {total_time:.2f} sec
#             ============================================================
#             """)

#             return JSONResponse(

#                 content=response_json,

#                 status_code=response.status_code

#             )

#         except Exception:

#             return JSONResponse(

#                 content={

#                     "raw": raw_text

#                 },

#                 status_code=response.status_code

#             )

#     except Exception as e:

#         return JSONResponse(

#             content={

#                 "error": str(e)

#             },

#             status_code=500

#         )














from typing import Optional, Dict, Any, Tuple, Union
from fastapi import Request, APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
import httpx
import asyncio
import json
import os
import sys
import re
import time
from dotenv import load_dotenv

# Ensure root directory is in sys.path for notification_service import
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from notification_service.dispatcher import dispatch_notifications

from db import upsert_token_usage
from cache import cache_manager
from embedding_service import embedding_service


router = APIRouter()

load_dotenv()


# ============================================================
# CONFIG
# ============================================================

ADK_BASE_URL = os.getenv("ADK_BASE_URL")

client = httpx.AsyncClient(
    timeout=60.0
)


# ============================================================
# TOKEN TRACKING
# ============================================================

async def track_tokens(raw_payload, userId, sessionId,appName):

    try:

        print("track_tokens called:", userId, sessionId)

        # ----------------------------------------------------
        # Parse payload safely
        # ----------------------------------------------------

        events = None

        if isinstance(raw_payload, (dict, list)):

            events = raw_payload

        elif isinstance(raw_payload, str):

            raw_payload = raw_payload.strip()

            if not raw_payload:
                print("Empty response → skipping token tracking")
                return

            # ------------------------------------------------
            # Normal JSON response
            # ------------------------------------------------

            try:

                events = json.loads(raw_payload)

            except json.JSONDecodeError:

                # ------------------------------------------------
                # Try JSONL / multiple JSON objects
                # ------------------------------------------------

                print("Response is not single JSON. Trying JSONL...")

                events = []

                for line in raw_payload.splitlines():

                    line = line.strip()

                    if not line:
                        continue

                    try:

                        events.append(
                            json.loads(line)
                        )

                    except json.JSONDecodeError:

                        continue

                if not events:

                    print(
                        "Unable to parse response as JSON/JSONL "
                        "→ skipping token tracking"
                    )

                    return

        else:

            print(
                "Unexpected payload type:",
                type(raw_payload)
            )

            return


        # ----------------------------------------------------
        # Normalize dict to list
        # ----------------------------------------------------

        if isinstance(events, dict):

            events = [events]

        elif not isinstance(events, list):

            print(
                "Unexpected parsed format:",
                type(events)
            )

            return


        # ====================================================
        # TOKEN COUNTS
        # ====================================================

        totalTokens = 0
        promptTokens = 0
        completionTokens = 0


        for event in events:

            if not isinstance(event, dict):
                continue

            # Get appName from ADK response
           

            usage = event.get("usageMetadata")

            if not usage:
                continue

            totalTokens += (
                usage.get("totalTokenCount", 0) or 0
            )

            promptTokens += (
                usage.get("promptTokenCount", 0) or 0
            )

            completionTokens += (
                usage.get("candidatesTokenCount", 0) or 0
            )

   
           


        # ====================================================
        # LOG TOKENS
        # ====================================================

        print(
            "Tokens:",
            totalTokens
        )

        print(
            "Prompt Tokens:",
            promptTokens
        )

        print(
            "Completion Tokens:",
            completionTokens
        )


        # ----------------------------------------------------
        # Store in DB
        # ----------------------------------------------------

        if totalTokens > 0:

            upsert_token_usage(
                userId,
                sessionId,
                totalTokens,
                promptTokens,
                completionTokens,
                appName
            )

            print(
                "Stored in DB:",
                userId,
                sessionId,
                appName
                
            )

        else:

            print(
                "No usageMetadata found → "
                "nothing stored"
            )


    except Exception as e:

        print(
            "Token tracking error:",
            repr(e)
        )


# ============================================================
# QUESTION EXTRACTION
# ============================================================

def extract_question(payload):

    try:

        if payload.get("newMessage"):

            parts = payload["newMessage"].get(
                "parts",
                []
            )

            if parts:

                for part in parts:

                    if (
                        isinstance(part, dict)
                        and "text" in part
                    ):

                        return part["text"]


        return (
            payload.get("question")
            or payload.get("message")
            or ""
        )

    except Exception as e:

        print(
            "Question extraction error:",
            repr(e)
        )

        return ""


# ============================================================
# LIMIT EXTRACTION
# ============================================================

def extract_limit(question: str):

    try:

        match = re.search(
            r"\b\d+\b",
            question
        )

        if match:

            return int(match.group())

        return None

    except Exception:

        return None


# ============================================================
# PROXY RUN
# ============================================================

# ============================================================
# SHARED AGENT EXECUTION PIPELINE
# ============================================================

# OLD MONOLITHIC SIGNATURE (COMMENTED):
# @router.post("/dev/proxy/run")
# async def proxy_run(request: Request, background_tasks: BackgroundTasks):

async def execute_agent_pipeline(
    payload: dict,
    background_tasks: Optional[BackgroundTasks] = None
) -> Tuple[Union[dict, list], int]:

    start_total = time.perf_counter()

    try:

        # ====================================================
        # 1. READ REQUEST JSON
        # ====================================================

        # OLD:
        # t = time.perf_counter()
        # payload = await request.json()
        # json_time = (
        #     time.perf_counter() - t
        # )
        json_time = 0.0

        print(
            "============================================================"
        )

        print(
            "INCOMING PAYLOAD"
        )

        print(
            payload
        )

        print(
            "============================================================"
        )


        # ====================================================
        # 2. EXTRACT USER / SESSION
        # ====================================================

        userId = payload.get(
            "userId",
            "unknown_user"
        )

        sessionId = payload.get(
            "sessionId",
            "default_session"
        )

        appName = payload.get(
        "appName",
        "unknown_app"
        )


        # ====================================================
        # 3. EXTRACT QUESTION
        # ====================================================

        t = time.perf_counter()

        question = extract_question(
            payload
        )

        limit = extract_limit(
            question
        )

        question_time = (
            time.perf_counter() - t
        )


        print(
            "Question:",
            question
        )

        print(
            "Limit:",
            limit
        )


        embedding = None


        # ====================================================
        # 4. QUESTION CACHE
        # ====================================================

        cache_lookup_time = 0

        if question:

            t = time.perf_counter()

            cached_response = (
                cache_manager.get_question_cache(
                    question
                )
            )

            cache_lookup_time = (
                time.perf_counter() - t
            )


            if cached_response:

                total_time = (
                    time.perf_counter()
                    - start_total
                )


                print(
                    "⚡ Returning Question Cache Response"
                )

                print(
                    f"Cache response time: "
                    f"{total_time:.2f} sec"
                )


                # Dispatch notification for cached responses if requested
                try:
                    notif_config = payload.get("notifications", {})
                    req_channels = notif_config.get("channels")
                    req_targets = notif_config.get("targets")
                    force_notify = notif_config.get("force", False)

                    # OLD:
                    # background_tasks.add_task(
                    #     dispatch_notifications,
                    #     adk_raw_response=cached_response,
                    #     user_query=question,
                    #     user_id=userId,
                    #     session_id=sessionId,
                    #     app_name=appName,
                    #     requested_channels=req_channels,
                    #     channel_targets=req_targets,
                    #     force_notify=force_notify
                    # )
                    if background_tasks:
                        background_tasks.add_task(
                            dispatch_notifications,
                            adk_raw_response=cached_response,
                            user_query=question,
                            user_id=userId,
                            session_id=sessionId,
                            app_name=appName,
                            requested_channels=req_channels,
                            channel_targets=req_targets,
                            force_notify=force_notify
                        )
                    else:
                        asyncio.create_task(
                            dispatch_notifications(
                                adk_raw_response=cached_response,
                                user_query=question,
                                user_id=userId,
                                session_id=sessionId,
                                app_name=appName,
                                requested_channels=req_channels,
                                channel_targets=req_targets,
                                force_notify=force_notify
                            )
                        )
                except Exception as e:
                    print("Cached notification scheduling error:", str(e))

                # OLD:
                # return JSONResponse(
                #     content=cached_response,
                #     status_code=200
                # )
                return cached_response, 200


        # ====================================================
        # 5. ADK URL
        # ====================================================

        adk_base = (os.getenv("ADK_BASE_URL") or "http://127.0.0.1:8080").strip().rstrip("/")
        url = f"{adk_base}/run"


        print(
            "============================================================"
        )

        print(
            "ADK REQUEST"
        )

        print(
            "URL:",
            url
        )

        print(
            "============================================================"
        )


        # ====================================================
        # 6. CALL ADK (WITH AUTO-HEALING & LOCAL FALLBACK)
        # ====================================================

        t = time.perf_counter()

        try:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Content-Type":
                        "application/json"
                }
            )
        except httpx.RequestError as req_err:
            # Fallback to local 127.0.0.1:8080 if remote URL connection failed
            if "127.0.0.1" not in url and "localhost" not in url:
                print(f"⚠️ Primary ADK URL failed ({req_err}). Retrying with local http://127.0.0.1:8080/run...")
                adk_base = "http://127.0.0.1:8080"
                url = f"{adk_base}/run"
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type":
                            "application/json"
                    }
                )
            else:
                raise req_err

        # Auto-create session if ADK reports session not found, then retry once
        if response.status_code == 404 and ("session" in response.text.lower() or "not found" in response.text.lower()):
            print(f"⚠️ Session '{sessionId}' not found in ADK. Auto-creating session for user '{userId}'...")
            try:
                create_sess_url = f"{adk_base}/apps/{appName}/users/{userId}/sessions"
                sess_res = await client.post(create_sess_url, json={})
                if sess_res.status_code in (200, 201):
                    new_sess = sess_res.json()
                    new_sid = new_sess.get("id") if isinstance(new_sess, dict) else str(new_sess)
                    print(f"✨ Auto-created ADK session: {new_sid}. Retrying /run...")
                    payload["sessionId"] = new_sid
                    response = await client.post(
                        url,
                        json=payload,
                        headers={
                            "Content-Type":
                                "application/json"
                        }
                    )
            except Exception as auto_sess_err:
                print("Auto session creation notice:", auto_sess_err)

        adk_time = (
            time.perf_counter()
            - t
        )


        # ====================================================
        # 7. IMPORTANT RESPONSE DEBUGGING
        # ====================================================

        print(
            "============================================================"
        )

        print(
            "ADK RESPONSE"
        )

        print(
            "Status:",
            response.status_code
        )

        print(
            "Headers:",
            dict(response.headers)
        )

        print(
            "Content-Type:",
            response.headers.get(
                "content-type"
            )
        )

        print(
            "Response length:",
            len(response.text)
        )

        print(
            "Response text:"
        )

        print(
            response.text
        )

        print(
            "============================================================"
        )


        raw_text = response.text


        # ====================================================
        # 8. TOKEN TRACKING
        # ====================================================

        asyncio.create_task(

            track_tokens(
                raw_text,
                userId,
                sessionId,
                appName
                
            )

        )
        print("track_tokens",track_tokens)

        # ====================================================
        # 9. PARSE ADK RESPONSE
        # ====================================================

        response_parse_time = 0
        cache_store_time = 0


        try:

            t = time.perf_counter()

            response_json = response.json()

            response_parse_time = (
                time.perf_counter()
                - t
            )


            # =================================================
            # 10. CACHE RESPONSE
            # =================================================

            if question:

                t = time.perf_counter()

                cache_manager.store_question_cache(
                    question,
                    response_json
                )

                cache_store_time = (
                    time.perf_counter()
                    - t
                )

            # =================================================
            # 10b. DISPATCH NOTIFICATIONS (ASYNC BACKGROUND TASK)
            # =================================================
            try:
                notif_config = payload.get("notifications", {})
                req_channels = notif_config.get("channels")
                req_targets = notif_config.get("targets")
                force_notify = notif_config.get("force", False)

                # OLD:
                # background_tasks.add_task(
                #     dispatch_notifications,
                #     adk_raw_response=response_json,
                #     user_query=question,
                #     user_id=userId,
                #     session_id=sessionId,
                #     app_name=appName,
                #     requested_channels=req_channels,
                #     channel_targets=req_targets,
                #     force_notify=force_notify
                # )
                if background_tasks:
                    background_tasks.add_task(
                        dispatch_notifications,
                        adk_raw_response=response_json,
                        user_query=question,
                        user_id=userId,
                        session_id=sessionId,
                        app_name=appName,
                        requested_channels=req_channels,
                        channel_targets=req_targets,
                        force_notify=force_notify
                    )
                else:
                    asyncio.create_task(
                        dispatch_notifications(
                            adk_raw_response=response_json,
                            user_query=question,
                            user_id=userId,
                            session_id=sessionId,
                            app_name=appName,
                            requested_channels=req_channels,
                            channel_targets=req_targets,
                            force_notify=force_notify
                        )
                    )
            except Exception as e:
                print("Notification scheduling error:", str(e))


            # =================================================
            # 11. PERFORMANCE REPORT
            # =================================================

            total_time = (
                time.perf_counter()
                - start_total
            )


            print(
                """
============================================================
PERFORMANCE REPORT
============================================================
JSON Parsing         : {:.2f} ms
Question Extraction  : {:.2f} ms
Question Cache       : {:.2f} ms
ADK Call             : {:.2f} sec
Response Parsing     : {:.2f} ms
Cache Store          : {:.2f} ms
------------------------------------------------------------
TOTAL                : {:.2f} sec
============================================================
""".format(

                    json_time * 1000,

                    question_time * 1000,

                    cache_lookup_time * 1000,

                    adk_time,

                    response_parse_time * 1000,

                    cache_store_time * 1000,

                    total_time
                )
            )


            # =================================================
            # 12. RETURN ADK RESPONSE
            # =================================================

            # OLD:
            # return JSONResponse(
            #     content=response_json,
            #     status_code=response.status_code
            # )
            return response_json, response.status_code


        except json.JSONDecodeError:

            # =================================================
            # NON-JSON RESPONSE
            # =================================================

            print(
                "ADK response is not valid JSON."
            )


            total_time = (
                time.perf_counter()
                - start_total
            )


            print(
                f"Total time: "
                f"{total_time:.2f} sec"
            )


            # OLD:
            # return JSONResponse(
            #     content={
            #         "raw": raw_text
            #     },
            #     status_code=response.status_code,
            #     media_type=(
            #         response.headers.get(
            #             "content-type",
            #             "text/plain"
            #         )
            #     )
            # )
            return {"raw": raw_text}, response.status_code


        except Exception as e:

            # =================================================
            # RESPONSE PROCESSING ERROR
            # =================================================

            print(
                "Response processing error:",
                repr(e)
            )


            print(
                "Returning raw ADK response"
            )


            # OLD:
            # return JSONResponse(
            #     content={
            #         "raw": raw_text,
            #         "error": str(e)
            #     },
            #     status_code=response.status_code
            # )
            return {"raw": raw_text, "error": str(e)}, response.status_code


    except httpx.TimeoutException as e:

        # ====================================================
        # ADK TIMEOUT
        # ====================================================

        total_time = (
            time.perf_counter()
            - start_total
        )


        print(
            "============================================================"
        )

        print(
            "ADK TIMEOUT"
        )

        print(
            "Error:",
            repr(e)
        )

        print(
            f"Total time: {total_time:.2f} sec"
        )

        print(
            "============================================================"
        )


        # OLD:
        # return JSONResponse(
        #     content={
        #         "error": "ADK request timed out",
        #         "details": str(e)
        #     },
        #     status_code=504
        # )
        return {"error": "ADK request timed out", "details": str(e)}, 504


    except httpx.RequestError as e:

        # ====================================================
        # ADK CONNECTION ERROR
        # ====================================================

        total_time = (
            time.perf_counter()
            - start_total
        )


        print(
            "============================================================"
        )

        print(
            "ADK REQUEST ERROR"
        )

        print(
            "Error:",
            repr(e)
        )

        print(
            f"Total time: {total_time:.2f} sec"
        )

        print(
            "============================================================"
        )


        # OLD:
        # return JSONResponse(
        #     content={
        #         "error": "Unable to connect to ADK",
        #         "details": str(e)
        #     },
        #     status_code=502
        # )
        return {"error": "Unable to connect to ADK", "details": str(e)}, 502


    except Exception as e:

        # ====================================================
        # OUTER ERROR
        # ====================================================

        total_time = (
            time.perf_counter()
            - start_total
        )


        print(
            "============================================================"
        )

        print(
            "PROXY ERROR"
        )

        print(
            "Error:",
            repr(e)
        )

        print(
            f"Total time: {total_time:.2f} sec"
        )

        print(
            "============================================================"
        )


        # OLD:
        # return JSONResponse(
        #     content={
        #         "error": str(e)
        #     },
        #     status_code=500
        # )
        return {"error": str(e)}, 500


# ============================================================
# PROXY RUN (PUBLIC HTTP ENDPOINT)
# ============================================================

@router.post("/dev/proxy/run")
async def proxy_run(request: Request, background_tasks: BackgroundTasks):
    """
    Standard HTTP endpoint for UI / API clients.
    Delegates directly to execute_agent_pipeline and returns JSONResponse.
    """
    try:
        payload = await request.json()
        content, status_code = await execute_agent_pipeline(payload, background_tasks)
        return JSONResponse(content=content, status_code=status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
