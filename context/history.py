"""Conversation history tracking for EMU's context fusion engine."""
from dataclasses import dataclass, field
from typing import List, Optional
from context.models import EmotionState


@dataclass
class HistoryEntry:
    role: str  # "user" or "emu"
    text: str
    emotion: Optional[EmotionState] = None


class ConversationHistory:
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.entries: List[HistoryEntry] = []

    def add(self, role: str, text: str, emotion: Optional[EmotionState] = None) -> None:
        if not text:
            return
        self.entries.append(HistoryEntry(role=role, text=text, emotion=emotion))
        if len(self.entries) > self.max_history:
            self.entries.pop(0)

    def recent_summary(self) -> str:
        if not self.entries:
            return "No previous interaction."
        lines = []
        for entry in self.entries[-5:]:
            emotion_str = f" ({entry.emotion.value})" if entry.emotion else ""
            lines.append(f"{entry.role.upper()}{emotion_str}: {entry.text}")
        return " | ".join(lines)
