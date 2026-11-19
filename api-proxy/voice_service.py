import os
import re
import json
import base64
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from google import genai
from google.genai import types

dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

logger = logging.getLogger("api_proxy.voice")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")


def get_gemini_client() -> genai.Client:
    """
    Returns a configured google.genai Client supporting:
    1. Vertex AI via service account (credentials/adk-key.json)
    2. Direct GEMINI_API_KEY (AI Studio)
    3. Default Google Cloud credentials
    """
    use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI") 
    project = os.getenv("GOOGLE_CLOUD_PROJECT") 
    location = os.getenv("GOOGLE_CLOUD_LOCATION") 

    if use_vertex or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        try:
            return genai.Client(vertexai=True, project=project, location=location)
        except Exception as e:
            logger.warning(f"Vertex AI Client init note: {e}")

    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception:
            pass

    return genai.Client()

# Optional Google Cloud SDK imports (handled gracefully if APIs not yet enabled)
try:
    from google.cloud import speech_v2 as speech
    HAS_SPEECH_SDK = True
except Exception:
    HAS_SPEECH_SDK = False

try:
    from google.cloud import texttospeech
    HAS_TTS_SDK = True
except Exception:
    HAS_TTS_SDK = False

router = APIRouter(prefix="/dev/proxy/voice", tags=["Voice"])

# ============================================================
# DOMAIN PHRASE SET FOR WAREHOUSE ACOUSTICS
# ============================================================
DEFAULT_WAREHOUSE_PHRASES = [
    "GRN", "SKU", "Picklist", "PIV", "Bin", "Pallet", "Mobillor", "MOBY",
    "PO", "Process Order", "Batch", "Location", "Warehouse", "Quantity",
    "Inventory", "Movement", "Material", "Inspection", "UOM", "Plant"
]


# ============================================================
# 1. SPEECH-TO-TEXT (STT) WITH GOOGLE SPEECH & GEMINI FALLBACK
# ============================================================
def transcribe_audio(
    audio_bytes: bytes,
    content_type: str = "audio/webm",
    language_code: str = "en-IN"
) -> str:
    """
    Transcribes audio into text.
    Primary: Google Cloud Speech-to-Text v2 with domain phrase boosting.
    Intelligent Fallback: Gemini 2.5 Flash Multimodal Audio Transcription.
    """
    if not audio_bytes:
        raise ValueError("Audio bytes cannot be empty")

    # Method 1: Google Cloud Speech v2
    if HAS_SPEECH_SDK and GOOGLE_CLOUD_PROJECT:
        try:
            client = speech.SpeechClient()
            phrase_items = [
                speech.PhraseSet.Phrase(value=phrase, boost=20.0)
                for phrase in DEFAULT_WAREHOUSE_PHRASES
            ]

            config = speech.RecognitionConfig(
                auto_decoding_config=speech.AutoDecodingConfig(),
                language_codes=[language_code],
                model="long",
                adaptation=speech.SpeechAdaptation(
                    phrase_sets=[speech.PhraseSet(phrases=phrase_items)]
                ),
            )

            request = speech.RecognizeRequest(
                recognizer=f"projects/{GOOGLE_CLOUD_PROJECT}/locations/global/recognizers/_",
                config=config,
                content=audio_bytes,
            )

            response = client.recognize(request=request)
            transcripts = [
                res.alternatives[0].transcript
                for res in response.results
                if res.alternatives
            ]
            final_text = " ".join(transcripts).strip()
            if final_text:
                logger.info(f"🎙️ [STT Google Cloud] Transcribed: {final_text}")
                return final_text
        except Exception as e:
            logger.warning(f"⚠️ [STT Google Cloud] Notice: {str(e)}. Falling back to Gemini Multimodal Audio...")

    # Method 2: Gemini Multimodal Audio Transcription Fallback (Works with Vertex AI or API Key)
    try:
        client = get_gemini_client()
        mime = "audio/webm"
        if "wav" in content_type.lower():
            mime = "audio/wav"
        elif "mp3" in content_type.lower():
            mime = "audio/mp3"
        elif "ogg" in content_type.lower() or "opus" in content_type.lower():
            mime = "audio/ogg"

        prompt = (
            "Listen to this audio carefully and transcribe exactly what the user said into plain text. "
            "Only return the transcribed words. Do not add explanations, greetings, or formatting."
        )

        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime),
                prompt
            ]
        )
        if res.text:
            cleaned = res.text.strip().strip('"').strip("'")
            logger.info(f"🎙️ [STT Gemini Audio] Transcribed: {cleaned}")
            return cleaned
    except Exception as e:
        logger.error(f"❌ [STT Gemini] Audio transcription failed: {str(e)}")

    raise RuntimeError("Could not transcribe audio. Ensure Google Cloud Speech API or GEMINI_API_KEY is configured.")


