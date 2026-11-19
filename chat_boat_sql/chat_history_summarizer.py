from typing import Optional
from google.adk.apps.base_events_summarizer import BaseEventsSummarizer  # type: ignore
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions, EventCompaction
from google.genai.types import Content, Part


class ChatHistorySummarizer(BaseEventsSummarizer):
    """
    Zero-cost event summarizer for Google ADK.
    
    Performs sliding-window conversational pruning:
    - Strips intermediate function calls (schema lookups, SQL generation).
    - Strips heavy tool responses (database SQL JSON rows, schema definitions).
    - Strips internal thought traces.
    - Preserves clean User messages and Final Assistant markdown responses.
    """

    def __init__(self, max_retained_messages: int = 10):
        super().__init__()
        self.max_retained_messages = max_retained_messages

    async def maybe_summarize_events(
        self, *, events: list[Event]
    ) -> Optional[Event]:
        if not events:
            return None

        clean_history = []

        for event in events:
            if not (event.content and event.content.parts):
                continue

            for part in event.content.parts:
                # Drop raw tool calls, tool responses (SQL JSON/Schema), and thought traces
                if part.function_call or part.function_response or part.thought:
                    continue

                if part.text:
                    text = part.text.strip()
                    if not text:
                        continue

                    # Unpack prior compaction blocks if re-summarizing to avoid recursive nesting
                    if "[PREVIOUS CONVERSATION HISTORY" in text:
                        lines = [line.strip() for line in text.split("\n") if line.strip()]
                        for line in lines:
                            if line.startswith("[PREVIOUS CONVERSATION HISTORY"):
                                continue
                            if line.startswith("User:") or line.startswith("Assistant:"):
                                clean_history.append(line)
                    else:
                        role_label = "User" if event.author == "user" else "Assistant"
                        clean_history.append(f"{role_label}: {text}")

        if not clean_history:
            return None

        # ----------------------------------------------------
        # SLIDING WINDOW: Keep only latest N clean messages (default: 10 messages = 5 turns)
        # Prevents token bloat over 50+ turns while preserving recent entity context
        # ----------------------------------------------------
        if len(clean_history) > self.max_retained_messages:
            clean_history = clean_history[-self.max_retained_messages:]

        compacted_text = (
            f"[PREVIOUS CONVERSATION HISTORY - LATEST {len(clean_history)} MESSAGES]\n"
            + "\n".join(clean_history)
        )

        print(f"\n{'='*70}")
        print(f" [ADK COMPACTION TRIGGERED]")
        print(f" Input Events to Compact : {len(events)} events")
        print(f" Retained Clean Messages : {len(clean_history)} messages")
        print(f" Compacted History Sent to LLM:")
        print("-" * 50)
        print(compacted_text)
        print(f"{'='*70}\n")

        compacted_content = Content(
            role="model",
            parts=[Part(text=compacted_text)]
        )

        start_timestamp = events[0].timestamp
        end_timestamp = events[-1].timestamp

        compaction = EventCompaction(
            start_timestamp=start_timestamp,
            end_timestamp=end_timestamp,
            compacted_content=compacted_content,
        )

        actions = EventActions(compaction=compaction)

        return Event(
            author="user",
            actions=actions,
            invocation_id=Event.new_id(),
        )
