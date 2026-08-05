from __future__ import annotations

import logging

from app.workflows.cleanup_workflow import CleanupWorkflow

logger = logging.getLogger("morning_companion")


class CleanupJob:

    def __init__(self, workflow: CleanupWorkflow):
        self.workflow = workflow

    async def run(self):
        await self.workflow.execute()