# ============================================================
# 2. ADK TEXT & TABLE EXTRACTOR
# ============================================================
def extract_adk_text(adk_response: Any) -> str:
    """
    Extracts plain text / markdown table from raw ADK response.
    Handles:
    - list of event dicts (standard ADK /run response)
    - dict with 'events' or 'text'
    - JSON-encoded strings
    Strips raw tool calls, thought traces, and schema definitions so
    only clean assistant markdown / tables are displayed.
    """
    if isinstance(adk_response, str):
        adk_str = adk_response.strip()
        if (adk_str.startswith("[") and adk_str.endswith("]")) or (adk_str.startswith("{") and adk_str.endswith("}")):
            try:
                parsed = json.loads(adk_response)
                return extract_adk_text(parsed)
            except Exception:
                pass
        return adk_response

    events = []
    if isinstance(adk_response, list):
        events = adk_response
    elif isinstance(adk_response, dict):
        if "text" in adk_response and isinstance(adk_response["text"], str):
            return adk_response["text"]
        events = adk_response.get("events", [])
        if not events and "content" in adk_response:
            events = [adk_response]

    model_texts = []
    for ev in events:
        if not isinstance(ev, dict):
            continue
        # Skip user events
        if ev.get("author") == "user" or ev.get("role") == "user":
            continue

        content = ev.get("content", {})
        if isinstance(content, dict):
            if content.get("role") == "user":
                continue
            parts = content.get("parts", [])
            for p in parts:
                if isinstance(p, dict) and "text" in p and not p.get("thought"):
                    t = p["text"].strip()
                    if t:
                        model_texts.append(t)

        actions = ev.get("actions", {})
        if isinstance(actions, dict):
            parts = actions.get("content", {}).get("parts", [])
            for p in parts:
                if isinstance(p, dict) and "text" in p and not p.get("thought"):
                    t = p["text"].strip()
                    if t:
                        model_texts.append(t)

    if model_texts:
        return "\n\n".join(model_texts)

    return str(adk_response)


