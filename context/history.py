from collections import deque
class ConversationHistory:
 def __init__(self,max_items=12): self._items=deque(maxlen=max_items)
 def add(self,role,text,emotion=None): self._items.append((role,text,getattr(emotion,'value',emotion) if emotion else None))
 def recent_summary(self): return " | ".join(f"{r}: {t}" for r,t,_ in self._items)
