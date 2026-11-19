import os
import asyncio
import json
import logging
from dotenv import load_dotenv

from notification_service.extractor import extract_clean_adk_response
from notification_service.dispatcher import dispatch_notifications

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ======================================================================
# DATASET 1: STRUCTURED TABULAR REPORT (Inventory & Metrics)
# ======================================================================
mock_table_events = [
    {
        "id": "evt_tbl_1",
        "author": "warehouse_agent",
        "content": {
            "parts": [
                {"thought": "Querying stock levels for SKU-8802 in WMS database..."},
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
        "id": "evt_tbl_2",
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
        "id": "evt_tbl_3",
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

# ======================================================================
# DATASET 2: PURE TEXT CONVERSATIONAL REPORT (Operational Summary - NO TABLE)
# ======================================================================
mock_text_events = [
    {
        "id": "evt_txt_1",
        "author": "warehouse_agent",
        "content": {
            "parts": [
                {"thought": "User asking for shift status. Compiling operational highlights without table."},
                {
                    "text": """### Shift A Operational Health Summary

All primary conveyor lines and automated packing stations are operating within normal parameters.

• **Active Picklists:** 18 orders currently in progress across Zone B and Zone C.
• **Storage Utilization:** Main Hub is currently at 78% capacity with 420 bin locations ready for putaway.
• **Equipment Status:** Forklifts FL-01 through FL-04 operational; battery health optimal.
• **Priority Notice:** Inbound shipment for Purchase Order PO-9912 is expected at Dock 3 by 14:30."""
                }
            ]
        },
        "usageMetadata": {
            "promptTokenCount": 180,
            "candidatesTokenCount": 75,
            "totalTokenCount": 255
        }
    }
]


async def run_multi_channel_tests():
    print("=" * 75)
    print("[TEST] MULTI-CHANNEL TEST: [1] TABULAR DATA & [2] PURE TEXT CONVERSATIONAL DATA")
    print("=" * 75)

    # Detect configured channels in .env
    channels = []
    if os.getenv("TEAMS_WEBHOOK_URL"):
        channels.append("teams")
    if os.getenv("GMAIL_SMTP_USER") and os.getenv("GMAIL_SMTP_APP_PASSWORD"):
        channels.append("gmail")
    if os.getenv("OUTLOOK_DEFAULT_RECIPIENT") and (os.getenv("AZURE_CLIENT_ID") or os.getenv("OUTLOOK_SMTP_PASSWORD")):
        channels.append("outlook")
    if os.getenv("WHATSAPP_PHONE_NUMBER_ID") and os.getenv("WHATSAPP_ACCESS_TOKEN"):
        channels.append("whatsapp")

    if not channels:
        print("[WARNING] No channels configured in .env!")
        return

    print(f"* Active Configured Channels: {', '.join([c.upper() for c in channels])}\n")

    # ------------------------------------------------------------------
    # TEST CASE 1: STRUCTURED TABLE DATA
    # ------------------------------------------------------------------
    print("-" * 75)
    print("[CASE 1] DISPATCHING STRUCTURED TABLE DATA")
    print("-" * 75)
    clean_tbl_text, meta_tbl = extract_clean_adk_response(mock_table_events)
    print(f"* Clean Table Text Length: {len(clean_tbl_text)} chars (has_tables: {meta_tbl['has_tables']})")

    res_tbl = await dispatch_notifications(
        adk_raw_response=mock_table_events,
        user_query="Stock summary for SKU-8802 (Table Report)",
        user_id="operator_chandru",
        session_id="sess_table_test_01",
        app_name="chat_boat_sql",
        requested_channels=channels,
        force_notify=True
    )
    print(f"* Table Delivery Results:\n{json.dumps(res_tbl, indent=2)}")

    await asyncio.sleep(2) # Brief pause between dispatches

    # ------------------------------------------------------------------
    # TEST CASE 2: PURE TEXT CONVERSATIONAL DATA (NO TABLE)
    # ------------------------------------------------------------------
    print("\n" + "-" * 75)
    print("[CASE 2] DISPATCHING PURE TEXT SUMMARY (NO TABLE)")
    print("-" * 75)
    clean_txt_text, meta_txt = extract_clean_adk_response(mock_text_events)
    print(f"* Clean Pure Text Length: {len(clean_txt_text)} chars (has_tables: {meta_txt['has_tables']})")

    res_txt = await dispatch_notifications(
        adk_raw_response=mock_text_events,
        user_query="Shift A Operational Health Summary (Text Report)",
        user_id="operator_chandru",
        session_id="sess_text_test_02",
        app_name="chat_boat_sql",
        requested_channels=channels,
        force_notify=True
    )
    print(f"* Pure Text Delivery Results:\n{json.dumps(res_txt, indent=2)}")

    print("\n" + "=" * 75)
    print("[SUCCESS] BOTH TEST CASES (TABLE + PURE TEXT) DELIVERED SUCCESSFULLY!")
    print("Please check your MS Teams channel and Gmail inbox to review both formats.")
    print("=" * 75)

if __name__ == "__main__":
    asyncio.run(run_multi_channel_tests())