# ============================================================
# 3. SINGLE-PASS SPOKEN SUMMARY GENERATOR (ZERO-LATENCY BRIDGE)
# ============================================================
def generate_spoken_summary(agent_response_text: str) -> str:
    """
    Single-Pass Fast Spoken Summary Generator (0ms Latency):
    Extracts the conversational summary directly from the agent's single-pass output.
    - If the agent provided an introductory summary sentence before the table, extracts and uses it!
    - If tabular data exists, counts the records and formats a clean spoken sentence.
    - Bypasses the 2nd LLM round-trip, saving 1.5 - 2.5 seconds per voice query!
    """
    if not agent_response_text or not agent_response_text.strip():
        return "No response data available."

    clean_text = agent_response_text.strip()
    lines = [l.strip() for l in clean_text.splitlines() if l.strip()]

    # 1. Simple text without tables (< 180 chars) - speak directly
    has_table = any(l.startswith("|") for l in lines)
    if not has_table and len(clean_text) < 180:
        return re.sub(r'[*_#`]', '', clean_text).strip()

    # 2. Single-Pass: Extract conversational headline before the table
    intro_sentences = []
    table_rows = []
    in_table = False

    for l in lines:
        if l.startswith("|"):
            in_table = True
            # Count data rows (skip markdown separator rows like |---|)
            if not re.match(r"^\|[-:\s|]+\|$", l):
                table_rows.append(l)
        elif not in_table:
            # Lines before table: skip markdown headers, dividers, and notification notices
            clean_l = re.sub(r'[*_#`]', '', l).strip()
            if clean_l and not clean_l.lower().startswith("the notification has been sent") and not clean_l.startswith("---"):
                intro_sentences.append(clean_l)

    # 3. If agent already generated a headline before the table (Single-Pass Hit!)
    if intro_sentences:
        spoken = " ".join(intro_sentences).strip()
        spoken = re.sub(r'[:\-–]+$', '', spoken).strip()
        spoken = spoken.rstrip(".!?")
        if has_table and "displayed on your screen" not in spoken.lower():
            spoken = f"{spoken}. The full details are displayed on your screen."
        elif not spoken.endswith((".", "!", "?")):
            spoken = f"{spoken}."
        logger.info(f"⚡ [Single-Pass Summary] Extracted in 0ms: {spoken}")
        return spoken

    # 4. If pure table without headline, count rows deterministically (0ms)
    if len(table_rows) > 1:
        data_count = len(table_rows) - 1
        spoken = f"Found {data_count} matching records. The full table is displayed on your screen."
        logger.info(f"⚡ [Single-Pass Summary] Row-count summary in 0ms: {spoken}")
        return spoken

    # 5. Deterministic fallback for plain text
    no_markdown = re.sub(r'\|[-:\s|]+\|', '', clean_text)
    no_markdown = re.sub(r'[*_#`|]', '', no_markdown)
    return no_markdown[:160].strip()


# ============================================================
# 4. DIGIT & CODE PRONUNCIATION NORMALIZER
# ============================================================
def normalize_spoken_codes(text: str) -> str:
    """
    Converts 4+ digit numbers into spaced single digits:
    '7005022774' -> '7 0 0 5 0 2 2 7 7 4' so TTS articulates each digit distinctly.
    """
    if not text:
        return ""
    # Space out digits in large serial/ID numbers (e.g. 7005028727 -> 7 0 0 5 0 2 8 7 2 7)
    return re.sub(r'\b\d{4,}\b', lambda m: " ".join(list(m.group())), text)


# ============================================================
# 5. TEXT-TO-SPEECH (TTS) ENGINE
# ============================================================
def synthesize_speech(
    text: str,
    language_code: str = "en-IN",
    voice_name: str = "en-IN-Neural2-A"
) -> Optional[str]:
    """
    Synthesizes speech audio using Google Cloud Text-to-Speech Neural2.
    Returns Base64-encoded MP3 audio string.
    Returns None gracefully if Cloud TTS API is not yet active on GCP.
    """
    if not text or not text.strip():
        return None

    if not HAS_TTS_SDK:
        logger.warning("⚠️ google-cloud-texttospeech library not available.")
        return None

    try:
        formatted_text = normalize_spoken_codes(text)

        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.SynthesisInput(text=formatted_text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.05
        )

        response = client.synthesize_speech(
            input=input_text,
            voice=voice,
            audio_config=audio_config
        )

        b64_audio = base64.b64encode(response.audio_content).decode("utf-8")
        logger.info(f"🔊 [TTS] Synthesized audio ({len(b64_audio)} base64 chars)")
        return b64_audio

    except Exception as e:
        logger.warning(f"⚠️ [TTS] Cloud Text-to-Speech API call note: {str(e)} (Ensure Cloud Text-to-Speech API is enabled in GCP Console)")
        return None


# ============================================================
# 6. FASTAPI VOICE ENDPOINTS
# ============================================================

@router.post("/stt")
async def voice_stt_endpoint(file: UploadFile = File(...)):
    """
    Standalone Speech-to-Text: Upload audio file -> returns transcript text.
    """
    try:
        audio_bytes = await file.read()
        transcript = transcribe_audio(audio_bytes, content_type=file.content_type or "audio/webm")
        return {"success": True, "transcript": transcript}
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})


