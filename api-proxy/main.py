from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
import httpx
import asyncio
import json
from run_api import router as run_router
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from tool_box import router as execute_query_router
from voice_service import router as voice_router
app = FastAPI(title="Mobillor AI Gateway", version="2.0")

# OLD: Duplicate middleware in commented section
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


app.include_router(run_router)

app.include_router(
    execute_query_router,
    prefix="/dev/proxy"
)
app.include_router(voice_router
)

# URLs
ADK_BASE_URL = os.getenv("ADK_BASE_URL")


ADK_RUN_URL = f"{ADK_BASE_URL}/run"


# HTTP client
client = httpx.AsyncClient(timeout=60.0)


# ---------------------------------------------------
# HOME
# ---------------------------------------------------
@app.get("/")
def home():
    return {"status": "API is running"}


# ---------------------------------------------------
# VOICE TESTING PLAYGROUND
# ---------------------------------------------------
@app.get("/voice", response_class=HTMLResponse)
async def serve_voice_ui():
    static_file = os.path.join(os.path.dirname(__file__), "static", "voice_test.html")
    if os.path.exists(static_file):
        return FileResponse(static_file)
    return HTMLResponse("<h3>Voice tester page not found. Please create api-proxy/static/voice_test.html</h3>", status_code=404)



# ---------------------------------------------------
# CREATE SESSION
# ---------------------------------------------------
@app.post("/dev/proxy/create_session")
async def create_session(userId: str = Query(...), appName: str = Query(...)):
    url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions"
    res = await client.post(url, json={})
    return JSONResponse(content=res.json(), status_code=res.status_code)


# @app.post("/dev/proxy/create_session")
# async def create_session(userId: str = Query(...), appName: str = Query(...)):

#     # url = f"{ADK_BASE_URL}/create_session"
#     url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions"

#     print(url)

#     res = await client.post(
#         url,
#         params={
#             "userId": userId,
#             "appName": appName
#         }
#     )

#     return JSONResponse(
#         content=res.json(),
#         status_code=res.status_code
#     )


# ---------------------------------------------------
# LIST SESSION
# ---------------------------------------------------
@app.get("/dev/proxy/list_session")
async def list_session(userId: str = Query(...), appName: str = Query(...)):
    url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions"
    res = await client.get(url)
    return JSONResponse(content=res.json(), status_code=res.status_code)


# ---------------------------------------------------
# GET SESSION
# ---------------------------------------------------
@app.get("/dev/proxy/get_session")
async def get_session(userId: str = Query(...), sessionId: str = Query(...), appName: str = Query(...)):
    url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions/{sessionId}"
    res = await client.get(url)
    return JSONResponse(content=res.json(), status_code=res.status_code)


# ---------------------------------------------------
# DELETE SESSION
# ---------------------------------------------------
@app.delete("/dev/proxy/delete_session")
async def delete_session(userId: str = Query(...), sessionId: str = Query(...), appName: str = Query(...)):
    url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions/{sessionId}"
    res = await client.delete(url)

    if res.status_code not in [200, 204]:
        return JSONResponse(
            content={"success": False, "error": res.text},
            status_code=res.status_code
        )

    return {"success": True, "sessionId": sessionId}


# ---------------------------------------------------
# DELETE ALL
# ---------------------------------------------------
@app.delete("/dev/proxy/deleteAll_session")
async def delete_all(userId: str = Query(...), appName: str = Query(...)):
    url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions"

    res = await client.get(url)
    sessions = res.json()

    async def delete_one(s):
        sid = s.get("id")
        durl = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions/{sid}"
        r = await client.delete(durl)
        return {"sessionId": sid, "success": r.status_code in [200, 204]}

    results = await asyncio.gather(*[delete_one(s) for s in sessions])

    return {"success": True, "deleted": results}


# # ---------------------------------------------------
# # EXECUTE QUERY
# # ---------------------------------------------------
# @app.post("/dev/proxy/execute-query")
# async def execute_query(request: Request):

#     body = await request.json()

#     url = "http://127.0.0.1:8010/execute-query"

#     try:

#         res = await client.post(
#             url,
#             json=body
#         )

