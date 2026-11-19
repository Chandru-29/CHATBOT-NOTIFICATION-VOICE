import os
import asyncio
import json
import logging
from dotenv import load_dotenv

from notification_service.extractor import extract_clean_adk_response
from notification_service.dispatcher import dispatch_notifications

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

mock_adk_events = [
    {
        "id": "evt_call_1",
        "author": "warehouse_agent",
        "content": {
            "parts": [
                {"thought": "Querying stock levels for SKU-8802..."},
                {
                    "function_call": {
                        "name": "validate_and_execute_sql",
                        "args": {"query": "SELECT sku, whId, qty, cd FROM Inventory WHERE sku='SKU-8802'"}
                    }
                }
            ]
        }
    },
    {
        "id": "evt_resp_2",
        "author": "warehouse_agent",
        "content": {
            "parts": [
                {
                    "function_response": {
                        "name": "validate_and_execute_sql",
                        "response": {
                            "rowCount": 2,
                            "result": [
                                {"sku": "SKU-8802", "whId": "HUB-NORTH", "qty": 1400, "cd": "2026-03-15"},
                                {"sku": "SKU-8802", "whId": "HUB-SOUTH", "qty": 850, "cd": "2026-03-14"}
                            ]
                        }
                    }
                }
            ]
        }
    },
    {
        "id": "evt_final_3",
        "author": "warehouse_agent",
        "content": {
            "parts": [
                {
                    "text": """Here is the current available inventory breakdown for **SKU-8802**:

| Item Code | Warehouse Location | Available Quantity | Last Updated Date |
|:----------|:-------------------|:-------------------|:------------------|
| SKU-8802  | HUB-NORTH          | 1,400 Units        | 2026-03-15        |
| SKU-8802  | HUB-SOUTH          | 850 Units          | 2026-03-14        |

**Total Consolidated Stock:** 2,250 Units.
*All stocks are verified and cleared for dispatch.*"""
                }
            ]
        },
        "usageMetadata": {
            "promptTokenCount": 210,
            "candidatesTokenCount": 85,
            "totalTokenCount": 295
        }
    }
]

async def run_outlook_test():
    print("=" * 70)
    print("[TEST] OUTLOOK / OFFICE 365 NOTIFICATION TEST")
    print("=" * 70)

    to_email = os.getenv("OUTLOOK_DEFAULT_RECIPIENT", "").strip()
    tenant_id = os.getenv("AZURE_TENANT_ID", "").strip()
    client_id = os.getenv("AZURE_CLIENT_ID", "").strip()
    sender_email = os.getenv("OUTLOOK_SENDER_EMAIL", "").strip()
    smtp_user = os.getenv("OUTLOOK_SMTP_USER", "").strip()

    print(f"* Configured Recipient: {to_email or 'Not set'}")
    print(f"* Azure App Client ID:  {client_id or 'Not set'}")
    print(f"* Sender Email:         {sender_email or smtp_user or 'Not set'}")

    if not to_email:
        print("\n[ERROR] OUTLOOK_DEFAULT_RECIPIENT is not configured in .env!")
        return

    # Extract clean text from ADK
    clean_text, meta = extract_clean_adk_response(mock_adk_events)
    print("\n[STEP 1] ADK Extraction Check:")
    print(f"* Clean text length: {len(clean_text)} characters")

    # Dispatch to Outlook
    print("\n[STEP 2] Dispatching Notification to Outlook...")
    result = await dispatch_notifications(
        adk_raw_response=mock_adk_events,
        user_query="Stock summary for SKU-8802",
        user_id="operator_chandru",
        session_id="sess_outlook_test_01",
        app_name="chat_boat_sql",
        requested_channels=["outlook"],
        force_notify=True
    )

    print("\n[STEP 3] Outlook Result:")
    print(json.dumps(result, indent=2))

    if result.get("outlook", {}).get("success"):
        print("\n" + "=" * 70)
        print(f"[SUCCESS] Email successfully sent to Outlook recipient: {to_email}!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"[FAILURE] Outlook email failed: {result.get('outlook', {}).get('error')}")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_outlook_test())

