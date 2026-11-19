import os
import asyncio
import json
import logging
from dotenv import load_dotenv

from notification_service.extractor import extract_clean_adk_response
from notification_service.dispatcher import dispatch_notifications

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# 1. Structured Table Report
mock_table_events = [
    {
        "id": "evt_tbl",
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
        }
    }
]

# 2. Pure Text Conversational Report (No Table)
mock_text_events = [
    {
        "id": "evt_txt",
        "author": "warehouse_agent",
        "content": {
            "parts": [
                {
                    "text": """### 🏭 Shift A Operational Health Summary

All primary conveyor lines and automated packing stations are operating within normal parameters.

• **Active Picklists:** 18 orders currently in progress across Zone B and Zone C.
• **Storage Utilization:** Main Hub is currently at 78% capacity with 420 bin locations ready for putaway.
• **Equipment Status:** Forklifts FL-01 through FL-04 operational; battery health optimal.
• **Priority Notice:** Inbound shipment for Purchase Order PO-9912 is expected at Dock 3 by 14:30.

*No critical bottlenecks, safety incidents, or temperature anomalies reported.*"""
                }
            ]
        }
    }
]

async def run_teams_dual_test():
    print("=" * 70)
    print("[TEST] MS TEAMS DUAL TEST: [1] TABLE DATA & [2] PURE TEXT DATA")
    print("=" * 70)

    teams_url = os.getenv("TEAMS_WEBHOOK_URL", "").strip()
    if not teams_url:
        print("[ERROR] TEAMS_WEBHOOK_URL is not configured in .env!")
        return

    # 1. Dispatch Table Alert
    print("\n[STEP 1] Dispatching Table Data to Teams...")
    res_tbl = await dispatch_notifications(
        adk_raw_response=mock_table_events,
        user_query="Stock summary for SKU-8802 (Table Report)",
        user_id="operator_chandru",
        session_id="sess_teams_tbl_01",
        app_name="chat_boat_sql",
        requested_channels=["teams"],
        force_notify=True
    )
    print("Table Result:", json.dumps(res_tbl, indent=2))

    await asyncio.sleep(2)

    # 2. Dispatch Pure Text Alert
    print("\n[STEP 2] Dispatching Pure Text Summary (No Table) to Teams...")
    res_txt = await dispatch_notifications(
        adk_raw_response=mock_text_events,
        user_query="Shift Operational Status (Text Summary)",
        user_id="operator_chandru",
        session_id="sess_teams_txt_02",
        app_name="chat_boat_sql",
        requested_channels=["teams"],
        force_notify=True
    )
    print("Pure Text Result:", json.dumps(res_txt, indent=2))

    print("\n" + "=" * 70)
    print("[SUCCESS] Both Table and Pure Text Adaptive Cards posted to MS Teams!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_teams_dual_test())
