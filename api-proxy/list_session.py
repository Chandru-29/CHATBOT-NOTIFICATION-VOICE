from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import httpx
import os
from dotenv import load_dotenv
app = FastAPI()

ADK_BASE_URL = os.getenv("ADK_BASE_URL")


@app.get("/dev/proxy/list_session")
async def list_sessions(
    userId: str = Query(...),
    appName: str = Query(...)
):
    try:
        # Build ADK URL
        adk_url = f"{ADK_BASE_URL}/apps/{appName}/users/{userId}/sessions"

        #  Call ADK API
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                adk_url,
                headers={"Content-Type": "application/json"}
            )

        #  Return response
        return JSONResponse(
            content=response.json(),
            status_code=response.status_code
        )

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )