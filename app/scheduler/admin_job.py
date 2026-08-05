from __future__ import annotations

from app.workflows.admin_workflow import AdminWorkflow


class AdminJob:

    def __init__(
        self,
        workflow: AdminWorkflow,
    ) -> None:

        self.workflow = workflow

    async def run(self):

        await self.workflow.execute()