import os
import asyncio
import json
import logging
from dotenv import load_dotenv

from notification_service.extractor import extract_clean_adk_response
from notification_service.dispatcher import dispatch_notifications
from notification_service.channels.whatsapp import convert_markdown_table_to_whatsapp_text

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

async def run_whatsapp_test():
    print("=" * 70)
    print("[TEST] WHATSAPP (META CLOUD API) NOTIFICATION TEST")
    print("=" * 70)

    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    to_phone = os.getenv("WHATSAPP_DEFAULT_RECIPIENT", "").strip()

    print(f"* Phone ID:       {phone_id or 'Not set'}")
    print(f"* Recipient Phone:{to_phone or 'Not set'}")
    print(f"* Access Token:   {('Configured (' + token[:12] + '...)') if token else 'Not set'}")

    # Extract clean text from ADK
    clean_text, meta = extract_clean_adk_response(mock_adk_events)
    print("\n[STEP 1] Table-to-Bullet Mobile Transformer Check:")
    wa_text = convert_markdown_table_to_whatsapp_text(clean_text)
    print("-" * 40)
    print(wa_text)
    print("-" * 40)

    if not phone_id or not token or not to_phone:
        print("\n[INFO] WhatsApp credentials not yet configured in .env.")
        print("Once you add WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, and WHATSAPP_DEFAULT_RECIPIENT, rerun this test!")
        return

    # Dispatch to WhatsApp
    print("\n[STEP 2] Dispatching Notification to WhatsApp...")
    result = await dispatch_notifications(
        adk_raw_response=mock_adk_events,
        user_query="Stock summary for SKU-8802",
        user_id="operator_chandru",
        session_id="sess_wa_test_01",
        app_name="chat_boat_sql",
        requested_channels=["whatsapp"],
        force_notify=True
    )

    print("\n[STEP 3] WhatsApp Result:")
    print(json.dumps(result, indent=2))

    if result.get("whatsapp", {}).get("success"):
        print("\n" + "=" * 70)
        print(f"[SUCCESS] WhatsApp message sent to {to_phone} successfully!")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(f"[FAILURE] WhatsApp send failed: {result.get('whatsapp', {}).get('error')}")
        print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_whatsapp_test())

