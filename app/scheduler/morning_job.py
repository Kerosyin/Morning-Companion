from __future__ import annotations

from app.workflows.morning_workflow import MorningWorkflow


class MorningJob:

    def __init__(
        self,
        workflow: MorningWorkflow,
    ):
        self.workflow = workflow

    async def run(self):

        await self.workflow.execute()