#         return JSONResponse(
#             content=res.json(),
#             status_code=res.status_code
#         )

#     except httpx.RequestError as e:

#         return JSONResponse(
#             content={
#                 "success": False,
#                 "error": (
#                     "Could not connect to "
#                     "query execution service"
#                 ),
#                 "details": str(e)
#             },
#             status_code=503
#         )





# from fastapi import FastAPI, Query
# from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
# import httpx
# import asyncio
# from run_api import router as run_router
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI(title="Mobillor AI Gateway", version="2.0")

# OLD: Duplicate middleware in commented section
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# app.include_router(run_router)

# # URLs
# BASE_ADK_URL = "https://ai-chatbot.mobillor.net/dev_api"
# ADK_RUN_URL = f"{BASE_ADK_URL}/run"

# # HTTP client
# client = httpx.AsyncClient(timeout=60.0)


# # ---------------------------------------------------
# # HOME
# # ---------------------------------------------------
# @app.get("/")
# def home():
#     return {"status": "API is running"}


# # ---------------------------------------------------
# # VOICE TESTING PLAYGROUND (OLD: Duplicate test route)
# # ---------------------------------------------------
# @app.get("/voice", response_class=HTMLResponse)
# async def serve_voice_ui():
#     static_file = os.path.join(os.path.dirname(__file__), "static", "voice_test.html")
#     if os.path.exists(static_file):
#         return FileResponse(static_file)
#     return HTMLResponse("<h3>Voice tester page not found. Please create api-proxy/static/voice_test.html</h3>", status_code=404)


# # ---------------------------------------------------
# # CREATE SESSION
# # ---------------------------------------------------
# @app.post("/dev/proxy/create_session")
# async def create_session(userId: str = Query(...), appName: str = Query(...)):
#     url = f"{BASE_ADK_URL}/apps/{appName}/users/{userId}/sessions"
#     res = await client.post(url, json={})
#     return JSONResponse(content=res.json(), status_code=res.status_code)


# # ---------------------------------------------------
# # LIST SESSION
# # ---------------------------------------------------
# @app.get("/dev/proxy/list_session")
# async def list_session(userId: str = Query(...), appName: str = Query(...)):
#     url = f"{BASE_ADK_URL}/apps/{appName}/users/{userId}/sessions"
#     res = await client.get(url)
#     return JSONResponse(content=res.json(), status_code=res.status_code)


# # ---------------------------------------------------
# # GET SESSION
# # ---------------------------------------------------
# @app.get("/dev/proxy/get_session")
# async def get_session(userId: str = Query(...), sessionId: str = Query(...), appName: str = Query(...)):
#     url = f"{BASE_ADK_URL}/apps/{appName}/users/{userId}/sessions/{sessionId}"
#     res = await client.get(url)
#     return JSONResponse(content=res.json(), status_code=res.status_code)


# # ---------------------------------------------------
# # DELETE SESSION
# # ---------------------------------------------------
# @app.delete("/dev/proxy/delete_session")
# async def delete_session(userId: str = Query(...), sessionId: str = Query(...), appName: str = Query(...)):
#     url = f"{BASE_ADK_URL}/apps/{appName}/users/{userId}/sessions/{sessionId}"
#     res = await client.delete(url)

#     if res.status_code not in [200, 204]:
#         return JSONResponse(
#             content={"success": False, "error": res.text},
#             status_code=res.status_code
#         )

#     return {"success": True, "sessionId": sessionId}


# # ---------------------------------------------------
# # DELETE ALL
# # ---------------------------------------------------
# @app.delete("/dev/proxy/deleteAll_session")
# async def delete_all(userId: str = Query(...), appName: str = Query(...)):
#     url = f"{BASE_ADK_URL}/apps/{appName}/users/{userId}/sessions"

#     res = await client.get(url)
#     sessions = res.json()

#     async def delete_one(s):
#         sid = s.get("id")
#         durl = f"{BASE_ADK_URL}/apps/{appName}/users/{userId}/sessions/{sid}"
#         r = await client.delete(durl)
#         return {"sessionId": sid, "success": r.status_code in [200, 204]}

#     results = await asyncio.gather(*[delete_one(s) for s in sessions])

#     return {"success": True, "deleted": results}