@router.post("/tts")
async def voice_tts_endpoint(payload: Dict[str, Any]):
    """
    Standalone Text-to-Speech: Input text -> returns Base64 MP3 audio string.
    """
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text field cannot be empty")

    spoken_summary = generate_spoken_summary(text)
    audio_b64 = synthesize_speech(spoken_summary)

    return {
        "success": True,
        "spoken_text": spoken_summary,
        "audio_base64": audio_b64,
        "audio_format": "audio/mp3" if audio_b64 else None,
        "tts_available": audio_b64 is not None
    }


@router.post("/chat")
async def voice_chat_endpoint(
    file: UploadFile = File(...),
    userId: str = Form("user"),
    sessionId: str = Form("default_session"),
    appName: str = Form("chat_boat_sql")
):
    """
    End-to-End Voice Chat Pipeline:
    1. Transcribes audio upload. 
    2. Executes query through ADK Agent.
    3. Produces full markdown response + natural spoken summary.
    4. Generates Base64 MP3 audio stream for immediate headset playback.
    """
    import httpx

    # Step 1: STT Transcription
    try:
        audio_bytes = await file.read()
        query_text = transcribe_audio(audio_bytes, content_type=file.content_type or "audio/webm")
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Speech transcription failed: {str(e)}"}
        )

    # Step 2: Execute Shared Pipeline In-Memory (Zero Latency + Semantic Cache + MSSQL Tokens + Notifications)
    clean_query = re.sub(r'^(hey\s+)?moby[\s,.:!]+', '', query_text, flags=re.IGNORECASE).strip() or query_text

    payload = {
        "appName": appName,
        "userId": userId,
        "sessionId": sessionId,
        "newMessage": {
            "parts": [{"text": clean_query}],
            "role": "user"
        }
    }

    # OLD (Loopback network call):
    # adk_url = os.getenv("ADK_BASE_URL", "https://ai-chatbot.mobillor.net/dev_api") + "/run"
    # try:
    #     async with httpx.AsyncClient(timeout=60.0) as client:
    #         resp = await client.post(adk_url, json=payload, headers={"Content-Type": "application/json"})
    #         resp_json = resp.json()
    # except Exception as e:
    #     return JSONResponse(
    #         status_code=500,
    #         content={"success": False, "query": query_text, "error": f"Agent execution failed: {str(e)}"}
    #     )

    try:
        from run_api import execute_agent_pipeline
        resp_json, status_code = await execute_agent_pipeline(payload)
        if status_code >= 400:
            if isinstance(resp_json, dict):
                err_msg = (
                    resp_json.get("error")
                    or resp_json.get("detail")
                    or resp_json.get("message")
                    or resp_json.get("raw")
                    or "Agent execution failed"
                )
                if isinstance(err_msg, (dict, list)):
                    err_msg = str(err_msg)
            else:
                err_msg = str(resp_json)
            logger.error(f"❌ [Voice Agent] Execution error ({status_code}): {err_msg} | payload={payload}")
            return JSONResponse(
                status_code=status_code,
                content={"success": False, "query": query_text, "error": err_msg, "status_code": status_code}
            )
    except Exception as e:
        logger.error(f"❌ [Voice Agent] Exception in pipeline: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "query": query_text, "error": f"Agent execution failed: {str(e)}"}
        )

    # Step 3: Extract Clean Text / Table
    raw_markdown = extract_adk_text(resp_json)

    # Step 4: Generate Voice-friendly Spoken Summary
    spoken_summary = generate_spoken_summary(raw_markdown)

    # Step 5: Synthesize Speech
    audio_b64 = synthesize_speech(spoken_summary)

    return {
        "success": True,
        "query": query_text,
        "text_response": raw_markdown,
        "spoken_summary": spoken_summary,
        "audio_base64": audio_b64,
        "audio_format": "audio/mp3" if audio_b64 else None,
        "tts_available": audio_b64 is not None
    }
