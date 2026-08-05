from __future__ import annotations

from app.ai.history_manager import HistoryManager


class HistoryService:

    def __init__(self):

        self.manager = HistoryManager()

    def prepare(self, history):

        return self.manager.prepare(history)